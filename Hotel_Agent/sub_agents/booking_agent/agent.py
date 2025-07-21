from google.adk.agents import Agent
from google.adk.tools.tool_context import ToolContext
import uuid
from datetime import datetime


def check_room_availability(tool_context: ToolContext, room_id: str):
    rooms_db = tool_context.state.get("rooms_db", {})
    
    if room_id not in rooms_db:
        return {
            "status": "error",
            "message": f"Room {room_id} does not exist."
        }
    
    else:
        room_info = rooms_db[room_id]
        if room_info.get("available", False):
            return {
                "status": "success",
                "message": f"Room {room_id} is available.",
                "room_info": room_info
            }
        else:
            return {
                "status": "error",
                "message": f"Room {room_id} is not available."
            }


def make_reservation(tool_context: ToolContext, room_id: str, guest_name: str):
    """Make a room reservation.
    
    Args:
        room_id: The room ID to book
        guest_name: Name of the guest (optional, will use session user_name if not provided)
    """
    
    rooms_db = tool_context.state.get("rooms_db", {})
    recent_bookings = tool_context.state.get("recent_bookings", [])
    user_name = tool_context.state.get("user_name", "Guest")
    
    if not guest_name:
        guest_name = user_name
    
    if room_id not in rooms_db:
        return {
            "status": "error",
            "message": f"Room {room_id} does not exist."
        }
    
    if not rooms_db[room_id].get("available", False):
        return {
            "status": "error",
            "message": f"Room {room_id} is not available for booking."
        }
    
    booking_id = str(uuid.uuid4())[:8]
    total_cost = rooms_db[room_id]["price"]
    
    booking = {
        "booking_id": booking_id,
        "room_id": room_id,
        "room_type": rooms_db[room_id]["type"],
        "guest_name": guest_name,
        "total_cost": total_cost,
        "status": "confirmed",
        "booking_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Update room availability
    rooms_db[room_id]["available"] = False
    
    # Add to recent bookings
    recent_bookings.append(booking)
    
    tool_context.state["rooms_db"] = rooms_db
    tool_context.state["recent_bookings"] = recent_bookings

    return {
        "status": "success",
        "message": f"Reservation confirmed! Booking ID: {booking_id}",
        "booking_details": {
            "booking_id": booking_id,
            "guest_name": guest_name,
            "room_id": room_id,
            "room_type": rooms_db[room_id]["type"],
            "total_cost": total_cost,
            "status": "confirmed",
            "booking_date": booking["booking_date"]
        }
    }


def confirm_booking(tool_context: ToolContext, booking_id: str):
    recent_bookings = tool_context.state.get("recent_bookings", [])
    
    for booking in recent_bookings:
        if booking_id and booking.get("booking_id") == booking_id:
            return {
                "status": "success",
                "message": f"Booking found with ID: {booking_id}",
                "booking_details": booking
            }
    
    
    return {
        "status": "error",
        "message": f"No booking found with ID: {booking_id}"
    }
    

def cancel_booking(tool_context: ToolContext, booking_id: str):
    recent_bookings = tool_context.state.get("recent_bookings", [])
    rooms_db = tool_context.state.get("rooms_db", {})
    
    for i, booking in enumerate(recent_bookings):
        if booking.get("booking_id") == booking_id:
            rooms_db["room_id"]["available"] = True
            recent_bookings.pop(i)
            tool_context.state["recent_bookings"] = recent_bookings
            tool_context.state["rooms_db"] = rooms_db

            return {
                "status": "success",
                "message": f"Booking with ID {booking_id} has been cancelled.",
                "booking_details": booking
            }

    
    return {
        "status": "error",
        "message": f"No booking found with ID: {booking_id}"
    }
    


booking_agent = Agent(
    name="booking_agent",
    model="gemini-2.0-flash",
    description="An agent that handles hotel room bookings and reservations for immediate occupancy.",
    instruction="""
    You are the arabic Booking Agent in a hotel customer support multi-agent system.

    Your responsibility is to assist users with **booking-related tasks** for immediate room occupancy. This is a simplified booking system where rooms are either available or not available for immediate booking.

    **Core Capabilities:**

    1. **Handle Reservation Requests**
    - When a user wants to book a room, collect the required information:
        - Specific room ID (e.g., room_101, room_102, etc.)
        - Guest name (if not provided, will use session user_name)
    - Use the check_room_availability function to verify if a specific room is available
    - Use the make_reservation function to finalize the booking
    - Provide clear confirmation with all booking details including booking ID

    2. **Handle Room Availability Checks**
    - Use check_room_availability to check if a specific room is available
    - The function requires a room_id parameter (e.g., "room_101")
    - Display room information (type, price) if available
    - Inform user if room is not available or doesn't exist

    3. **Handle Confirmation Requests**
    - If a user asks to confirm an existing booking, use the confirm_booking function
    - Require booking ID to look up reservations
    - Display all relevant booking information clearly

    4. **Handle Cancellation Requests**
    - Use the cancel_booking function to cancel reservations
    - Require booking ID for cancellation
    - Confirm cancellation and make room available again

    **Important Notes:**
    - This is a single-day booking system - no check-in/check-out dates required
    - Rooms are either available or unavailable for immediate booking
    - Once booked, a room becomes unavailable until cancelled
    - Each booking generates a unique booking ID for reference

    **User Name:**
      <user_name>
      {user_name}
      </user_name>

    **Recent Bookings:**
      <recent_bookings>
      {recent_bookings}
      </recent_bookings>

    **Pending Issues:**
      <pending_issues>
      {pending_issues}
      </pending_issues>

   **Rooms Database:**
      <rooms_db>
      {rooms_db}
      </rooms_db>

    **Guidelines:**
    - Always be professional, helpful, and concise
    - Ask for missing information (room ID, guest name) politely
    - Confirm details before making reservations
    - Provide clear booking confirmations with booking ID
    - Handle errors gracefully and provide helpful error messages
    - If user asks for room recommendations, suggest checking specific room IDs
    - Do not handle non-booking related queries — route those back to the root agent

    **Available Functions:**
    - check_room_availability(room_id): Check if a specific room is available
    - make_reservation(room_id, guest_name): Create a new booking
    - confirm_booking(booking_id): Look up existing bookings
    - cancel_booking(booking_id): Cancel a reservation

    Always use the appropriate functions to complete booking tasks and provide accurate information from the current state.
    Always Respond in arabic to the customer
    """,
    tools=[check_room_availability, make_reservation, confirm_booking, cancel_booking],
)