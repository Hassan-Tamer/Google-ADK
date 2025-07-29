from google.adk.agents import Agent
from google.adk.tools.tool_context import ToolContext
import uuid
from datetime import datetime
from Hotel_Agent.prompts import PROMPTS


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
    instruction=PROMPTS["booking_agent"],
    tools=[check_room_availability, make_reservation, confirm_booking, cancel_booking],
)