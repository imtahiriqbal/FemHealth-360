# agents.py
# Fulfills: Multi-Agent Systems
import os
from google.adk.agents import Agent, LlmAgent, ParallelAgent, SequentialAgent, LoopAgent
from google.adk.tools import AgentTool, google_search, FunctionTool
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.adk.models.google_llm import Gemini
from tools import calculate_cycle_phase, book_appointment_tool, exit_loop_tool

# --- 1. The Remote Specialist (A2A) ---
# Connects to the server running in remote_server.py
remote_library_agent = RemoteA2aAgent(
    name="medical_library_proxy",
    description="Use this to get precise definitions of medical terms.",
    agent_card="http://localhost:8001/.well-known/agent-card.json"
)

# --- 2. The Holistic Care Team (Parallel) ---
# These run simultaneously to save time
diet_agent = LlmAgent(
    name="Dietitian",
    model="gemini-2.5-flash-lite",
    instruction="Provide 3 nutrition tips for the user's condition. Focus on anti-inflammatory foods.",
    tools=[google_search]
)

fitness_agent = LlmAgent(
    name="FitnessCoach",
    model="gemini-2.5-flash-lite",
    instruction="Provide 3 safe exercises for the user's condition. Avoid high-cortisol activities.",
    tools=[google_search]
)

mental_agent = LlmAgent(
    name="Therapist",
    model="gemini-2.5-flash-lite",
    instruction="Provide 1 mindfulness technique.",
    tools=[google_search]
)

holistic_team = ParallelAgent(
    name="HolisticCareTeam",
    sub_agents=[diet_agent, fitness_agent, mental_agent]
)

# --- 3. The Jargon Simplifier (Loop) ---
# Iteratively simplifies text until it passes critique
simplifier = LlmAgent(
    name="Simplifier",
    model="gemini-2.5-flash-lite",
    instruction="Take the medical text provided and rewrite it for a 12-year-old audience.",
    output_key="simplified_text"
)

critic = LlmAgent(
    name="Critic",
    model="gemini-2.5-flash-lite",
    instruction="""
    Check the {simplified_text}. 
    If it is simple and clear, call the 'exit_loop_tool'.
    If it is still complex, explain why so the Simplifier can try again.
    """,
    tools=[FunctionTool(exit_loop_tool)]
)

jargon_loop = LoopAgent(
    name="JargonLoop",
    sub_agents=[simplifier, critic],
    max_iterations=3
)

# --- 4. The Orchestrator (Root) ---
root_agent = LlmAgent(
    name="FemHealth_Orchestrator",
    model="gemini-2.5-flash-lite",
    description="Main coordinator for FemHealth 360.",
    instruction="""
    You are the FemHealth 360 Concierge.
    1. If the user mentions a condition (like PCOS), use the 'HolisticCareTeam' to get a full plan.
    2. If the user shares cycle dates, use 'calculate_cycle_phase'.
    3. If the user asks for a definition, use the 'medical_library_proxy'.
    4. If the user wants to book a doctor, use 'book_appointment_tool'.
    5. Always simplify complex medical advice using the 'JargonLoop' before showing it to the user.
    """,
    tools=[
        AgentTool(holistic_team),
        AgentTool(jargon_loop),
        AgentTool(remote_library_agent), # Note: Remote agents are sometimes added directly or via AgentTool
        # remote_library_agent,
        FunctionTool(calculate_cycle_phase),
        FunctionTool(book_appointment_tool)
    ]
)
