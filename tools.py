# tools.py
# Fulfills: Custom Tools, Long-Running Operations
from google.adk.tools import ToolContext

def calculate_cycle_phase(days_since_period: int) -> dict:
    """
    Calculates the menstrual cycle phase based on days since last period.
    
    Args:
        days_since_period: Number of days since the start of the last period.
    """
    if days_since_period <= 5:
        phase = "Menstrual"
    elif days_since_period <= 13:
        phase = "Follicular"
    elif days_since_period == 14:
        phase = "Ovulation"
    else:
        phase = "Luteal"
        
    return {"phase": phase, "status": "success"}

def book_appointment_tool(doctor_name: str, time: str, tool_context: ToolContext) -> dict:
    """
    Books an appointment. 
    CRITICAL: This tool requires HUMAN APPROVAL for a deposit.
    """
    
    # Check if we already have confirmation in the context
    if not tool_context.tool_confirmation:
        # PAUSE EXECUTION and ask the user
        tool_context.request_confirmation(
            hint=f"Booking with {doctor_name} at {time} requires a $50 deposit. Do you authorize this charge?",
            payload={"doctor": doctor_name, "time": time}
        )
        # Return pending status immediately
        return {
            "status": "pending",
            "message": "Waiting for user approval for deposit."
        }

    # RESUME EXECUTION (Only runs if confirmation exists)
    if tool_context.tool_confirmation.confirmed:
        return {
            "status": "confirmed", 
            "message": f"SUCCESS: Appointment confirmed with {doctor_name} at {time}. Deposit charged."
        }
    else:
        return {
            "status": "rejected", 
            "message": "Booking cancelled by user."
        }

def exit_loop_tool() -> dict:
    """
    Call this tool ONLY when the text has been successfully simplified and approved.
    """
    return {"status": "loop_exited", "message": "Text simplified successfully."}
