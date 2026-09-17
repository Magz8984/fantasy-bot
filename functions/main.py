from dataclasses import dataclass
import requests

from fastapi import FastAPI
from firebase_functions import https_fn
from fastapi.middleware.cors import CORSMiddleware
from firebase_functions.options import set_global_options

import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

# Fetch the service account key JSON file path
cred = credentials.Certificate("../serviceAccount.json")

firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://fantasy-f1-3a499-default-rtdb.firebaseio.com'
})

# For cost control, you can set the maximum number of containers that can be
# running at the same time. This helps mitigate the impact of unexpected
# traffic spikes by instead downgrading performance. This limit is a per-function
# limit. You can override the limit for each function using the max_instances
# parameter in the decorator, e.g. @https_fn.on_request(max_instances=5).
set_global_options(max_instances=10)

# initialize_app()
#
#
# @https_fn.on_request()
# def on_request_example(req: https_fn.Request) -> https_fn.Response:
#     return https_fn.Response("Hello world!")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Wrap the FastAPI app with Mangum


@dataclass
class Player:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
    first_name: str
    second_name: str
    form: str
    id: int
    in_dreamteam: bool
    team: int
    code: int
    now_cost: int
    starts: int
    minutes: int
    expected_goal_involvements: float
    expected_goals_conceded: float
    ict_index: float
    starts_per_90: float
    form_rank: int
    team_name: str
    news: str
    calculated_form: float
    element_type: int
    element_type_name: str
    f_e_r: str


@dataclass
class AddPlayerDTO:
    player_id: int  # The ID of the player to add
    in_bench: bool = False  # Whether the player is in the bench or not


@dataclass
class Team:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
    id: int
    name: str
    draw: int
    loss: int
    win: int


@dataclass
class PlayerType:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
    id: int
    singular_name: str
    singular_name_short: str
    element_count: int


def findTeamById(teams: list[Team], team_id: int):
    for team in teams:
        if team.id == team_id:
            return team
    return None


# Sanitize players by adding team_name and converting now_cost to float
def sanitizePlayers(players: list[Player], teams: list[Team], player_types: list[PlayerType]):
    # Add team_name to each player based on their team ID
    for player in players:
        team = findTeamById(teams, player.team)
        if team:
            player.team_name = team.name
        else:
            player.team_name = "Unknown"
        player.now_cost = player.now_cost / 10  # Convert to float

        # Calculate the calculated_form based on the formula
        player.calculated_form = (float(player.expected_goal_involvements) * 0.4) + (
            float(player.form) * 0.3) + (float(player.ict_index) * 0.3)

        # Calculate the f_e_r (form to expected return) based on the formula
        player.f_e_r = player.calculated_form / \
            player.now_cost if player.now_cost != 0 else 0

    for player in players:
        # Find the corresponding player type based on element_type
        player_type = next(
            (pt for pt in player_types if pt.id == player.element_type), None)
        if player_type:
            player.element_type_name = player_type.singular_name_short
        else:
            player.element_type_name = "Unknown"

    return players


# Fetch players from the Fantasy Premier League API and return a list of Player objects
def getPlayers():
    request = requests.get(
        "https://fantasy.premierleague.com/api/bootstrap-static/")

    data = request.json()

    elements = data.get('elements', [])

    teams = data.get('teams', [])

    teams = [Team(**team) for team in teams]

    # Convert each player dictionary to a Player object
    players = [Player(**player) for player in elements]

    element_types = data.get('element_types', [])

    player_types = [PlayerType(**element_type)
                    for element_type in element_types]

    # Sanitize players by adding team_name and converting now_cost to float
    players = sanitizePlayers(players, teams, player_types)
    
    return players;


@app.get("/api/player_ranking")
def player_ranking():
    
    # Fetch players from the Fantasy Premier League API and return a list of Player objects
    players = getPlayers()

    # Sort players based on f_e_r in descending order
    players.sort(key=lambda player: player.f_e_r, reverse=True)

    return {"message": players}
