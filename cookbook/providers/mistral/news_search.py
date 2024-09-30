from phi.agent import Agent
from phi.model.mistral import Mistral
from phi.tools.duckduckgo import DuckDuckGo

agent = Agent(
    model=Mistral(model="open-mistral-nemo"),
    tools=[DuckDuckGo()],
    show_tool_calls=True,
    markdown=True,
)

agent.print_response("Provide the latest news on NVIDIA", stream=True)
