import streamlit as st
import json
import os
from datetime import datetime
import openai  # You'll need to install this: pip install openai -- upgrade (version req for this script is higher)
from dotenv import load_dotenv
import random

load_dotenv()

openai_client = openai.OpenAI(
    api_key=os.environ['OPENAI_API_KEY'],
    max_retries=5,
    timeout=10  # 7 seconds timeout
)

from core.json.hackathon_json import list_teams, create_team, join_team, load_data, get_unassigned_participants

# Function to generate LLM prompt and get response
def get_llm_response(user_input, data, context=None):
    prompt = f"""
    You are an AI assistant for a hackathon team creation and matching bot. Your task is to understand the user's intent and guide them through the process of creating a team, listing ideas, or joining a team. Here's the current state of teams:

    {list_teams(data)}

    The user has just said: "{user_input}"

    Current context: {context if context else "No ongoing process"}

    Based on this input and context, determine which of the following actions to take:
    1. Start team creation process
    2. Continue team creation process (ask for team name or idea)
    3. Finalize team creation
    4. List ideas
    5. Start join team process
    6. Clarify user intent

    Respond in the following JSON format:
    {{
        "action": "start_team_creation" or "continue_team_creation" or "finalize_team_creation" or "list_ideas" or "start_join_team" or "clarify",
        "team_name": "extracted team name" (if applicable),
        "idea": "extracted idea" (if applicable),
        "message": "a friendly message to the user based on their intent and the current context"
    }}
    """

    # In a production environment, you would use an actual LLM API here.
    # For this example, we'll use a simulated response.
    # Replace this with your actual LLM API call, e.g.:
    # response = openai.Completion.create(engine="text-davinci-002", prompt=prompt, max_tokens=150)
    # llm_response = json.loads(response.choices[0].text.strip())

    chat_completion_resp = openai_client.chat.completions.create(
        model="gpt-4o",
        response_format={
            "type": "json_object"
        },
        messages=[
            {"role": "system", "content": prompt}
        ],
        temperature=0,
        max_tokens=256,
        top_p=0,
        frequency_penalty=0,
        presence_penalty=0
    )

    llm_response = json.loads(chat_completion_resp.choices[0].message.content)

    # Simulated LLM response (replace with actual LLM in production)
    if context == "waiting_for_team_name":
        llm_response = {
            "action": "continue_team_creation",
            "team_name": user_input.strip(),
            "message": f"Great! Your team name is '{user_input.strip()}'. Would you like to add an idea for your team? If not, just say 'no idea' or 'skip'."
        }
    elif context == "waiting_for_idea":
        idea = None if user_input.lower() in ['no idea', 'skip'] else user_input.strip()
        llm_response = {
            "action": "finalize_team_creation",
            "idea": idea,
            "message": "Alright! Let's confirm your team details."
        }
    elif "create" in user_input.lower() and "team" in user_input.lower():
        llm_response = {
            "action": "start_team_creation",
            "message": "Sure, let's create a team! What would you like to name your team?"
        }
    elif "list" in user_input.lower() and "idea" in user_input.lower():
        llm_response = {
            "action": "list_ideas",
            "message": "Certainly! Here are all the current teams and their ideas:"
        }
    elif "join" in user_input.lower() and "team" in user_input.lower():
        llm_response = {
            "action": "start_join_team",
            "message": "Great! Which team would you like to join?"
        }
    else:
        llm_response = {
            "action": "clarify",
            "message": "I'm not sure what you want to do. Can you please clarify if you want to create a team, list ideas, or join a team?"
        }

    return llm_response

# Function to process user input based on LLM response
def process_input(user_input, data, context=None):
    llm_response = get_llm_response(user_input, data, context)
    
    if llm_response["action"] == "start_team_creation":
        st.session_state.context = "waiting_for_team_name"
        return llm_response["message"]
    elif llm_response["action"] == "continue_team_creation":
        if "team_name" in llm_response:
            st.session_state.team_name = llm_response["team_name"]
            st.session_state.context = "waiting_for_idea"
            return llm_response["message"]
    elif llm_response["action"] == "finalize_team_creation":
        idea = llm_response.get("idea", None)
        result = create_team(data, st.session_state.team_name, idea, st.session_state.username)
        st.session_state.context = None
        st.session_state.team_name = None
        return f"{result}\n\nIs there anything else you'd like to do?"
    elif llm_response["action"] == "list_ideas":
        return list_teams(data)
    elif llm_response["action"] == "join_team":
        if "team_name" in llm_response:
            return join_team(data, llm_response["team_name"], st.session_state.username)
        else:
            return llm_response["message"]
    elif llm_response["action"] == "list_velle":
        return get_unassigned_participants(data)
    else:  # clarify
        return llm_response["message"]

# Streamlit app
def main():
    st.title("Hackathon Team Creation and Matching Bot")

    # Initialize session state
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'data' not in st.session_state:
        st.session_state.data = load_data()
    if 'username' not in st.session_state:
        st.session_state.username = random.choice(["Alice", "Bob", "Charlie", "David", "Eve"]) # this will always be present in case of slack

    # Username input
    if not st.session_state.username:
        st.session_state.username = st.text_input("Enter your name:")
        if st.session_state.username:
            st.success(f"Welcome, {st.session_state.username}!")

    if st.session_state.username:
        # Display user guidance
        with st.expander("🔍 What can I do?", expanded=True):
            st.markdown("""
            Here are the actions you can take:

            1. **Create a team**: Say something like "I want to create a team" or "Let's make a new team".
            2. **Join a team**: Say "I'd like to join a team" or "Can I join an existing team?".
            3. **List all teams**: Ask "What teams are there?" or "Show me all the teams".
            4. **Get help**: If you're unsure, just ask "What can I do?" or "Help me get started".

            Just type your request in the chat box below, and I'll guide you through the process!
            """)

        # Display chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Chat input
        if prompt := st.chat_input("What would you like to do?"):
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # Generate bot response
            response = process_input(prompt, st.session_state.data, st.session_state.context)

            # Add bot response to chat history
            st.session_state.messages.append({"role": "assistant", "content": response})
            with st.chat_message("assistant"):
                st.markdown(response)

        # Sidebar with team information
        st.sidebar.title("Team Information")
        user_team = next((p['team'] for p in st.session_state.data['participants'] if p['name'] == st.session_state.username), None)
        if user_team:
            st.sidebar.success(f"You are in team: {user_team}")
        else:
            st.sidebar.warning("You are not in a team yet.")
        
        st.sidebar.subheader("All Teams")
        st.sidebar.text(list_teams(st.session_state.data))

if __name__ == "__main__":
    main()
