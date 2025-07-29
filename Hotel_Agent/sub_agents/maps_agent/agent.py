import os
from google.adk.agents import Agent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters
from Hotel_Agent.prompts import PROMPTS


maps_agent = Agent(
    name="maps_agent",
    model="gemini-2-0-flash",
    description="An agent that helps customer to reach our hotel.",
    instruction=PROMPTS["maps_agent"],

    tools=[
        MCPToolset(
            connection_params=StdioServerParameters(
                command='npx',
                args=["-y", "@tomtom-org/tomtom-mcp"],
                env={"TOMTOM_API_KEY": os.getenv("TOMTOM_API_KEY", "")},
                timeout=20
            ),
        )
    ],
)