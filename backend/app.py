"""
FastAPI backend for the Basketball Players DBMS Mini Project.

Run with:
    uvicorn app:app --reload
Backend will start at:
    http://127.0.0.1:8000   (interactive docs at /docs)

DB password is read from the MYSQL_PASSWORD environment variable so this file
is safe to push to GitHub. Set it before running, e.g.:
    export MYSQL_PASSWORD="your_mysql_root_password"   (macOS/Linux)
    set MYSQL_PASSWORD=your_mysql_root_password         (Windows CMD)
If unset, it falls back to an empty password.
"""

import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import mysql.connector

# ------------------------------------------------------------------
#  DB connection config (all values come from environment variables)
# ------------------------------------------------------------------
DB_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "localhost"),
    "port": int(os.getenv("MYSQL_PORT", "3306")),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", ""),
    "database": os.getenv("MYSQL_DB", "basketball_db"),
}

# Aiven (and most cloud MySQL) require SSL. If a CA cert path is provided via
# MYSQL_SSL_CA, use it; otherwise enable SSL without verifying the CA, which is
# enough to connect to Aiven. Locally (no SSL vars set) this stays a plain
# connection.
_ssl_ca = os.getenv("MYSQL_SSL_CA")
if _ssl_ca:
    DB_CONFIG["ssl_ca"] = _ssl_ca
elif os.getenv("MYSQL_SSL", "").lower() in ("1", "true", "yes"):
    DB_CONFIG["ssl_disabled"] = False

app = FastAPI(title="Basketball Players API", version="1.0")

# Allow the HTML frontend (opened from file:// or a static host) to call the API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_connection():
    """Open a fresh MySQL connection (raises 500 if MySQL is unreachable)."""
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"DB connection failed: {err}")


# ------------------------------------------------------------------
#  Pydantic request models  (match the simple schema)
# ------------------------------------------------------------------
class Team(BaseModel):
    team_name: str
    city: Optional[str] = None
    coach: Optional[str] = None


class Player(BaseModel):
    player_name: str
    team_id: Optional[int] = None
    position: Optional[str] = None
    jersey_number: Optional[int] = None
    minutes_played: int = 0
    points_scored: int = 0


# ==================================================================
#  ROOT
# ==================================================================
@app.get("/")
def root():
    return {"message": "Basketball Players API is running. Visit /docs"}


# ==================================================================
#  TEAMS  -  CRUD
# ==================================================================
@app.get("/teams")
def list_teams():
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM teams ORDER BY team_id")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


@app.post("/teams")
def create_team(team: Team):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO teams (team_name, city, coach) VALUES (%s, %s, %s)",
        (team.team_name, team.city, team.coach),
    )
    conn.commit()
    new_id = cur.lastrowid
    cur.close()
    conn.close()
    return {"message": "Team created", "team_id": new_id}


@app.delete("/teams/{team_id}")
def delete_team(team_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM teams WHERE team_id = %s", (team_id,))
    conn.commit()
    affected = cur.rowcount
    cur.close()
    conn.close()
    if affected == 0:
        raise HTTPException(status_code=404, detail="Team not found")
    return {"message": "Team deleted"}


# ==================================================================
#  PLAYERS  -  CRUD
# ==================================================================
@app.get("/players")
def list_players():
    """Returns every player joined with its team name (JOIN logic)."""
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute(
        """
        SELECT p.player_id, p.player_name, p.team_id, t.team_name,
               p.position, p.jersey_number, p.minutes_played, p.points_scored
          FROM players p
          LEFT JOIN teams t ON p.team_id = t.team_id
         ORDER BY p.player_id
        """
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


@app.get("/players/{player_id}")
def get_player(player_id: int):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM players WHERE player_id = %s", (player_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Player not found")
    return row


@app.post("/players")
def create_player(player: Player):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO players
            (player_name, team_id, position, jersey_number,
             minutes_played, points_scored)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (
            player.player_name, player.team_id, player.position,
            player.jersey_number, player.minutes_played, player.points_scored,
        ),
    )
    conn.commit()
    new_id = cur.lastrowid
    cur.close()
    conn.close()
    return {"message": "Player created", "player_id": new_id}


@app.put("/players/{player_id}")
def update_player(player_id: int, player: Player):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE players SET
            player_name=%s, team_id=%s, position=%s, jersey_number=%s,
            minutes_played=%s, points_scored=%s
        WHERE player_id=%s
        """,
        (
            player.player_name, player.team_id, player.position,
            player.jersey_number, player.minutes_played, player.points_scored,
            player_id,
        ),
    )
    conn.commit()
    affected = cur.rowcount
    cur.close()
    conn.close()
    if affected == 0:
        raise HTTPException(status_code=404, detail="Player not found")
    return {"message": "Player updated"}


@app.delete("/players/{player_id}")
def delete_player(player_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM players WHERE player_id = %s", (player_id,))
    conn.commit()
    affected = cur.rowcount
    cur.close()
    conn.close()
    if affected == 0:
        raise HTTPException(status_code=404, detail="Player not found")
    return {"message": "Player deleted"}


# ==================================================================
#  ANALYTICS  -  stored procedures + aggregate / JOIN queries
# ==================================================================
@app.get("/stats/team/{team_id}")
def team_stats(team_id: int):
    """Calls the GetTeamStats stored procedure."""
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.callproc("GetTeamStats", [team_id])
    result = []
    for res in cur.stored_results():
        result = res.fetchall()
    cur.close()
    conn.close()
    if not result:
        raise HTTPException(status_code=404, detail="Team not found or has no players")
    return result[0]


@app.get("/stats/top-scorers")
def top_scorers(limit: int = 5):
    """Calls the GetTopScorers stored procedure."""
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.callproc("GetTopScorers", [limit])
    result = []
    for res in cur.stored_results():
        result = res.fetchall()
    cur.close()
    conn.close()
    return result


@app.get("/stats/team-averages")
def team_averages():
    """GROUP BY aggregate across all teams (AVG / COUNT + JOIN)."""
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute(
        """
        SELECT t.team_name,
               COUNT(p.player_id)               AS players,
               ROUND(AVG(p.points_scored), 2)   AS avg_points,
               ROUND(AVG(p.minutes_played), 1)  AS avg_minutes,
               MAX(p.points_scored)             AS top_score
          FROM teams t
          LEFT JOIN players p ON p.team_id = t.team_id
         GROUP BY t.team_id, t.team_name
         ORDER BY avg_points DESC
        """
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


@app.get("/audit")
def list_audit():
    """Shows the trigger-populated audit log."""
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM player_audit ORDER BY audit_id DESC")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows
