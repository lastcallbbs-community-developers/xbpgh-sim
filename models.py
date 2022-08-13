from __future__ import annotations

from enum import Enum, unique
from dataclasses import dataclass
from typing import Optional


__all__ = [
    "Coords",
    "CellType",
    "Direction",
    "Reaction",
    "Rule",
    "Solution",
    "State",
    "Level",
    "Metrics",
    "StepResult",
    "SimulationResult",
]


@dataclass(eq=True, order=True, frozen=True)
class Coords:
    x: int
    y: int

    def in_bounds(self) -> bool:
        return 0 <= self.x < 4 and 0 <= self.y < 5

    def __add__(self, o: Coords) -> Coords:
        return Coords(self.x + o.x, self.y + o.y)


@unique
class CellType(Enum):
    IGNORE = 0
    SEED = 1
    FLESH = 2
    # NB: Note this transposition
    FLESH_MUSCLE = 4
    FLESH_HEART = 3
    FLESH_FAT = 5
    BONE = 6
    BONE_SPINE = 7
    SKIN = 8
    SKIN_HAIR = 9
    SKIN_EYE = 10
    METAL = 11
    ANY = 12
    NONE = 13

    def is_living(self) -> bool:
        return self not in {
            CellType.IGNORE,
            CellType.METAL,
            CellType.ANY,
            CellType.NONE,
        }

    def to_symbol(self) -> str:
        return {
            CellType.IGNORE: " ",
            CellType.SEED: "*",
            CellType.FLESH: "f",
            CellType.FLESH_MUSCLE: "M",
            CellType.FLESH_HEART: "H",
            CellType.FLESH_FAT: "F",
            CellType.BONE: "b",
            CellType.BONE_SPINE: "B",
            CellType.SKIN: "s",
            CellType.SKIN_HAIR: "W",
            CellType.SKIN_EYE: "O",
            CellType.METAL: "█",
            CellType.ANY: "?",
            CellType.NONE: "_",
        }[self]

    @staticmethod
    def from_symbol(s: str) -> CellType:
        return {
            " ": CellType.IGNORE,
            "*": CellType.SEED,
            "f": CellType.FLESH,
            "M": CellType.FLESH_MUSCLE,
            "H": CellType.FLESH_HEART,
            "F": CellType.FLESH_FAT,
            "b": CellType.BONE,
            "B": CellType.BONE_SPINE,
            "s": CellType.SKIN,
            "W": CellType.SKIN_HAIR,
            "O": CellType.SKIN_EYE,
            "█": CellType.METAL,
            "X": CellType.METAL,  # Alternative
            "?": CellType.ANY,
            "_": CellType.NONE,
        }[s]


@unique
class Direction(Enum):
    RIGHT = 1
    UP = 2
    LEFT = 4
    DOWN = 8

    def delta(self) -> Coords:
        if self == Direction.RIGHT:
            return Coords(+1, 0)
        elif self == Direction.UP:
            return Coords(0, +1)
        elif self == Direction.LEFT:
            return Coords(-1, 0)
        elif self == Direction.DOWN:
            return Coords(0, -1)
        else:
            assert False


@unique
class Reaction(Enum):
    IGNORE = 0
    DIVIDE = 1
    DIE = 4
    FUSE = 3
    SPECIALIZE = 2


@dataclass
class Rule:
    target_type: CellType
    neighbor_type: CellType
    neighbor_dir: Direction
    reaction: Reaction
    divide_dir: Optional[Direction] = None
    fuse_dir: Optional[Direction] = None
    spec_type: Optional[CellType] = None

    def check_rule(self):
        assert self.target_type not in {
            CellType.METAL,
            CellType.ANY,
            CellType.NONE,
        }, "Target cannot be METAL, ANY or NONE"
        if self.target_type == CellType.IGNORE:
            assert (
                self.neighbor_type == CellType.IGNORE
            ), "Rules with no target must have no neighbor"
            assert (
                self.reaction == Reaction.IGNORE
            ), "Rules with no target must have no reaction"

        assert (self.divide_dir is not None) == (self.reaction == Reaction.DIVIDE)
        assert (self.fuse_dir is not None) == (self.reaction == Reaction.FUSE)
        assert (self.spec_type is not None) == (self.reaction == Reaction.SPECIALIZE)

        # Type-specific checks
        if self.target_type == CellType.BONE_SPINE:
            assert (
                self.reaction == Reaction.IGNORE
            ), "Spine cells cannot perform any action"
        if self.target_type == CellType.SKIN_EYE:
            assert self.reaction != Reaction.DIVIDE, "Eye cells cannot divide"

        if self.reaction == Reaction.SPECIALIZE:
            if self.target_type == CellType.SEED:
                assert self.spec_type in {
                    CellType.FLESH,
                    CellType.BONE,
                    CellType.SKIN,
                }, "Invalid seed specialization"
            elif self.target_type == CellType.FLESH:
                assert self.spec_type in {
                    CellType.FLESH_MUSCLE,
                    CellType.FLESH_HEART,
                    CellType.FLESH_FAT,
                }, "Invalid flesh specialization"
            elif self.target_type == CellType.BONE:
                assert self.spec_type in {
                    CellType.BONE_SPINE
                }, "Invalid bone specialization"
            elif self.target_type == CellType.SKIN:
                assert self.spec_type in {
                    CellType.SKIN_HAIR,
                    CellType.SKIN_EYE,
                }, "Invalid skin specialization"
            else:
                assert False, "Invalid specialization"

        # If a rule has neighbor conditionals, it may be unable to divide/fuse in that direction
        if self.neighbor_type != CellType.IGNORE:
            if (
                self.reaction == Reaction.DIVIDE
                and self.divide_dir == self.neighbor_dir
            ):
                assert (
                    self.neighbor_type == CellType.NONE
                ), "Cannot divide into conditional neighbor"
            if self.reaction == Reaction.FUSE and self.fuse_dir == self.neighbor_dir:
                assert self.neighbor_type not in {
                    CellType.METAL,
                    CellType.NONE,
                }, "Cannot fuse into non-cell neighbor"

    def visualize(self) -> str:
        g = [[" " for _ in range(5)] for _ in range(5)]

        loc = Coords(1, 1)
        g[2 * loc.x][2 * loc.y] = self.target_type.to_symbol()

        n_loc = loc + self.neighbor_dir.delta()
        g[2 * n_loc.x][2 * n_loc.y] = self.neighbor_type.to_symbol()

        h = [[" " for _ in range(5)] for _ in range(5)]

        loc = Coords(1, 1)
        h[2 * loc.x][2 * loc.y] = self.target_type.to_symbol()

        n_loc = loc + self.neighbor_dir.delta()
        h[2 * n_loc.x][2 * n_loc.y] = self.neighbor_type.to_symbol()

        if self.reaction == Reaction.DIVIDE:
            assert self.divide_dir is not None
            n_loc = loc + self.divide_dir.delta()
            h[2 * n_loc.x][2 * n_loc.y] = self.target_type.to_symbol()
            h[loc.x + n_loc.x][loc.y + n_loc.y] = "-" if loc.x != n_loc.x else "|"

        elif self.reaction == Reaction.DIE:
            h[2 * loc.x][2 * loc.y] = CellType.NONE.to_symbol()

        elif self.reaction == Reaction.FUSE:
            assert self.fuse_dir is not None
            n_loc = loc + self.fuse_dir.delta()
            h[2 * n_loc.x][2 * n_loc.y] = self.target_type.to_symbol()
            h[loc.x + n_loc.x][loc.y + n_loc.y] = "-" if loc.x != n_loc.x else "|"

        elif self.reaction == Reaction.SPECIALIZE:
            assert self.spec_type is not None
            h[2 * loc.x][2 * loc.y] = self.spec_type.to_symbol()

        g_lines = (
            ["┌" + "─" * 5 + "┐"]
            + ["│" + "".join(s) + "│" for s in zip(*g)][::-1]
            + ["└" + "─" * 5 + "┘"]
        )
        mid = [" ", " ", " ", ">", " ", " ", " "]
        h_lines = (
            ["┌" + "─" * 5 + "┐"]
            + ["│" + "".join(s) + "│" for s in zip(*h)][::-1]
            + ["└" + "─" * 5 + "┘"]
        )

        return "\n".join("".join(t) for t in zip(g_lines, mid, h_lines))


