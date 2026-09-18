from dataclasses import dataclass, field
from typing import Any, List, Optional


@dataclass
class GameweekOverrides:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
    rules: dict
    scoring: dict
    element_types: list
    pick_multiplier: Optional[int]


@dataclass
class Gameweek:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
    id: int
    name: str
    deadline_time: str
    release_time: Optional[str]
    average_entry_score: int
    finished: bool
    data_checked: bool
    highest_scoring_entry: Optional[int]
    deadline_time_epoch: int
    deadline_time_game_offset: int
    highest_score: Optional[int]
    is_previous: bool
    is_current: bool
    is_next: bool
    cup_leagues_created: bool
    h2h_ko_matches_created: bool
    can_enter: bool
    can_manage: bool
    released: bool
    ranked_count: int
    overrides: GameweekOverrides
    chip_plays: list
    most_selected: Optional[int]
    most_transferred_in: Optional[int]
    top_element: Optional[int]
    top_element_info: Optional[Any]
    transfers_made: int
    most_captained: Optional[int]
    most_vice_captained: Optional[int]


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
    ict_index: float  # Influence, Creativity, Threat
    starts_per_90: float
    form_rank: int
    team_name: str
    news: str
    calculated_form: float
    element_type: int
    element_type_name: str
    f_e_r: str
    in_squad: bool = False  # Whether the player is in the squad or not
    in_bench: bool = False  # Whether the player is in the bench or not


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


@dataclass
class BootstrapStatic:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
    events: list[Gameweek]
    element_types: list[PlayerType]
    teams: list[Team]
    players: list[Player]


# ---------------------------------------------------------------------
# AI recommendation data types
# ---------------------------------------------------------------------

@dataclass
class TransferPair:
    player_out_id: int
    player_in_id: int

    @classmethod
    def from_dict(cls, data: dict) -> "TransferPair":
        return cls(
            player_out_id=data["player_out_id"],
            player_in_id=data["player_in_id"],
        )


@dataclass
class PlayerRef:
    id: int

    @classmethod
    def from_dict(cls, data: dict) -> "PlayerRef":
        return cls(id=data["id"])


@dataclass
class Recommendation:
    transfers: List[TransferPair] = field(default_factory=list)
    substitutions: List[TransferPair] = field(default_factory=list)
    captain: PlayerRef = None
    vice_captain: PlayerRef = None
    summary: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> "Recommendation":
        return cls(
            transfers=[TransferPair.from_dict(t)
                       for t in data.get("transfers", [])],
            substitutions=[TransferPair.from_dict(
                s) for s in data.get("substitutions", [])],
            captain=PlayerRef.from_dict(data["captain"]),
            vice_captain=PlayerRef.from_dict(data["vice_captain"]),
            summary=data.get("summary", ""),
        )


@dataclass
class HydratedTransfer:
    player_out: Optional[Player] = None
    player_in: Optional[Player] = None


@dataclass
class HydratedSubstitution:
    player_in: Optional[Player] = None
    player_out: Optional[Player] = None


@dataclass
class HydratedRecommendation:
    transfers: List[HydratedTransfer] = field(default_factory=list)
    substitutions: List[HydratedSubstitution] = field(default_factory=list)
    captain: Optional[Player] = None
    vice_captain: Optional[Player] = None
    summary: str = ""


@dataclass
class GameWeekAIRecommendations:
    recommendations: HydratedRecommendation
    gameweek: int = 0
    squad: list = field(default_factory=list)
