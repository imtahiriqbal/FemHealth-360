# remote_server.py
# Fulfills: Agent2Agent
import os
import uvicorn
from google.adk.agents import LlmAgent
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from google.adk.models.google_llm import Gemini
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

# Basic retry config
retry_config = types.HttpRetryOptions(attempts=3, initial_delay=1)

# Define the Knowledge Base Agent
library_agent = LlmAgent(
    model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
    name="medical_library",
    description="An external medical encyclopedia service. Use this to define complex terms.",
    instruction="""
    You are a Medical Library. Your goal is to provide precise, dictionary-style definitions 
    for women's health terms (e.g., 'Hirsutism', 'Dysmenorrhea').
    Keep definitions concise (under 50 words) and strictly factual.
    """
)

# Expose via A2A Protocol
app = to_a2a(library_agent, port=8001)

if __name__ == "__main__":
    print("🏥 Starting Medical Library Server on port 8001...")
    uvicorn.run(app, host="localhost", port=8001)
