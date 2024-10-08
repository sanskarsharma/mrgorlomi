import sqlite3
from typing import Dict, List, Tuple
import uuid
from core.hackathon_base import HackathonBase, HackathonError
import logging
import os
import sys
import csv

logging.basicConfig()
logging.getLogger().setLevel(os.environ.get("LOG_LEVEL", "INFO"))

logger = logging.getLogger(__name__)

init_script = """
CREATE TABLE if not exists teams (
    team_id TEXT PRIMARY KEY,
    team_name TEXT UNIQUE NOT NULL CHECK(length(team_name) <= 100),
    captain_username TEXT UNIQUE NOT NULL,
    FOREIGN KEY (captain_username) REFERENCES participants(username)
);

CREATE TABLE IF NOT EXISTS ideas (
    idea_id TEXT PRIMARY KEY,
    team_id TEXT NOT NULL,
    idea_text TEXT NOT NULL,
    created_by TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (team_id) REFERENCES teams(team_id),
    FOREIGN KEY (created_by) REFERENCES participants(username)
);

CREATE TABLE if not exists participants (
    username TEXT PRIMARY KEY,
    full_name TEXT,
    bio TEXT,
    team_id TEXT,
    FOREIGN KEY (team_id) REFERENCES teams(team_id)
);

-- Create a view to count team members
CREATE VIEW if not exists team_member_count AS
SELECT team_id, COUNT(*) as member_count
FROM participants
WHERE team_id IS NOT NULL
GROUP BY team_id;

-- Create a trigger to enforce the 5-member limit
CREATE TRIGGER if not exists enforce_team_size
BEFORE INSERT ON participants
FOR EACH ROW
WHEN NEW.team_id IS NOT NULL
BEGIN
    SELECT RAISE(ABORT, 'Team already has the maximum of 5 members')
    WHERE (
        SELECT member_count 
        FROM team_member_count 
        WHERE team_id = NEW.team_id
    ) >= 5;
END;
"""


