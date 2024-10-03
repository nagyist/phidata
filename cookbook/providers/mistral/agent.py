import os

from phi.agent import Agent, RunResponse  # noqa
from phi.model.mistral import MistralChat
from phi.tools.yfinance import YFinanceTools

api_key = os.getenv("MISTRAL_API_KEY")

agent = Agent(
    model=MistralChat(id="open-mistral-nemo", api_key=api_key),
    tools=[YFinanceTools(stock_price=True)],
    show_tool_calls=True,
    markdown=True,
    debug_mode=True,
)

# Get the response in a variable
# run: RunResponse = agent.run("What is the stock price of NVDA and TSLA")
# print(run.content)

# Print the response in the terminal
agent.print_response("What is the stock price of NVDA and TSLA")