# 1. Used by Firebase in Production


@app.get("/squad")
def get_squad():
    ref = db.reference('squad')
    squad_data = ref.get()
    
    if(squad_data is None):
        return {"message": []}

    players = getPlayers();
    
    # Get player IDs from the squad data
    squad_player_ids = [player['player_id'] for player in squad_data]
    
    # Get players from the API that are in the squad
    squad_players = [player for player in players if player.id in squad_player_ids]
    
    return squad_players


@app.post("/add_player")
def add_player(player_data: AddPlayerDTO):
    ref = db.reference('squad')
    # Get current squad data
    current_squad = ref.get() or []
    # Add the new player data to the squad

    # Check if current squad is 15 players
    if len(current_squad) >= 15:
        return {"message": "Squad is full. Cannot add more players."}

    if player_data.in_bench:
        # Check if there are already 4 players in the bench
        bench_players = [
            player for player in current_squad if player.get('in_bench')]
        if len(bench_players) >= 4:
            return {"message": "Bench is full. Cannot add more players to the bench."}

    # Check if the player is already in the squad
    if any(player['player_id'] == player_data.player_id for player in current_squad):
        return {"message": "Player already in squad"}

    current_squad.append(player_data.__dict__)

    ref.set(current_squad)
    return {"message": "Player added successfully"}


@app.get("/remove_player/{player_id}")
def remove_player(player_id: int):
    ref = db.reference('squad')
    current_squad = ref.get() or []
    # Remove the player with the given player_id
    updated_squad = [player for player in current_squad if player.get(
        'player_id') != player_id]

    if len(updated_squad) == len(current_squad):
        return {"message": "Player not found in squad"}

    ref.set(updated_squad)
    return {"message": "Player removed successfully"}


@app.delete("/clear_squad")
def clear_squad():
    ref = db.reference('squad')
    ref.set([])  # Clear the squad by setting it to an empty list
    return {"message": "Squad cleared successfully"}


@app.get("/squad")
def get_squad():
    ref = db.reference('squad')
    squad_data = ref.get()

    return squad_data


@https_fn.on_request()
def main(req: https_fn.Request) -> https_fn.Response:
    try:
        asgi_request = {
            "type": "http",
            "method": req.method,
            "path": req.path,
            "headers": [
                (k.lower().encode(), v.encode()) for k, v in req.headers.items()
            ],
            "query_string": req.query_string or b"",
            "body": req.get_data() or b"",
        }

        # Async function to receive request body
        async def receive():
            return {
                "type": "http.request",
                "body": req.get_data() or b"",
                "more_body": False,
            }

        # Variables to collect response data
        response_body = []
        response_headers = []
        response_status = 200

        # Async function to send response
        async def send(message):
            nonlocal response_body, response_headers, response_status
            if message["type"] == "http.response.start":
                response_status = message.get("status", 200)
                response_headers = message.get("headers", [])
            elif message["type"] == "http.response.body":
                response_body.append(message.get("body", b""))

        # Run the ASGI app in an asyncio loop
        async def run_asgi():
            # app is the FastAPI instance
            await app(asgi_request, receive, send)

        import asyncio
        asyncio.run(run_asgi())

        # Combine response body
        full_body = b"".join(response_body)

        # Convert headers to dict for `https_fn.Response`
        headers_dict = {
            k.decode() if isinstance(k, bytes) else k: v.decode() if isinstance(v, bytes) else v
            for k, v in response_headers
        }

        # Create Firebase Functions response
        return https_fn.Response(
            response=full_body,
            status=response_status,
            headers=headers_dict,
        )

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return https_fn.Response(
            response=json.dumps({"error": "Internal Server Error"}),
            status=500,
            headers={"Content-Type": "application/json"},
        )


# Entry point for bootstrapping the application
# if __name__ == "__main__":
    # config = get_config()
    # uvicorn.run(app, host=config.host, port=config.port)
