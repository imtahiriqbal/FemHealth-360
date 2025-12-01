# main.py
# Fulfills: Sessions, Memory, Observability, App/Workflow
import asyncio
import os
import uuid
from dotenv import load_dotenv

from google.adk.apps.app import App, ResumabilityConfig
from google.adk.runners import Runner
from google.adk.sessions import DatabaseSessionService, InMemorySessionService
from google.adk.memory import InMemoryMemoryService
from google.adk.plugins.logging_plugin import LoggingPlugin
from google.genai import types

# Import our architecture
from agents import root_agent

load_dotenv()

# Define the application name constant
# We are reverting the display name to the desired name.
APP_NAME_DISPLAY = "FemHealth360"
# FIX CONSTANT: The runner environment stubbornly looks for sessions under 
# the name inferred from the root agent's site-packages path ("agents"). 
# We must use this name in the App object and for all database lookups.
APP_NAME_DB_KEY = "agents"

# --- Configuration ---
# Persistent Sessions (Local SQLite)
session_service = DatabaseSessionService(db_url="sqlite:///femhealth_sessions.db")

# Long Term Memory
memory_service = InMemoryMemoryService()

# This is the correct pattern to override the path-based inference.
app = App(
    name=APP_NAME_DB_KEY, # Pass the name the environment requires ("agents")
    root_agent=root_agent,
    plugins=[LoggingPlugin()],
    resumability_config=ResumabilityConfig(is_resumable=True)
)

# The Runner extracts the agent and the correct application name from the App instance.
runner = Runner(
    app=app,
    session_service=session_service,
    memory_service=memory_service,
)

# --- Workflow Logic ---
def check_for_approval(events):
    """Scans events for the adk_request_confirmation trigger."""
    for event in events:
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.function_call and part.function_call.name == "adk_request_confirmation":
                    return {
                        "approval_id": part.function_call.id,
                        "invocation_id": event.invocation_id,
                        # In a real app, you'd parse the 'hint' args here to show the user
                        "hint": "Booking requires approval." 
                    }
    return None

def create_approval_response(approval_info, approved: bool):
    """Creates the payload to resume the agent."""
    response_payload = types.FunctionResponse(
        id=approval_info["approval_id"],
        name="adk_request_confirmation",
        response={"confirmed": approved}
    )
    return types.Content(
        role="user", 
        parts=[types.Part(function_response=response_payload)]
    )

async def run_chat_loop():
    user_id = "user_123"
    # Using a UUID for session_id ensures a new session is created each time.
    session_id = f"session_{uuid.uuid4().hex[:6]}"
    
    # 🌟 NEW FIX: Explicitly create the session record in the database 
    # using the correct key (APP_NAME_DB_KEY) before the runner attempts to use it.
    try:
        await session_service.create_session(
            app_name=APP_NAME_DB_KEY, 
            user_id=user_id, 
            session_id=session_id
        )
    except Exception as e:
        # This will catch exceptions if the session already exists, 
        # which is fine, but ensures it is created if it's new.
        print(f"[System Warning: Could not explicitly create session (likely exists): {e}]")


    # Use the display name for the user interface
    print(f"🏥 {APP_NAME_DISPLAY} initialized (Session: {session_id})")
    print("Type 'quit' to exit.\n")

    while True:
        user_input = input("You > ")
        if user_input.lower() in ["quit", "exit"]:
            break

        print("\n🤖 Processing...")
        
        # 1. Send Message
        events = []
        user_msg = types.Content(role="user", parts=[types.Part(text=user_input)])
        
        async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=user_msg):
            events.append(event)
            # Print streaming text if available
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        print(f"Agent > {part.text}")

        # 2. Check for Pauses (Human-in-the-Loop)
        approval_req = check_for_approval(events)
        
        if approval_req:
            print(f"\n⚠️ SYSTEM: {approval_req['hint']}")
            decision = input("Do you approve? (yes/no) > ").strip().lower()
            is_approved = (decision == "yes")
            
            print("🤖 Resuming workflow...")
            
            # 3. Resume Execution
            resume_msg = create_approval_response(approval_req, is_approved)
            
            async for event in runner.run_async(
                user_id=user_id, 
                session_id=session_id, 
                new_message=resume_msg,
                invocation_id=approval_req["invocation_id"] # Critical for resuming!
            ):
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text:
                            print(f"Agent > {part.text}")

        # 4. Post-Turn Memory Ingestion
        # After the turn is complete, save useful facts to memory
        # We MUST use the runner's configured app name ("agents") for session access.
        print(f'DB APP NAME KEY: {APP_NAME_DB_KEY}\nUser ID: {user_id}\nSession ID: {session_id}')  # Debug line
        current_session = await session_service.get_session(app_name=APP_NAME_DB_KEY, session_id=session_id, user_id=user_id)
        await memory_service.add_session_to_memory(current_session)
        print("\n[System: Interaction saved to Memory Bank]\n")

if __name__ == "__main__":
    asyncio.run(run_chat_loop())