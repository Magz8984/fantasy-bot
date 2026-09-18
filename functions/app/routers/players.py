from dataclasses import asdict

from fastapi import APIRouter

from app.fpl_client import getBootStrap, getCurrentGameWeek
from app.squad_service import getFormattedPlayers

router = APIRouter(tags=["players"])


@router.get("/api/bootstrap_static")
def bootstrap_static():
    return asdict(getBootStrap())


@router.get("/api/current_game_week")
def current_game_week():
    return asdict(getCurrentGameWeek())


@router.get("/api/player_ranking")
def player_ranking():
    players = getFormattedPlayers()
    players.sort(key=lambda player: player.calculated_form, reverse=True)
    return {"message": players}