class HackathonSQLite(HackathonBase):
    def __init__(self):

        self.sqlite_db_filepath = "data/hackathon_data.db"
        self.participants_csv_filepath = "data/participants.csv"

        # ensure DB schema is setup
        self.conn = sqlite3.connect(self.sqlite_db_filepath)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.executescript(init_script)
        self.cursor = self.conn.cursor()

        if os.path.getsize(self.sqlite_db_filepath) == 0 or  os.path.getsize(self.participants_csv_filepath) == 0:
            logger.error("Filepaths provided are either empty or does not exist.")
            sys.exit(1)

        with open(self.participants_csv_filepath, 'r', newline='', encoding='utf-8') as csvfile :
            csvreader = csv.DictReader(csvfile)
            to_insert = []
            
            p_map = {}
            # loop and prepare data
            for i, row in enumerate(csvreader):
                to_insert.append((row['username'], row['full_name'], row['bio']))
                p_map[row['username']] = {'full_name': row['full_name'], 'bio': row['bio']}
            
            # insert if not already present
            self.conn.executemany("""
                INSERT OR IGNORE INTO participants (username, full_name, bio) VALUES (?, ?, ?)
                """, to_insert)
            self.conn.commit()

            # set the participants map in memory
            self.participants_map = p_map 

    def get_participant_details(self, username: str) -> Tuple[bool, str, str]:
        '''
        returns a tuple of (bool, str, str) which signifies user attributes is_participant, full_name, bio
        '''
        if not username in self.participants_map:
            return False, "", ""
        return True, self.participants_map[username].get('full_name'), self.participants_map[username].get('bio')

    def create_team(self, team_name: str, captain_username: str) -> Tuple[str, str]:
        if len(team_name) > 100:
            raise HackathonError("Team name must be 100 characters or less.")

        try:
            # Check if the captain already has a team
            self.cursor.execute("SELECT team_id FROM teams WHERE captain_username = ?", (captain_username,))
            existing_team = self.cursor.fetchone()
            if existing_team:
                raise HackathonError("User can only create one team. Delete the old team first.")

            team_id = str(uuid.uuid4())
            self.cursor.execute("INSERT INTO teams (team_id, team_name, captain_username) VALUES (?, ?, ?)",
                                (team_id, team_name, captain_username))
            self.cursor.execute("UPDATE participants SET team_id = ? WHERE username = ?",
                                (team_id, captain_username))
            self.conn.commit()
            return team_name, team_id
        except sqlite3.IntegrityError as e:
            self.conn.rollback()
            if "UNIQUE constraint failed: teams.team_name" in str(e):
                raise HackathonError("Team name already exists.")
            elif "UNIQUE constraint failed: teams.captain_username" in str(e):
                raise HackathonError("You are already a captain of another team.")
            else:
                raise HackathonError('Some error occured, pls try later')
        except sqlite3.Error as e:
            self.conn.rollback()
            raise HackathonError('Some error occured, pls try later')

    def rename_my_team(self, new_team_name: str, username: str, ) -> Tuple[str, str]:
        if len(new_team_name) > 100:
            raise HackathonError("New team name must be 100 characters or less.")

        try:
            # First, find the team where the user is the captain
            self.cursor.execute("""
                SELECT team_id, team_name FROM teams 
                WHERE captain_username = ?
            """, (username,))
            
            team = self.cursor.fetchone()
            
            if not team:
                raise HackathonError("You are not a captain of any team. Only team captain can rename team")
            
            team_id, old_team_name = team

            # Rename the team
            self.cursor.execute("UPDATE teams SET team_name = ? WHERE team_id = ?", (new_team_name, team_id))
            self.conn.commit()
            return new_team_name, team_id
        except sqlite3.Error as e:
            self.conn.rollback()
            logger.error(e)
            raise HackathonError('Some error occured, pls try again.')

    def list_my_team(self, username: str) -> str:
        try:
            self.cursor.execute("""
                SELECT
                    t.team_name, 
                    (SELECT full_name FROM participants WHERE username = t.captain_username) as captain, 
                    p.full_name
                FROM teams t
                JOIN participants p ON t.team_id = p.team_id
                WHERE t.team_id = (SELECT team_id FROM participants WHERE username = ?)
            """, (username,))
            rows = self.cursor.fetchall()
            
            if not rows:
                return "You are not in any team."

            team_name = rows[0][0]
            captain = rows[0][1]
            members = [row[2] for row in rows if row[2] != captain]

            team_info = [{
                "team_name": team_name,
                "captain": captain,
                "members": members
            }]

            return self.__get_formatted_list_team_text(team_info, my_team=True)
        except sqlite3.Error as e:
            raise HackathonError('Some error occurred, please try later')

    def join_team(self, team_name: str, username: str) -> bool:
        try:

            # Check if the user is already in a team
            self.cursor.execute("SELECT team_id FROM participants WHERE username = ?", (username,))
            existing_team = self.cursor.fetchone()
            if existing_team and existing_team[0] is not None:
                raise HackathonError("You are already in a team. Either leave/delete your team first.")

            # Use LOWER and LIKE for case-insensitive, partial matching of team name
            self.cursor.execute("""
                SELECT team_id FROM teams 
                WHERE LOWER(team_name) LIKE LOWER(?)
            """, (f"%{team_name}%",))
            
            team_results = self.cursor.fetchall()
            if not team_results:
                raise HackathonError("No matching team found.")
            elif len(team_results) > 1:
                raise HackathonError("Multiple matching teams found. Please provide a more specific team name.")

            team_id = team_results[0][0]

            # Check if the team has less than 5 members
            if self._get_team_size(team_id) >= 5:
                raise HackathonError("Team already has the maximum of 5 members.")

            self.cursor.execute("UPDATE participants SET team_id = ? WHERE username = ?",
                                (team_id, username))

            self.conn.commit()
            return True
        except sqlite3.Error as e:
            self.conn.rollback()
            raise HackathonError('Some error occured, pls try later')

    def _get_team_size(self, team_id: str) -> int:
        self.cursor.execute("SELECT COUNT(*) FROM participants WHERE team_id = ?", (team_id,))
        return self.cursor.fetchone()[0]

    def __get_formatted_list_team_text(self, teams: List[Dict], my_team: bool) -> str:
        if not teams:
            return "No teams found."
        message = "Here are the details of all the teams that have been registered:\n\n" if not my_team else "Here is the detail of your team:\n\n"
        for i, team in enumerate(teams, 1):
            message += f"{i}. Team: {team['team_name']}\n \n"
            message += f"   Captain: {team['captain']}\n \n"
            
            if team['members']:
                message += "   Members:\n"
                for j, member in enumerate(team['members'], 1):
                    message += f"     {j}. {member}\n"
            else:
                message += "   No additional members.\n"
            
            message += "\n\n"  # Add an extra newline for spacing between teams

        return message.strip()  # Remove trailing newline

    def list_teams(self) -> str:
        try:
            self.cursor.execute("""
                SELECT
                    t.team_name, 
                    (select full_name from participants where username = t.captain_username) as captain, 
                    p.full_name
                FROM teams t
                LEFT JOIN participants p ON t.team_id = p.team_id
            """)
            rows = self.cursor.fetchall()
            
            teams = {}
            for row in rows:
                team_name, captain, member = row
                if team_name not in teams:
                    teams[team_name] = {"captain": captain, "members": []}
                if member and member != captain:
                    teams[team_name]["members"].append(member)
            
            team_list = [{"team_name": k, **v} for k, v in teams.items()]
            return self.__get_formatted_list_team_text(team_list, my_team=False)
        except sqlite3.Error as e:
            raise HackathonError('Some error occured, pls try later')

    def get_unassigned_participants(self) -> List[str]:
        try:
            self.cursor.execute("SELECT full_name FROM participants WHERE team_id IS NULL")
            return [row[0] for row in self.cursor.fetchall()]
        except sqlite3.Error as e:
            raise HackathonError('Some error occured, pls try later')

    def leave_current_team(self, username: str) -> bool:
        try:
            self.cursor.execute("SELECT team_id FROM participants WHERE username = ?", (username,))
            team = self.cursor.fetchone()
            if not team or team[0] is None:
                raise HackathonError("You are not a member in any team.")

            team_id = team[0]

            # Check if the user is the team captain
            self.cursor.execute("SELECT captain_username FROM teams WHERE team_id = ?", (team_id,))
            captain = self.cursor.fetchone()
            if captain and captain[0] == username:
                raise HackathonError("Team captain cannot leave the team. Delete your team instead.")

            # Remove the user from the team
            self.cursor.execute("UPDATE participants SET team_id = NULL WHERE username = ?", (username,))
            
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            self.conn.rollback()
            raise HackathonError('Some error occured, pls try later')

    def delete_my_team(self, username: str) -> bool:
        try:
            self.cursor.execute("SELECT team_id, captain_username FROM teams WHERE captain_username = ?", (username,))
            team = self.cursor.fetchone()
            if not team:
                raise HackathonError("Your team does not exist i.e you are not a captain of any team. If you're member in any team, you can opt to leave your current team instead.")
            
            team_id, captain_username = team

            if captain_username != username:
                raise HackathonError("Only the team captain can delete the team.")

            # Remove all members from the team
            self.cursor.execute("UPDATE participants SET team_id = NULL WHERE team_id = ?", (team_id,))
            
            # Delete the team
            self.cursor.execute("DELETE FROM teams WHERE team_id = ?", (team_id,))
            
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            self.conn.rollback()
            raise HackathonError('Some error occured, pls try later')

    def add_idea_to_team(self, username: str, idea_text: str) -> str:
        try:
            # Check if the user is in a team
            self.cursor.execute("SELECT team_id FROM participants WHERE username = ?", (username,))
            user_team = self.cursor.fetchone()
            if not user_team or user_team[0] is None:
                raise HackathonError("You must be in a team to add an idea. Hury and join a team soon!")

            team_id = user_team[0]
            idea_id = str(uuid.uuid4())

            self.cursor.execute("""
                INSERT INTO ideas (idea_id, team_id, idea_text, created_by)
                VALUES (?, ?, ?, ?)
            """, (idea_id, team_id, idea_text, username))

            self.conn.commit()
            return f"Your Idea {idea_text} is successfully added"
        except sqlite3.Error as e:
            self.conn.rollback()
            raise HackathonError('Some error occured, pls try later')

    def edit_idea(self, username: str, idea_id: str, new_idea_text: str) -> str:
        try:
            # Check if the idea exists and belongs to the user's team
            self.cursor.execute("""
                SELECT i.team_id, i.created_by, p.team_id
                FROM ideas i
                JOIN participants p ON p.username = ?
                WHERE i.idea_id = ?
            """, (username, idea_id))

            result = self.cursor.fetchone()
            if not result:
                raise HackathonError("You don't have any idea kiddo to change, sad.")

            idea_team_id, idea_creator, user_team_id = result
            if idea_team_id != user_team_id:
                raise HackathonError("You can only edit ideas for your own team. Got it?")

            self.cursor.execute("""
                UPDATE ideas
                SET idea_text = ?
                WHERE idea_id = ?
            """, (new_idea_text, idea_id))

            self.conn.commit()
            return "Idea updated successfully"
        except sqlite3.Error as e:
            self.conn.rollback()
            raise HackathonError('Some error occured, pls try later')

    def list_team_ideas(self, username: str) -> str:
        try:
            self.cursor.execute("""
                SELECT i.idea_id, i.idea_text, i.created_by, i.created_at
                FROM ideas i
                JOIN participants p ON p.team_id = i.team_id
                WHERE p.username = ?
                ORDER BY i.created_at DESC
            """, (username,))

            ideas = self.cursor.fetchall()
            if not ideas:
                return "Your team doesn't have any ideas yet. Get going!"

            idea_list = "Your team's ideas:\n\n"
            for idea in ideas:
                idea_list += f"Idea: {idea[1]}\n\n"
                idea_list += f"Created by: {idea[2]}\n\n"

            return idea_list.strip()
        except sqlite3.Error as e:
            raise HackathonError('Some error occured, pls try later')

    def __del__(self):
        try:
            self.cursor.close()
        except sqlite3.Error as e:
            logger.error(e)
