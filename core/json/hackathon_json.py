import json
import os
from datetime import datetime

data_filepath = 'core/json/hackathon_data.json'

# Function to load data from JSON file
def load_data():
    if os.path.exists(data_filepath):
        with open(data_filepath, 'r') as f:
            return json.load(f)
    return {"teams": [], "participants": []}

# Function to save data to JSON file
def save_data(data):
    with open(data_filepath, 'w') as f:
        json.dump(data, f, indent=4, sort_keys=True)


# Function to create a new team
def create_team(data, team_name, idea, creator):
    if any(team['name'] == team_name for team in data['teams']):
        return f"A team with the name '{team_name}' already exists. Please choose a different name."
    # if any(participant['name'] == creator for participant in data['participants']):
    #     return f"You are already in a team. You cannot create a new team."
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
    if any(p["name"] == participant and p.get('team') for p in data["participants"]):
        return "You are already in a team. You cannot join another team."

    for team in data["teams"]:
        if team["name"] == team_name:
            team["members"].append(participant)
            for p in data["participants"]:
                if p["name"] == participant:
                    p["team"] = team_name
            # data["participants"].append({"name": participant, "team": team_name})
            save_data(data)
            return f"You have successfully joined the team '{team_name}'."
    return f"Team '{team_name}' not found."

# Function to list all teams and ideas
def list_teams(data):
    if not data["teams"]:
        return "There are no teams created yet."
    return "\n".join([f"Team: {team['name']}, Idea: {team['idea']}, Members: {', '.join(team['members'])}" for team in data["teams"]])

def get_unassigned_participants(data):
    return [p['name'] for p in data['participants'] if not p['team']]