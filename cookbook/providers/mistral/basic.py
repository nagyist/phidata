import os

from phi.agent import Agent, RunResponse  # noqa
from phi.model.mistral import MistralChat

api_key = os.getenv("MISTRAL_API_KEY")

agent = Agent(model=MistralChat(id="open-mistral-nemo", api_key=api_key), instructions=["Respond in a southern tone"], markdown=True)

# Get the response in a variable
# run: RunResponse = agent.run("Explain simulation theory")
# print(run.content)

# Print the response in the terminal
agent.print_response("Explain simulation theory")
