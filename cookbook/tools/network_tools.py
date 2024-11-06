from phi.agent import Agent
from phi.tools.network import NetworkTools

agent = Agent(tools=[NetworkTools()])
agent.print_response("What is the IP address of the local machine?")
