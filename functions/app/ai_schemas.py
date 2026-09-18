"""JSON schemas passed to Claude's structured-output config."""


def transfer_pair_schema():
    """One player swapped out for one player in."""
    return {
        "type": "object",
        "properties": {
            "player_out_id": {"type": "integer"},
            "player_in_id": {"type": "integer"},
        },
        "required": ["player_out_id", "player_in_id"],
        "additionalProperties": False,
    }


def player_ref_schema():
    return {
        "type": "object",
        "properties": {"id": {"type": "integer"}},
        "required": ["id"],
        "additionalProperties": False,
    }
