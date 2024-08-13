import streamlit as st
import json
import os
from datetime import datetime
import openai  # You'll need to install this: pip install openai

openai_client = openai.OpenAI(
    api_key="<insert_api_key>",
    max_retries=5,
    timeout=10  # 7 seconds timeout
)

# Function to load data from JSON file
def load_data():
    if os.path.exists('hackathon_data.json'):
        with open('hackathon_data.json', 'r') as f:
            return json.load(f)
    return {"teams": [], "participants": []}

# Function to save data to JSON file
def save_data(data):
    with open('hackathon_data.json', 'w') as f:
        json.dump(data, f)

# Function to create a new team
def create_team(data, team_name, idea, creator):
    if any(team['name'] == team_name for team in data['teams']):
        return f"A team with the name '{team_name}' already exists. Please choose a different name."
    if any(participant['name'] == creator for participant in data['participants']):
        return f"You are already in a team. You cannot create a new team."
    team = {
        "name": team_name,
        "idea": idea,
        "members": [creator],
        "created_at": datetime.now().isoformat()
    }
    data["teams"].append(team)
    data["participants"].append({"name": creator, "team": team_name})
    save_data(data)
    return f"Team '{team_name}' has been created with the idea: {idea}"

# Function to join an existing team
def join_team(data, team_name, participant):
    for team in data["teams"]:
        if team["name"] == team_name:
            if any(p["name"] == participant for p in data["participants"]):
                return "You are already in a team. You cannot join another team."
            team["members"].append(participant)
            data["participants"].append({"name": participant, "team": team_name})
            save_data(data)
            return f"You have successfully joined the team '{team_name}'."
    return f"Team '{team_name}' not found."

# Function to list all teams and ideas
def list_teams(data):
    if not data["teams"]:
        return "There are no teams created yet."
    return "\n".join([f"Team: {team['name']}, Idea: {team['idea']}, Members: {', '.join(team['members'])}" for team in data["teams"]])

# Function to generate LLM prompt and get response
def get_llm_response(user_input, data):
    prompt = f"""
    You are an AI assistant for a hackathon team creation and matching bot. Your task is to understand the user's intent and categorize it into one of three actions: create a team, list ideas, or join a team. Here's the current state of teams:

    {list_teams(data)}

    The user has just said: "{user_input}"

    Based on this input, determine which of the following actions the user wants to take:
    1. Create a team
    2. List ideas
    3. Join a team

    If the user wants to create a team, extract the team name and idea if provided.
    If the user wants to join a team, extract the team name they want to join.
    If the user's intent is unclear, ask for clarification.

    Respond in the following JSON format:
    {{
        "action": "create_team" or "list_ideas" or "join_team" or "clarify",
        "team_name": "extracted team name" (if applicable),
        "idea": "extracted idea" (if applicable),
        "message": "a friendly message to the user based on their intent"
    }}
    """

    # In a production environment, you would use an actual LLM API here.
    # For this example, we'll use a simulated response.
    # Replace this with your actual LLM API call, e.g.:
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

    return llm_response

# Function to process user input based on LLM response
def process_input(user_input, data):
    llm_response = get_llm_response(user_input, data)
    
    if llm_response["action"] == "create_team":
        if "team_name" in llm_response and "idea" in llm_response:
            return create_team(data, llm_response["team_name"], llm_response["idea"], st.session_state.username)
        else:
            return llm_response["message"]
    elif llm_response["action"] == "list_ideas":
        return list_teams(data)
    elif llm_response["action"] == "join_team":
        if "team_name" in llm_response:
            return join_team(data, llm_response["team_name"], st.session_state.username)
        else:
            return llm_response["message"]
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
        st.session_state.username = ""

    # Username input
    if not st.session_state.username:
        st.session_state.username = st.text_input("Enter your name:")
        if st.session_state.username:
            st.success(f"Welcome, {st.session_state.username}!")

    if st.session_state.username:
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
            response = process_input(prompt, st.session_state.data)

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