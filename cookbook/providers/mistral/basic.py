from phi.agent import Agent, RunResponse  # noqa
from phi.model.mistral import Mistral

agent = Agent(model=Mistral(model="open-mistral-nemo"), instructions=["Respond in a southern tone"], markdown=True)

# Get the response in a variable
# run: RunResponse = agent.run("Explain simulation theory")
# print(run.content)

# Print the response in the terminal
agent.print_response("Explain simulation theory")
