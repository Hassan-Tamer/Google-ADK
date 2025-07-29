from google.adk.agents import Agent
from google.adk.tools.tool_context import ToolContext
import uuid
from datetime import datetime
from Hotel_Agent.prompts import PROMPTS


def create_issue_ticket(tool_context: ToolContext, user_name: str, issue_description: str):
    pending_issues = tool_context.state.get("pending_issues", [])
    session_user_name = tool_context.state.get("user_name", "Guest")
    
    if not user_name:
        user_name = session_user_name
    
    ticket_id = str(uuid.uuid4())[:8]
    issue_ticket = {
        "ticket_id": ticket_id,
        "user_name": user_name,
        "issue_description": issue_description,
        "status": "open",
    }
    
    pending_issues.append(issue_ticket)
    tool_context.state["pending_issues"] = pending_issues
    
    return {
        "status": "success",
        "message": f"Issue ticket created successfully! Ticket ID: {ticket_id}",
        "ticket_details": {
            "ticket_id": ticket_id,
            "user_name": user_name,
            "issue_description": issue_description,
            "status": "open",
        }
    }


def view_issue_status(tool_context: ToolContext, ticket_id: str):
    pending_issues = tool_context.get_state("pending_issues", [])
    
    for issue in pending_issues:
        if issue.get("ticket_id") == ticket_id:
            return {
                "status": "success",
                "message": f"Ticket found with ID: {ticket_id}",
                "ticket_details": issue
            }
    
    return {
        "status": "error",
        "message": f"No ticket found with ID: {ticket_id}"
    }


def resolve_issue(tool_context: ToolContext, ticket_id: str):
    pending_issues = tool_context.state.get("pending_issues", [])
    
    for i, issue in enumerate(pending_issues):
        if issue.get("ticket_id") == ticket_id:
            pending_issues.pop(i)
            tool_context.state["pending_issues"] = pending_issues
            
            return {
                "status": "success",
                "message": f"Ticket {ticket_id} has been resolved",
                "ticket_details": pending_issues[i]
            }
    
    return {
        "status": "error",
        "message": f"No ticket found with ID: {ticket_id}"
    }


# Create the issue agent
issue_agent = Agent(
    name="issue_agent",
    model="gemini-2.0-flash",
    description="An agent that handles customer issues and support tickets.",
    instruction=PROMPTS["issue_agent"],
    tools=[create_issue_ticket, view_issue_status, resolve_issue],
)