"""Fetches and normalizes data from the public Fantasy Premier League API."""
import requests

from app.models import BootstrapStatic, Gameweek, Player, PlayerType, Team


def getBootStrap() -> BootstrapStatic:
    request = requests.get(
        "https://fantasy.premierleague.com/api/bootstrap-static/"
    )
    data = request.json()

    events = [Gameweek(**event) for event in data.get("events", [])]
    element_types = [PlayerType(**et) for et in data.get("element_types", [])]
    teams = [Team(**team) for team in data.get("teams", [])]
    players = [Player(**player) for player in data.get("elements", [])]

    # Add application-specific fields: team_name, element_type_name,
    # calculated_form, f_e_r, etc.
    players = sanitizePlayers(players, teams, element_types)

    return BootstrapStatic(
        events=events,
        element_types=element_types,
        teams=teams,
        players=players,
    )


def getCurrentGameWeek():
    bootstrap = getBootStrap()
    events = bootstrap.events
    return next((gw for gw in events if gw.is_current), None)


def findTeamById(teams: list[Team], team_id: int):
    for team in teams:
        if team.id == team_id:
            return team
    return None


def sanitizePlayers(players: list[Player], teams: list[Team], player_types: list[PlayerType]):
    """Adds team_name, calculated_form, f_e_r, and converts now_cost to float."""
    for player in players:
        team = findTeamById(teams, player.team)
        player.team_name = team.name if team else "Unknown"
        player.now_cost = player.now_cost / 10  # Convert to float

        player.calculated_form = (
            (float(player.expected_goal_involvements) * 0.4)
            + (float(player.form) * 0.3)
            + (float(player.ict_index) * 0.3)
        )

        player.f_e_r = (
            player.calculated_form / player.now_cost
            if player.now_cost != 0 else 0
        )

    for player in players:
        player_type = next(
            (pt for pt in player_types if pt.id == player.element_type), None
        )
        player.element_type_name = player_type.singular_name_short if player_type else "Unknown"

    return players
