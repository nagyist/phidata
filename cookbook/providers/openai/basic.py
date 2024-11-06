from phi.agent import Agent
from phi.model.openai import OpenAIChat
from phi.tools.network import NetworkTools
from phi.playground import Playground, serve_playground_app


# Initialize agent with network tools
network_agent = Agent(
    name="Network Agent",
    model=OpenAIChat(id="gpt-4"),
    tools=[NetworkTools()],
    markdown=True,
    description="A network agent that can check your network connection, monitor bandwidth usage, and scan ports on your machine.",
    instructions=[
        "You are a network agent that can check your network connection, monitor bandwidth usage, and scan ports on your machine.",
        "Always use tables to display data.",
    ],
)

app = Playground(agents=[network_agent]).get_app()

if __name__ == "__main__":
    serve_playground_app("basic:app", reload=True)
