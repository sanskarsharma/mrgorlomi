
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory

from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate

from core.sqlite.hackathon_sqlite import HackathonSQLite, HackathonError
import json

class OpenAILLM:

    def __init__(self, model_name: str = "gpt-4o"):
        self.model_name = model_name
        self.prompt_template = """
        You are an AI assistant for a hackathon team creation and matching bot. 
        You name is Mr. Gorlomi and you have a short temperament and you speak engilsh but pretend to know italian. Don't talk in italian ever just use really common italian slang. 
        
        Current conversation:
        {history}

        The user has just said: {input}

        Your task is to understand the user's intent and categorize it into one of these actions: 
        1. Create a team (create_team)
        2. List team along with their members (list_teams)
        3. Join a team (join_team)
        4. List participants who don't belong to any team (get_unassigned_participants)
        5. Leave the curretn team which user belongs to (leave_current_team)
        6. Delete user's team (delete_my_team)

        If the user wants to create a team, figure out the team name from their response or ask if team name is not provided.
        If the user wants to join a team, igure out the team name from their response or ask if team name is not provided.
        If the user's intent is unclear, ask for clarification. Be sassy when asking for clarification. 

        Respond in the following JSON format:
        {{
            "action": "create_team" or "list_teams" or "join_team" or "get_unassigned_participants" or "leave_current_team" or "delete_my_team" or "clarify",
            "team_name": "extracted team name" (if applicable),
            "message": "a friendly message to the user based on their intent"
        }}
        """

    def get_hackathon_database_connection(self) -> HackathonSQLite:
        return HackathonSQLite()
        
    def get_conversation(self, chain: ConversationChain, prompt: str, username: str):
        num_tokens = chain.llm.get_num_tokens(prompt)
        response = chain({"input": prompt})

        print(response)

        llm_response = json.loads(response['response'])

        try:
            if llm_response["action"] == "create_team":
                if "team_name" in llm_response and llm_response.get("team_name"):
                    team_name, team_id = self.get_hackathon_database_connection().create_team(llm_response["team_name"], username)
                    return f'Team created with name {team_name}', num_tokens
                else:
                    return llm_response["message"], num_tokens

            elif llm_response["action"] == "list_teams":
                team_list = self.get_hackathon_database_connection().list_teams()
                return str(team_list), num_tokens

            elif llm_response["action"] == "join_team":
                if "team_name" in llm_response and llm_response.get("team_name"):
                    success = self.get_hackathon_database_connection().join_team(llm_response["team_name"], username)
                    if not success:
                        raise HackathonError("Could not join team, please try again.")
                    return f'You joined {llm_response.get("team_name")} team successfully', num_tokens
                else:
                    return llm_response["message"], num_tokens

            elif llm_response["action"] == "get_unassigned_participants":
                ll = self.get_hackathon_database_connection().get_unassigned_participants()
                return f'Unassigned folks are {str(ll)}', num_tokens

            elif llm_response["action"] == "leave_current_team":
                success = self.get_hackathon_database_connection().leave_current_team(username)
                if not success:
                    raise HackathonError("Could not leave team, please try again.")
                return f'You left your team successfully', num_tokens

            elif llm_response["action"] == "delete_my_team":
                success = self.get_hackathon_database_connection().delete_my_team(username)
                if not success:
                    raise HackathonError("Could not delete team, please try again.")
                return f'You have deleted your team successfully', num_tokens

            else:  # clarify
                return llm_response["message"], num_tokens
        except HackathonError as e:
            return str(e), num_tokens

    ## This uses json as data. import right funcs if you need to use test this
    # def get_conversation(self, chain: ConversationChain, prompt: str, username: str):
    #     num_tokens = chain.llm.get_num_tokens(prompt)
    #     response = chain({"input": prompt})

    #     print(response)

    #     llm_response = json.loads(response['response'])

    #     data = load_data()
    #     if llm_response["action"] == "create_team":
    #         if "team_name" in llm_response and llm_response.get("team_name"):
    #             return create_team(data, llm_response["team_name"], "random idea", username), num_tokens
    #         else:
    #             return llm_response["message"], num_tokens
    #     elif llm_response["action"] == "list_teams":
    #         return list_teams(data), num_tokens
    #     elif llm_response["action"] == "join_team":
    #         if "team_name" in llm_response and llm_response.get("team_name"):
    #             return join_team(data, llm_response["team_name"], username), num_tokens
    #         else:
    #             return llm_response["message"], num_tokens
    #     elif llm_response["action"] == "list_velle":
    #         return get_unassigned_participants(data), num_tokens
    #     else:  # clarify
    #         return llm_response["message"], num_tokens

    def get_conversation_chain(self) -> ConversationChain:
        
        llm = ChatOpenAI(model_name=self.model_name)
        llm.model_kwargs = {"temperature": 0.5, "response_format" : {"type": "json_object"}}

        prompt = PromptTemplate(
            input_variables=["history", "input"], template=self.prompt_template)

        memory = ConversationBufferMemory(human_prefix="User", ai_prefix="Bot")
        conversation = ConversationChain(
            prompt=prompt,
            llm=llm,
            verbose=True,
            memory=memory,
        )

        return conversation
    
    def clear_memory(self, chain: ConversationChain):
        return chain.memory.clear()
