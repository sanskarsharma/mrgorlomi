

from abc import ABC, abstractmethod
from typing import Dict, List, Tuple


class HackathonError(Exception):
    def __init__(self, message: str):
        self.message = message


class HackathonBase(ABC):

    @abstractmethod
    def create_team(team_name: str, captain_username: str) -> Tuple[str, str]:
        '''
        Create a new team with the given team name, idea and given captain username 
        and return a tuple of the team name and team id'''
        pass
    
    @abstractmethod
    def join_team(team_name: str, username: str) -> bool:
        '''
        User with the given username should join the the team with given team name
        Returns True if the user is successfully added to the team, False otherwise'''
        pass

    @abstractmethod
    def list_teams(data) -> List[Dict]:
        '''
        List all the teams along with their captain and their members'''
        pass

    @abstractmethod
    def get_unassigned_participants() -> List[str]:
        '''
        List username of all participants who are not in any team'''
        pass

    @abstractmethod
    def leave_current_team(self, username: str) -> bool:
        '''
        User with the given username should leave the team they are currently part of'''
        pass

    @abstractmethod
    def delete_my_team(self, username: str) -> bool:
        '''
        Delete the team of the user with the given username'''
        pass