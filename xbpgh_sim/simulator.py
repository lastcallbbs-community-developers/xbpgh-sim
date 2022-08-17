from typing import Optional
from copy import deepcopy

from .models import *


__all__ = ["simulate_step", "simulate_solution"]


def simulate_step(prv_state: State, rules: list[Rule]) -> StepResult:
    nxt_state = deepcopy(prv_state)
    dead_cells = set()

    rules_applied: list[list[Optional[int]]] = [
        [None for _ in range(5)] for _ in range(4)
    ]

    def try_apply_rule(loc: Coords, rule: Rule) -> bool:
        if rule.target_type == CellType.IGNORE:
            return False

        if rule.target_type != prv_state.cell_types[loc.x][loc.y]:
            return False

        # The type can't have changed under these rules
        assert nxt_state.cell_types[loc.x][loc.y] == rule.target_type
        assert rule.target_type.is_living()

        if rule.neighbor_type != CellType.IGNORE:
            n_loc = loc + rule.neighbor_dir.delta()
            n_type = (
                prv_state.cell_types[n_loc.x][n_loc.y]
                if n_loc.in_bounds()
                else CellType.NONE
            )

            if rule.neighbor_type == CellType.ANY:
                if n_type == CellType.NONE:
                    return False
            else:
                if n_type != rule.neighbor_type:
                    return False

        if rule.reaction == Reaction.IGNORE:
            return False

        elif rule.reaction == Reaction.DIVIDE:
            assert rule.divide_dir is not None
            n_loc = loc + rule.divide_dir.delta()
            if not (
                n_loc.in_bounds()
                and nxt_state.cell_types[n_loc.x][n_loc.y] == CellType.NONE
            ):
                return False

            nxt_state.cell_types[n_loc.x][n_loc.y] = nxt_state.cell_types[loc.x][loc.y]

            if loc.x != n_loc.x:
                nxt_state.horz_connected[min(loc.x, n_loc.x)][loc.y] = True
            else:
                nxt_state.vert_connected[loc.x][min(loc.y, n_loc.y)] = True

            assert nxt_state.live_cells is not None
            nxt_state.live_cells.append(n_loc)

            return True

        elif rule.reaction == Reaction.DIE:
            dead_cells.add(loc)
            return True

        elif rule.reaction == Reaction.FUSE:
            assert rule.fuse_dir is not None

            n_loc = loc + rule.fuse_dir.delta()
            if not (
                n_loc.in_bounds() and nxt_state.cell_types[n_loc.x][n_loc.y].is_living()
            ):
                return False

            if loc.x != n_loc.x:
                if nxt_state.horz_connected[min(loc.x, n_loc.x)][loc.y]:
                    return False
                nxt_state.horz_connected[min(loc.x, n_loc.x)][loc.y] = True
                return True
            else:
                if nxt_state.vert_connected[loc.x][min(loc.y, n_loc.y)]:
                    return False
                nxt_state.vert_connected[loc.x][min(loc.y, n_loc.y)] = True
                return True

        elif rule.reaction == Reaction.SPECIALIZE:
            assert rule.spec_type is not None
            nxt_state.cell_types[loc.x][loc.y] = rule.spec_type
            return True

        else:
            raise ValueError(f"Invalid reaction {rule.reaction}")

    did_change = False
    assert prv_state.live_cells is not None
    for loc in prv_state.live_cells:
        for rule_num, rule in enumerate(rules):
            if try_apply_rule(loc, rule):
                rules_applied[loc.x][loc.y] = rule_num
                nxt_state.check_state()
                did_change = True
                break
        else:
            # This cell does NOOP
            pass

    for loc in dead_cells:
        nxt_state.cell_types[loc.x][loc.y] = CellType.NONE

        if loc.x > 0:
            nxt_state.horz_connected[loc.x - 1][loc.y] = False
        if loc.x + 1 < 4:
            nxt_state.horz_connected[loc.x][loc.y] = False

        if loc.y > 0:
            nxt_state.vert_connected[loc.x][loc.y - 1] = False
        if loc.y + 1 < 5:
            nxt_state.vert_connected[loc.x][loc.y] = False

    assert nxt_state.live_cells is not None
    nxt_state.live_cells = [
        loc for loc in nxt_state.live_cells if loc not in dead_cells
    ]

    return StepResult(nxt_state, rules_applied, len(dead_cells), did_change)


def simulate_solution(level: Level, solution: Solution) -> SimulationResult:
    state = State(
        cell_types=[
            [CellType.METAL if t == CellType.METAL else CellType.NONE for t in a]
            for a in level.target_state.cell_types
        ],
        horz_connected=[[False for _ in range(5)] for _ in range(3)],
        vert_connected=[[False for _ in range(4)] for _ in range(4)],
    )

    if solution.metal_coords:
        assert level.can_place_metal
        for loc in solution.metal_coords:
            state.cell_types[loc.x][loc.y] = CellType.METAL

    if state.cell_types[solution.start_pos.x][solution.start_pos.y] != CellType.NONE:
        raise ValueError(f"Invalid starting position {solution.start_pos}")

    state.cell_types[solution.start_pos.x][solution.start_pos.y] = CellType.SEED
    state.live_cells = [solution.start_pos]

    num_rules = sum(r.target_type != CellType.IGNORE for r in solution.rules)
    num_rules_conditional = sum(
        r.neighbor_type != CellType.IGNORE for r in solution.rules
    )

    num_frames = 1
    num_waste = 0

    states = [state]
    rules_applied = []
    for _ in range(11):
        res = simulate_step(state, solution.rules)

        state = res.state
        states.append(state)

        rules_applied.append(res.rules_applied)

        num_waste += res.num_waste
        num_frames += res.did_change

    is_stable = not simulate_step(state, solution.rules).did_change

    final_state = deepcopy(state)
    final_state.live_cells = None
    is_correct = final_state == level.target_state

    is_wasteful = num_waste > level.theoretical_min_waste
    if is_correct:
        assert num_waste >= level.theoretical_min_waste

    return SimulationResult(
        level=level,
        solution=solution,
        states=states,
        rules_applied=rules_applied,
        final_state=final_state,
        metrics=Metrics(
            is_correct=is_correct,
            num_rules=num_rules,
            num_rules_conditional=num_rules_conditional,
            num_frames=num_frames,
            is_stable=is_stable,
            num_waste=num_waste,
            is_wasteful=is_wasteful,
        ),
    )
