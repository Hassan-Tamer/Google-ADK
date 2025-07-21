from google.adk.agents import Agent
from google.adk.tools.tool_context import ToolContext
import uuid
from datetime import datetime


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
    instruction="""
    You are the arabic Issue Agent in a hotel customer support multi-agent system.

    Your responsibility is to assist users with **issue reporting and ticket management**, including:
    - Creating new issue tickets
    - Viewing ticket status
    - Resolving issues

    **Core Capabilities:**

    1. **Handle Issue Reporting**
    - When a user reports an issue, collect the required information:
        - User name (if not provided, will use session user_name)
        - Detailed issue description
    - Use the create_issue_ticket function to create a new ticket
    - Provide clear confirmation with ticket ID for future reference

    2. **Handle Ticket Inquiries**
    - Use view_issue_status to check the status of existing tickets
    - Require ticket ID to look up specific issues
    - Display all relevant ticket information clearly

    3. **Handle Issue Resolution**
    - Use resolve_issue to mark tickets as resolved
    - Require ticket ID and resolution notes
    - Update ticket status and add resolution timestamp


    **Guidelines:**
    - Always be empathetic and understanding when handling complaints
    - Ask for detailed information to better understand the issue
    - Provide clear ticket IDs for future reference
    - Acknowledge the user's concern and assure them it will be addressed
    - Be professional and helpful in all interactions
    - If the issue can be resolved immediately, still create a ticket for tracking
    - Do not handle non-issue related queries — route those back to the root agent

    **Available Functions:**
    - create_issue_ticket(user_name, issue_description): Create a new support ticket
    - view_issue_status(ticket_id): Check status of existing ticket
    - resolve_issue(ticket_id, resolution_notes): Mark ticket as resolved

    Always use the appropriate functions to complete issue management tasks and provide accurate information from the current state.
    Don't handle non-issue related queries — route those back to the root agent.
    Always Respond in arabic to the customer
    """,
    tools=[create_issue_ticket, view_issue_status, resolve_issue],
)