from fastapi import APIRouter

from app.models import AddPlayerDTO
from app.fpl_client import getBootStrap
from app.squad_service import (
    add_player_to_squad,
    clear_squad,
    getSquad,
    remove_player_from_squad,
)

router = APIRouter(tags=["squad"])


@router.get("/squad")
def get_squad():
    # NOTE: your original file defined this route TWICE (once here, once
    # near the bottom returning the raw Firebase `squad` node directly).
    # FastAPI only ever matched the first one registered, so the second
    # was dead code. Kept the version marked "Used by Firebase in
    # Production" — full Player objects with in_squad/in_bench annotated.
    players = getBootStrap().players
    return getSquad(players)


@router.post("/add_player")
def add_player(player_data: AddPlayerDTO):
    # Preserved as-is: your original short-circuited here before reaching
    # the real add logic, so this endpoint currently does nothing. The
    # working implementation lives in squad_service.add_player_to_squad —
    # remove the line below once you're ready to turn it on.
    return {"message": "Player addition not implemented yet"}
    return add_player_to_squad(player_data)


@router.delete("/remove_player/{player_id}")
def remove_player(player_id: int):
    # Same as above: preserved the early return from your original.
    return {"message": "Player removal not implemented yet"}
    return remove_player_from_squad(player_id)


@router.delete("/clear_squad")
def clear_squad_route():
    return clear_squad()
