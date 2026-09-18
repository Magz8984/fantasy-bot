"""Everything related to calling Claude for squad recommendations:
building compact prompts, the system prompt, and hydrating the response
back into full Player objects.
"""
import json

from anthropic import Anthropic

from app.config import ANTHROPIC_API_KEY, CLAUDE_MODEL
from app.ai_schemas import player_ref_schema, transfer_pair_schema
from app.models import HydratedRecommendation, HydratedSubstitution, HydratedTransfer, Player, Recommendation

SYSTEM_PROMPT = """
You are an FPL manager analyzing my squad for the upcoming gameweek.

Rules:

- "squad=true" means the player is currently in my 15-man squad.
- "bench=true" means the player is currently on my bench.
- "bench=false" means the player is currently in the starting XI.
- Transfers may only bring in players with squad=false.
- A transfer must replace a player with the same position.
- Substitutions may only bring a bench player into the XI.
- Substitutions must replace a starting-XI player.
- Do not use a player in more than one action.
- Reference players using their ID only.
- Do not invent player IDs.
- Only select transfer targets from transfer_candidates.

Return:
- recommended transfers
- recommended substitutions
- captain
- vice captain
- concise reasoning

If an action is not justified, return an empty array.
"""


def compact_player(player: Player) -> dict:
    return {
        "id": player.id,
        "name": f"{player.first_name} {player.second_name}",
        "pos": player.element_type_name,
        "team": player.team_name,
        "price": player.now_cost,
        "form": player.form,
        "minutes": player.minutes,
        "xGI": player.expected_goal_involvements,
        "xGC": player.expected_goals_conceded,
        "ict": player.ict_index,
        "FER": round(player.f_e_r, 2),
        "squad": player.in_squad,
        "bench": player.in_bench,
        "news": player.news,
    }


def build_transfer_candidates(player_data):
    """
    For each benched/weak squad player, only include transfer-in candidates
    that are (a) not already in_squad, and (b) same element_type_name.
    This makes an invalid pairing structurally unreachable.
    """
    squad = [p for p in player_data if p["in_squad"]]
    pool = [p for p in player_data if not p["in_squad"]]

    candidates = []
    for out_player in squad:
        same_position_pool = [
            p for p in pool
            if p["element_type_name"] == out_player["element_type_name"]
        ]
        # keep it light — top N by form/f_e_r so you're not bloating the prompt
        same_position_pool = sorted(
            same_position_pool, key=lambda p: p["f_e_r"], reverse=True
        )[:8]

        candidates.append({
            "player_out": out_player,
            "eligible_replacements": same_position_pool,
        })
    return candidates


def build_substitution_candidates(player_data):
    """
    Only pair bench players (in_bench=true) with starting-XI players
    (in_squad=true, in_bench=false) of the same position.
    """
    squad = [p for p in player_data if p["in_squad"]]
    bench = [p for p in squad if p["in_bench"]]
    starting_xi = [p for p in squad if not p["in_bench"]]

    candidates = []
    for bench_player in bench:
        eligible_outs = [
            p for p in starting_xi
            if p["element_type_name"] == bench_player["element_type_name"]
        ]
        candidates.append({
            "player_in": bench_player,
            "eligible_to_bench": eligible_outs,
        })
    return candidates


def getSquadAnalysis(players: list[Player], current_game_week=None) -> HydratedRecommendation:
    claude_client = Anthropic(api_key=ANTHROPIC_API_KEY)

    # 1. Current squad
    squad = [p for p in players if p.in_squad]
    squad_data = [compact_player(p) for p in squad]

    # 2. Transfer candidates
    transfer_pool = []
    for position in ["GKP", "DEF", "MID", "FWD"]:
        position_players = [
            p for p in players
            if (not p.in_squad and p.element_type_name == position)
        ]
        position_players = sorted(
            position_players, key=lambda p: p.f_e_r, reverse=True
        )[:10]
        transfer_pool.extend(compact_player(p) for p in position_players)

    # 3. Current gameweek
    gameweek_data = None
    if current_game_week:
        gameweek_data = {
            "id": current_game_week.id,
            "name": current_game_week.name,
            "deadline": current_game_week.deadline_time,
        }

    # 4. Build compact prompt
    user_content = {
        "gameweek": gameweek_data,
        "squad": squad_data,
        "transfer_candidates": transfer_pool,
    }

    params = {
        "model": CLAUDE_MODEL,
        "max_tokens": 1200,
        "system": SYSTEM_PROMPT,
        "messages": [
            {
                "role": "user",
                "content": json.dumps(user_content, separators=(",", ":")),
            }
        ],
        "output_config": {
            "format": {
                "type": "json_schema",
                "schema": {
                    "type": "object",
                    "properties": {
                        "transfers": {
                            "type": "array",
                            "items": transfer_pair_schema(),
                        },
                        "substitutions": {
                            "type": "array",
                            "items": transfer_pair_schema(),
                        },
                        "captain": player_ref_schema(),
                        "vice_captain": player_ref_schema(),
                        "summary": {
                            "type": "string",
                            "description": "Concise recommendation reasoning.",
                        },
                    },
                    "required": [
                        "transfers",
                        "substitutions",
                        "captain",
                        "vice_captain",
                        "summary",
                    ],
                    "additionalProperties": False,
                },
            }
        },
    }

    response = claude_client.messages.create(**params, extra_body={"temperature": 0})

    raw = json.loads(
        next(b.text for b in response.content if b.type == "text")
    )

    recommendation = Recommendation.from_dict(raw)

    return hydrate_recommendation(recommendation, players)


def hydrate_recommendation(
    recommendation: Recommendation,
    players: list[Player],
) -> HydratedRecommendation:
    """Replaces player IDs with full Player objects from the provided list."""
    player_map = {player.id: player for player in players}

    hydrated_transfers = [
        HydratedTransfer(
            player_out=player_map.get(t.player_out_id),
            player_in=player_map.get(t.player_in_id),
        )
        for t in recommendation.transfers
    ]

    hydrated_substitutions = [
        HydratedSubstitution(
            player_in=player_map.get(s.player_in_id),
            player_out=player_map.get(s.player_out_id),
        )
        for s in recommendation.substitutions
    ]

    hydrated_captain = (
        player_map.get(recommendation.captain.id) if recommendation.captain else None
    )
    hydrated_vice_captain = (
        player_map.get(recommendation.vice_captain.id)
        if recommendation.vice_captain else None
    )

    return HydratedRecommendation(
        transfers=hydrated_transfers,
        substitutions=hydrated_substitutions,
        captain=hydrated_captain,
        vice_captain=hydrated_vice_captain,
        summary=recommendation.summary,
    )
