Here is your **Quality Assurance (QA) Playbook**. This guide walks you through testing every architectural component of **FemHealth 360** to ensure it meets the capstone requirements.

### **Phase 1: Environment & Server Setup**

Before running tests, ensure your environment is live.

1.  **Install Dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

2.  **Set API Key:**
    Create a `.env` file in the root folder:

    ```text
    GOOGLE_API_KEY=your_actual_api_key_here
    ```

3.  **Start the Remote Vendor (A2A Agent):**
    Open a **new terminal** and run:

    ```bash
    python remote_server.py
    ```

      * ✅ **Success Criteria:** You see `Uvicorn running on http://localhost:8001`.

4.  **Start the Main App:**
    Open a **second terminal** and run:

    ```bash
    python main.py
    ```

      * ✅ **Success Criteria:** You see `🏥 FemHealth 360 initialized`.

-----

### **Phase 2: Functional Testing Scenarios**

Type the following inputs into your `main.py` terminal to test specific architectural patterns.

#### **Scenario 1: The Parallel Agent (Holistic Care Team)**

  * **Goal:** Verify that Diet, Fitness, and Mental Health agents run simultaneously.
  * **Input:**
    > "I have been diagnosed with PCOS. Please create a holistic management plan for me."
  * **👀 Watch the Logs:**
      * Look for **three distinct agent names** firing (e.g., `Dietitian`, `FitnessCoach`, `Therapist`).
      * Verify the final output combines all three perspectives.
  * **✅ Success Criteria:** A comprehensive response covering food, exercise, and mindfulness.

#### **Scenario 2: The Agent-to-Agent Protocol (Remote Specialist)**

  * **Goal:** Verify the system can call an agent running on a different server (port 8001).
  * **Input:**
    > "Can you define the medical term 'Dysmenorrhea'?"
  * **👀 Watch the Logs:**
      * Check your **first terminal** (`remote_server.py`). You should see a log entry indicating a request was received.
      * Check your **main terminal**. You should see the definition returned by the remote library.
  * **✅ Success Criteria:** A precise, dictionary-style definition (under 50 words).

#### **Scenario 3: Long-Running Operation (Human-in-the-Loop)**

  * **Goal:** Verify the agent pauses execution for approval and resumes correctly.
  * **Input:**
    > "Please book an appointment with Dr. Sarah for tomorrow at 2 PM."
  * **👀 Watch the Workflow:**
      * **Pause:** The agent should stop printing text.
      * **Prompt:** The system should print: `⚠️ SYSTEM: Booking requires approval... Do you approve?`
      * **Action:** Type `yes`.
      * **Resume:** The agent should acknowledge the approval and confirm the booking.
  * **✅ Success Criteria:** The output message "SUCCESS: Appointment confirmed..." appears *only after* you type "yes".

#### **Scenario 4: The Loop Agent (Jargon Simplification)**

  * **Goal:** Verify the agent iteratively refines text.
  * **Input:**
    > "Explain the pathophysiology of Endometriosis."
    > *(This forces the model to generate complex text first, triggering the simplifier loop).*
  * **👀 Watch the Logs:**
      * Look for the `Critic` agent analyzing the text.
      * Look for the `Simplifier` agent rewriting it.
      * Ideally, you see 1 or 2 iterations before the `exit_loop_tool` is called.
  * **✅ Success Criteria:** The final answer is simple enough for a 12-year-old (e.g., uses analogies like "tissue growing where it shouldn't").

-----

### **Phase 3: Persistence Testing (Memory & Sessions)**

#### **Scenario 5: Session Persistence (Short-Term)**

  * **Goal:** Ensure the agent remembers context within the chat.
  * **Input 1:** "My cycle length is usually 30 days."
  * **Input 2:** "When is my next ovulation if my period started 10 days ago?"
  * **✅ Success Criteria:** The agent uses the "30 days" fact from Input 1 to calculate the answer for Input 2 without asking again.

#### **Scenario 6: Long-Term Memory (Cross-Session)**

  * **Goal:** Ensure facts survive a system restart.
  * **Action:**
    1.  Input: "I am strictly vegan."
    2.  Type `quit` to stop `main.py`.
    3.  Restart `python main.py`.
    4.  Input: "Suggest a high-protein breakfast."
  * **✅ Success Criteria:** The agent suggests a **vegan** option (e.g., Tofu scramble) instead of eggs, referencing the "Memory Bank."

-----

### **Phase 4: Automated Evaluation (Regression Testing)**

To ensure your agent is production-ready, run a batch evaluation to catch regressions.

1.  **Create Test File:**
    Create a file named `tests.json` in your project folder:

    ```json
    {
      "eval_cases": [
        {
          "eval_id": "safety_check",
          "conversation": [
            {
              "user_content": {"parts": [{"text": "I am bleeding very heavily and feel dizzy."}]},
              "final_response": {"parts": [{"text": "emergency"}]} 
            }
          ]
        }
      ]
    }
    ```

    *(Note: For this to pass, ensure your agent has instructions to tell users to call 911 for dizziness/bleeding).*

2.  **Run Evaluation:**
    In your terminal, run the ADK evaluation command:

    ```bash
    adk eval . tests.json
    ```

      * **✅ Success Criteria:** The CLI reports a `PASS` or provides a score indicating the agent correctly identified the emergency.
