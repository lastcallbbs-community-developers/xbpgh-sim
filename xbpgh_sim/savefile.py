import base64
import zlib

from .models import *
from .levels import LEVELS


__all__ = ["parse_solution", "dump_solution", "parse_save_file"]


def parse_solution(save_string: str) -> Solution:
    """parses a decompressed solution"""
    dat = zlib.decompress(base64.b64decode(save_string, validate=True))

    def pop_int(b):
        nonlocal dat
        assert len(dat) >= b
        res = int.from_bytes(dat[:b], "little", signed=True)
        dat = dat[b:]
        return res

    # Version number
    version = pop_int(4)
    if version not in {1002, 1003}:
        raise ValueError(f"Unknown save file version {version}")

    num_rules = pop_int(4)
    assert num_rules == 16
    rules = []
    for _ in range(num_rules):
        target_type = CellType(pop_int(4))
        neighbor_type = CellType(pop_int(4))
        neighbor_dir = Direction(pop_int(4))
        reaction = Reaction(pop_int(1))

        rule = Rule(target_type, neighbor_type, neighbor_dir, reaction)

        if reaction == Reaction.DIVIDE:
            delta_x = pop_int(4)
            delta_y = pop_int(4)
            rule.divide_dir = next(
                dir for dir in Direction if dir.delta() == Coords(delta_x, delta_y)
            )
        elif reaction == Reaction.FUSE:
            fuse_dir = Direction(pop_int(4))
            rule.fuse_dir = fuse_dir
        elif reaction == Reaction.SPECIALIZE:
            spec_type = CellType(pop_int(4))
            rule.spec_type = spec_type

        rule.check_rule()
        rules.append(rule)

    start_x = pop_int(4)
    start_y = pop_int(4)
    start_loc = Coords(start_x, start_y)
    assert start_loc.in_bounds()

    metal_coords = []
    if version == 1003:
        num_metal = pop_int(4)
        for _ in range(num_metal):
            x = pop_int(4)
            y = pop_int(4)
            loc = Coords(x, y)
            assert loc.in_bounds()
            assert loc not in metal_coords
            metal_coords.append(loc)

    assert len(dat) == 0

    return Solution(rules, start_loc, metal_coords, save_string=save_string)


def dump_solution(solution: Solution) -> str:
    dat = b""

    def push_int(b, v):
        nonlocal dat
        dat += v.to_bytes(b, "little", signed=True)

    push_int(4, 1003)

    assert len(solution.rules) == 16
    push_int(4, len(solution.rules))
    for rule in solution.rules:
        rule.check_rule()
        push_int(4, rule.target_type.value)
        push_int(4, rule.neighbor_type.value)
        push_int(4, rule.neighbor_dir.value)
        push_int(1, rule.reaction.value)

        if rule.reaction == Reaction.DIVIDE:
            assert rule.divide_dir is not None
            coords = rule.divide_dir.delta()
            push_int(4, coords.x)
            push_int(4, coords.y)
        elif rule.reaction == Reaction.FUSE:
            assert rule.fuse_dir is not None
            push_int(4, rule.fuse_dir.value)
        elif rule.reaction == Reaction.SPECIALIZE:
            assert rule.spec_type is not None
            push_int(4, rule.spec_type.value)

    assert solution.start_pos.in_bounds()
    push_int(4, solution.start_pos.x)
    push_int(4, solution.start_pos.y)

    assert len(set(solution.metal_coords)) == len(solution.metal_coords)
    push_int(4, len(solution.metal_coords))
    for coords in solution.metal_coords:
        push_int(4, coords.x)
        push_int(4, coords.y)

    return base64.b64encode(zlib.compress(dat)).decode("ascii")


def parse_save_file(f) -> dict[int, dict[int, Solution]]:
    solutions = {level.level_id: {} for level in LEVELS}
    for line in f:
        line = line.rstrip("\n")
        if " = " in line:
            key, val = line.split(" = ")
            key = key.split(".")
            val = val.strip()
            if key[0] == "Toronto" and key[1] == "Solution":
                level_id = int(key[2])
                save_slot = int(key[3])

                solution = parse_solution(val)
                # Check round-tripping the solution
                # assert dat == dump_solution(solution)
                solutions[level_id][save_slot] = solution
    return solutions
