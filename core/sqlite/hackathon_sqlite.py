import sqlite3
from typing import Dict, List, Tuple
import uuid
from core.hackathon_base import HackathonBase, HackathonError

data_filepath = 'core/sqlite/hackathon_data.db'

init_script = """
CREATE TABLE if not exists teams (
    team_id TEXT PRIMARY KEY,
    team_name TEXT UNIQUE NOT NULL CHECK(length(team_name) <= 100),
    captain_username TEXT UNIQUE NOT NULL,
    FOREIGN KEY (captain_username) REFERENCES participants(username)
);

CREATE TABLE if not exists participants (
    username TEXT PRIMARY KEY,
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

INSERT OR IGNORE INTO participants (username)
VALUES 
    ('Abhishek'),
    ('Shishi Lion'),
    ('Sanskar'),
    ('Shreyansh'),
    ('Khushi'),
    ('Yitzhak');

"""

class HackathonSQLite(HackathonBase):
    def __init__(self):
        self.conn = sqlite3.connect(data_filepath)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.executescript(init_script)
        self.cursor = self.conn.cursor()

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
                raise HackathonError("User is already a captain of another team.")
            else:
                raise HackathonError(str(e))
        except sqlite3.Error as e:
            self.conn.rollback()
            raise HackathonError(str(e))

    def join_team(self, team_name: str, username: str) -> bool:
        try:

            print('log 1111')
            # Check if the user is already in a team
            self.cursor.execute("SELECT team_id FROM participants WHERE username = ?", (username,))
            existing_team = self.cursor.fetchone()
            if existing_team and existing_team[0] is not None:
                raise HackathonError("User is already in a team.")
            print('log 2222')

            # Use LOWER and LIKE for case-insensitive, partial matching of team name
            self.cursor.execute("""
                SELECT team_id FROM teams 
                WHERE LOWER(team_name) LIKE LOWER(?)
            """, (f"%{team_name}%",))
            
            team_results = self.cursor.fetchall()
            print('log 3333')
            if not team_results:
                raise HackathonError("No matching team found.")
            elif len(team_results) > 1:
                raise HackathonError("Multiple matching teams found. Please provide a more specific team name.")
            print('log 4444')

            team_id = team_results[0][0]

            # Check if the team has less than 5 members
            if self._get_team_size(team_id) >= 5:
                raise HackathonError("Team already has the maximum of 5 members.")
            print('log 5555')

            self.cursor.execute("UPDATE participants SET team_id = ? WHERE username = ?",
                                (team_id, username))
            print('log 6666')

            self.conn.commit()
            print('log 7777')
            return True
        except sqlite3.Error as e:
            self.conn.rollback()
            raise HackathonError(str(e))

    def _get_team_size(self, team_id: str) -> int:
        self.cursor.execute("SELECT COUNT(*) FROM participants WHERE team_id = ?", (team_id,))
        return self.cursor.fetchone()[0]

    def __get_formatted_list_team_text(self, teams: List[Dict]) -> str:
        if not teams:
            return "No teams found."
        message = "Here are the current teams:\n\n"
        for i, team in enumerate(teams, 1):
            message += f"{i}. Team: {team['team_name']}\n\n"
            message += f"   Captain: {team['captain']}\n\n"
            
            if team['members']:
                message += "   Members:\n"
                for j, member in enumerate(team['members'], 1):
                    message += f"     {j}. {member}\n"
            else:
                message += "   No additional members.\n"
            
            message += "\n"  # Add an extra newline for spacing between teams

        return message.strip()  # Remove trailing newline

    def list_teams(self) -> str:
        try:
            self.cursor.execute("""
                SELECT t.team_name, t.captain_username, p.username
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
            return self.__get_formatted_list_team_text(team_list)
        except sqlite3.Error as e:
            raise HackathonError(str(e))

    def get_unassigned_participants(self) -> List[str]:
        try:
            self.cursor.execute("SELECT username FROM participants WHERE team_id IS NULL")
            return [row[0] for row in self.cursor.fetchall()]
        except sqlite3.Error as e:
            raise HackathonError(str(e))

    def leave_current_team(self, username: str) -> bool:
        try:
            self.cursor.execute("SELECT team_id FROM participants WHERE username = ?", (username,))
            team = self.cursor.fetchone()
            if not team or team[0] is None:
                raise HackathonError("User is not in any team.")

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
            raise HackathonError(str(e))

    def delete_my_team(self, username: str) -> bool:
        try:
            self.cursor.execute("SELECT team_id, captain_username FROM teams WHERE captain_username = ?", (username,))
            team = self.cursor.fetchone()
            if not team:
                raise HackathonError("Your team does not exist. You are not a captain of any team.")
            
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
            raise HackathonError(str(e))

    def __del__(self):
        try:
            self.cursor.close()
        except sqlite3.Error as e:
            print(e)
