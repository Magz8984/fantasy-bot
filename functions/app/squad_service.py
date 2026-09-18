"""Squad state (read from Firebase RTDB), and the end-to-end
"analyze this gameweek" orchestration."""
from dataclasses import asdict

from app.ai_client import getSquadAnalysis
from app.firebase_app import get_ref
from app.fpl_client import getBootStrap, getCurrentGameWeek
from app.models import GameWeekAIRecommendations, Player
from app.config import ANTHROPIC_API_KEY

POSITION_ORDER = {"GKP": 0, "DEF": 1, "MID": 2, "FWD": 3}


def getSquad(players: list[Player]):
    ref = get_ref("squad")
    squad_data = ref.get() or []

    squad_players = {p.get("player_id"): p for p in squad_data}

    squad = []
    for player in players:
        squad_info = squad_players.get(player.id)
        if squad_info:
            player.in_squad = True
            player.in_bench = squad_info.get("in_bench", False)
            squad.append(player)

    squad.sort(key=lambda p: POSITION_ORDER.get(p.element_type_name, 99))
    return squad


def getFormattedPlayers():
    """All players, annotated with in_squad/in_bench from Firebase."""
    players = getBootStrap().players

    ref = get_ref("squad")
    squad_data = ref.get() or []
    squad_players = {p.get("player_id"): p for p in squad_data}

    for player in players:
        squad_info = squad_players.get(player.id)
        if squad_info:
            player.in_squad = True
            player.in_bench = squad_info.get("in_bench", False)
        else:
            player.in_squad = False
            player.in_bench = False

    return players


def processSquadAnalysis():
    """Generates (or returns cached) AI squad analysis for the current gameweek."""
    print(ANTHROPIC_API_KEY)
    try:
        current_game_week = getCurrentGameWeek()

        # Use the gameweek deadline timestamp as the unique ID.
        # This prevents collisions between seasons.
        ref = get_ref(f"events/{current_game_week.deadline_time_epoch}")

        # Only generate one AI recommendation per gameweek.
        existing_recommendations = ref.get()
        if existing_recommendations:
            return existing_recommendations

        players = getFormattedPlayers()
        recommendations = getSquadAnalysis(players, current_game_week)
        squad = getSquad(players)

        gameweek_recommendations = GameWeekAIRecommendations(
            recommendations=recommendations,
            gameweek=current_game_week.id,
            squad=squad,
        )

        data = asdict(gameweek_recommendations)
        ref.set(data)
        return data

    except Exception as e:
        print(f"Error processing squad analysis: {e}")
        return None


def add_player_to_squad(player_data):
    ref = get_ref("squad")
    current_squad = ref.get() or []

    if len(current_squad) >= 15:
        return {"message": "Squad is full. Cannot add more players."}

    if player_data.in_bench:
        bench_players = [p for p in current_squad if p.get("in_bench")]
        if len(bench_players) >= 4:
            return {"message": "Bench is full. Cannot add more players to the bench."}

    if any(p["player_id"] == player_data.player_id for p in current_squad):
        return {"message": "Player already in squad"}

    current_squad.append(player_data.__dict__)
    ref.set(current_squad)
    return {"message": "Player added successfully"}


def remove_player_from_squad(player_id: int):
    ref = get_ref("squad")
    current_squad = ref.get() or []

    updated_squad = [p for p in current_squad if p.get("player_id") != player_id]
    if len(updated_squad) == len(current_squad):
        return {"message": "Player not found in squad"}

    ref.set(updated_squad)
    return {"message": "Player removed successfully"}


def clear_squad():
    ref = get_ref("squad")
    ref.set([])
    return {"message": "Squad cleared successfully"}