@dataclass
class Solution:
    rules: list[Rule]
    start_pos: Coords
    metal_coords: list[Coords]


@dataclass
class State:
    # size 4 x 5
    cell_types: list[list[CellType]]

    # size 3 x 5
    # horz_connected[i][j] is whether (i, j) is connected to (i+1, j)
    horz_connected: list[list[bool]]

    # size 4 x 4
    # vert_connected[i][j] is whether (i, j) is connected to (i, j+1)
    vert_connected: list[list[bool]]

    live_cells: Optional[list[Coords]] = None

    def check_state(self):
        assert len(self.cell_types) == 4 and all(len(a) == 5 for a in self.cell_types)
        assert len(self.horz_connected) == 3 and all(
            len(a) == 5 for a in self.horz_connected
        )
        assert len(self.vert_connected) == 4 and all(
            len(a) == 4 for a in self.vert_connected
        )

        for i in range(4):
            for j in range(5):
                assert self.cell_types[i][j] not in {CellType.IGNORE, CellType.ANY}

                if i + 1 < 4 and self.horz_connected[i][j]:
                    assert (
                        self.cell_types[i][j].is_living()
                        and self.cell_types[i + 1][j].is_living()
                    )

                if j + 1 < 5 and self.vert_connected[i][j]:
                    assert (
                        self.cell_types[i][j].is_living()
                        and self.cell_types[i][j + 1].is_living()
                    )

        if self.live_cells is not None:
            assert set(
                Coords(i, j)
                for i in range(4)
                for j in range(5)
                if self.cell_types[i][j].is_living()
            ) == set(self.live_cells)
            assert len(self.live_cells) == len(set(self.live_cells))

    def __post_init__(self):
        self.check_state()

    def visualize(self) -> str:
        g = [[" " for _ in range(9)] for _ in range(7)]
        for x in range(4):
            for y in range(5):
                g[2 * x][2 * y] = self.cell_types[x][y].to_symbol()

        for x in range(3):
            for y in range(5):
                if self.horz_connected[x][y]:
                    g[2 * x + 1][2 * y] = "-"

        for x in range(4):
            for y in range(4):
                if self.vert_connected[x][y]:
                    g[2 * x][2 * y + 1] = "|"

        result = (
            ["┌" + "─" * 7 + "┐"]
            + ["│" + "".join(s) + "│" for s in zip(*g)][::-1]
            + ["└" + "─" * 7 + "┘"]
        )
        return "\n".join(result)

    @classmethod
    def from_visualize(cls, s: str) -> State:
        """Initialize a state from a 9x7 ASCII art block, possibly with a border"""
        g = list(zip(*reversed(s.split("\n"))))
        if len(g) == 9 and all(len(a) == 11 for a in g):
            g = [a[1:-1] for a in g[1:-1]]
        assert len(g) == 7 and all(len(a) == 9 for a in g)

        return cls(
            cell_types=[
                [CellType.from_symbol(g[2 * x][2 * y]) for y in range(5)]
                for x in range(4)
            ],
            horz_connected=[
                [g[2 * x + 1][2 * y] == "-" for y in range(5)] for x in range(3)
            ],
            vert_connected=[
                [g[2 * x][2 * y + 1] == "|" for y in range(4)] for x in range(4)
            ],
        )


@dataclass
class Level:
    level_id: int
    level_name: str
    level_index: int  # for sorting

    target_state: State

    can_place_metal: bool = False


@dataclass
class Metrics:
    is_correct: bool
    num_rules: int
    num_rules_conditional: int
    num_frames: int
    is_stable: bool
    num_waste: int


@dataclass
class StepResult:
    state: State
    rules_applied: list[list[Optional[int]]]
    num_waste: int
    did_change: bool


@dataclass
class SimulationResult:
    level: Level
    solution: Solution

    states: list[State]
    rules_applied: list[list[list[Optional[int]]]]

    final_state: State

    metrics: Metrics
