from google.adk.agents import Agent
from Hotel_Agent.sub_agents.booking_agent.agent import booking_agent
from Hotel_Agent.sub_agents.maps_agent.agent import maps_agent
from Hotel_Agent.sub_agents.issues_agent.agent import issue_agent
from google.adk.tools.tool_context import ToolContext
from Hotel_Agent.prompts import PROMPTS

def update_user_info(user_name: str,tool_context: ToolContext) -> str:
    tool_context.state["user_name"] = user_name
    
    return {
         "status": "success",
         "message": f"User name updated to {user_name}"
    }



coordinator_agent = Agent(
    name="root_coordinator",
    model="gemini-2.0-flash",
    description="Coordinator agent that handles and routes user messages to booking, maps, and issue agents.",
    instruction= PROMPTS['coordinator_agent'],
    sub_agents=[booking_agent,issue_agent,maps_agent],
    tools=[update_user_info],
)
