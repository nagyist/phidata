import json
from typing import Optional, Iterator

from pydantic import BaseModel, Field

from phi.agent import Agent
from phi.model.openai import OpenAIChat
from phi.workflow import Workflow, RunResponse, RunEvent
from phi.storage.workflow.sqlite import SqlWorkflowStorage
from phi.tools.duckduckgo import DuckDuckGo
from phi.utils.log import logger


class NewsArticle(BaseModel):
    title: str = Field(..., description="Title of the article.")
    url: str = Field(..., description="Link to the article.")
    summary: Optional[str] = Field(..., description="Summary of the article if available.")


class SearchResults(BaseModel):
    articles: list[NewsArticle]


class BlogPostGenerator(Workflow):
    def get_search_results(self, topic: str) -> Optional[SearchResults]:
        # Define the web search agent
        web_search_agent: Agent = Agent(
            tools=[DuckDuckGo()],
            instructions=["Given a topic, search for 20 articles and return the 5 most relevant articles."],
            response_model=SearchResults,
        )

        # Run until we get a valid search results
        try_number = 0
        while search_results is None and try_number < 3:
            logger.info(f"Try: {try_number} | Searching the web for: {topic}")
            try:
                try_number += 1
                searcher_response: RunResponse = web_search_agent.run(topic)
                if (
                    searcher_response
                    and searcher_response.content
                    and isinstance(searcher_response.content, SearchResults)
                ):
                    logger.info(f"Searcher found {len(searcher_response.content.articles)} articles.")
                    search_results = searcher_response.content
                else:
                    logger.warning("Searcher response invalid, trying again...")
            except Exception as e:
                logger.warning(f"Error running web_search_agent: {e}")

    def get_cached_blog_post(self, topic: str) -> Optional[str]:
        """Get cached blog post for a topic from the session state"""

        if "blog_posts" in self.session_state:
            logger.info("Checking if a cached blog post exists")
            cached_blog_posts = self.session_state["blog_posts"]
            if topic in cached_blog_posts:
                logger.info("Found cached blog post")
                return cached_blog_posts[topic]
        return None

    def cache_blog_post(self, topic: str, blog_post: str):
        """Cache the blog post in the session state for future runs"""

        if "blog_posts" not in self.session_state:
            self.session_state["blog_posts"] = {}
        self.session_state["blog_posts"][topic] = blog_post

    def write_blog_post(self, topic: str, search_results: SearchResults) -> Iterator[RunResponse]:
        # Define the writer agent
        writer: Agent = Agent(
            instructions=[
                "You will be provided with a topic and a list of top articles on that topic.",
                "Carefully read each article and generate a New York Times worthy blog post on that topic.",
                "Break the blog post into sections and provide key takeaways at the end.",
                "Make sure the title is catchy and engaging.",
                "Always provide sources, do not make up information or sources.",
            ],
        )
        # Prepare the input for the writer
        writer_input = {
            "topic": topic,
            "articles": [v.model_dump() for v in search_results.articles],
        }

        # Run the writer and yield the response
        logger.info("Writing blog post")
        yield from writer.run(json.dumps(writer_input, indent=4), stream=True)

        # Cache the blog post for future runs
        self.cache_blog_post(topic=topic, blog_post=writer.run_response.content)

    def run(self, topic: str, use_cache: bool = True) -> Iterator[RunResponse]:
        logger.info(f"Writing a blog post on: {topic}")

        # Step 1: Use the cached blog post if use_cache is True
        cached_blog_post = self.get_cached_blog_post(topic=topic)
        if use_cache and cached_blog_post is not None:
            yield RunResponse(
                run_id=self.run_id,
                event=RunEvent.workflow_completed,
                content=cached_blog_post,
            )
            return

        # Step 2: Search the web for articles on the topic
        search_results: Optional[SearchResults] = self.get_search_results(topic=topic)
        # If no search_results are found for the topic, end the workflow
        if search_results is None or len(search_results.articles) == 0:
            yield RunResponse(
                run_id=self.run_id,
                event=RunEvent.workflow_completed,
                content=f"Sorry, could not find any articles on the topic: {topic}",
            )
            return

        # Step 3: Write a blog post
        yield from self.write_blog_post(topic=topic, search_results=search_results)


# Instantiate the workflow
generate_blog_post = BlogPostGenerator(
    storage=SqlWorkflowStorage(
        table_name="generate_blog_post_workflows",
        db_file="tmp/workflows.db",
    ),
)

agent = Agent(
    model=OpenAIChat(id="gpt-4o"),
    workflows=[generate_blog_post],
    markdown=True,
    show_tool_calls=True,
    add_datetime_to_instructions=True,
    # debug_mode=True,
)
agent.print_response("Write a blog post on simulation theory", stream=True)
