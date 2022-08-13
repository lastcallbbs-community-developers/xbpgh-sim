import sys

import dataclasses
from typing import Optional

from models import *
from savefile import *
from levels import *
from simulator import *


USAGE = """\
Usage:
  python -m main validate_all <save_file_path>
  python -m main simulate <level_name> <slot_number> <save_file_path>

<save_file_path> can be "-" for stdin
<level_name> can be be "1-2" for the 2nd level in the 1st column of the base game, or "B4-3" for the 3rd level in the 4th column of the bonus levels, or a bonus level name (e.g. "Clark"). Use "B5-3" or "editor" for the puzzle editor.
<slot_number> should be 0, 1, 2, or 3 (top-left, top-right, bottom-left, or bottom-right)
"""


def get_level_from_name(level_name) -> Optional[Level]:
    level_name = level_name.strip().lower()
    for level in LEVELS:
        if level_name == level.level_name.lower():
            return level

    if 'editor' in level_name:
        return LEVELS[-1]

    # Bonus level last names
    for level in LEVELS[15:29]:
        if level.level_name.split()[-1].lower() in level_name:
            return level

    # Try to parse 1-2, possibly with a leading "b" or "bonus"
    digits = [c for c in level_name if '0' <= c <= '9']
    if len(digits) == 2:
        col, row = map(int, digits)
        return LEVELS[(15 if level_name.startswith('b') else 0) + (col - 1) * 3 + (row - 1)]

    return None


def main():
    if len(sys.argv) == 1:
        print(USAGE)
        sys.exit(1)

    op = sys.argv[1]
    if op == "validate_all":
        if len(sys.argv) != 3:
            print(USAGE)
            sys.exit(1)
        fname = sys.argv[2]

        if fname == "-":
            solutions = parse_save_file(sys.stdin)
        else:
            with open(fname) as f:
                solutions = parse_save_file(f)

        for level in LEVELS:
            assert level.target_state == State.from_visualize(
                level.target_state.visualize()
            )
            for slot, solution in solutions[level.level_id].items():
                print(f"{level.level_name} (Slot {slot})")
                result = simulate_solution(level, solution)
                print(result.metrics)
                if not result.metrics.is_correct:
                    print("  Have         Want")
                    print(
                        "\n".join(
                            a + "    " + b
                            for a, b in zip(
                                result.final_state.visualize().split("\n"),
                                result.level.target_state.visualize().split("\n"),
                            )
                        )
                    )
                print()
    elif op == "simulate":
        if len(sys.argv) != 5:
            print(USAGE)
            sys.exit(1)

        level_name, slot, fname = sys.argv[2:]

        try:
            level = get_level_from_name(level_name)
            assert level is not None
        except Exception:
            print(f"Could not parse level name {level_name}")
            print(USAGE)
            sys.exit(1)

        slot = int(slot)

        if fname == "-":
            solutions = parse_save_file(sys.stdin)
        else:
            with open(fname) as f:
                solutions = parse_save_file(f)

        if slot not in solutions[level.level_id]:
            print(f"No solution in slot {slot} for level {level.level_name}")
            print("Slot should be 0, 1, 2, or 3 for top-left, top-right, bottom-left, or bottom-right")
            sys.exit(1)

        solution = solutions[level.level_id][slot]
        result = simulate_solution(level, solution)
        print(f"{level.level_name} (Slot {slot})")
        print("Metrics:")
        for field in dataclasses.fields(Metrics):
            print(field.name, "=", getattr(result.metrics, field.name))
        assert len(result.states) == 12
        print("Simulation:")
        for i in range(2):
            print(
                "\n".join(
                    " ".join(segments)
                    for segments in zip(
                        *(
                            state.visualize().split("\n")
                            for state in result.states[6 * i : 6 * i + 6]
                        )
                    )
                )
            )
        print("Rules:")
        for rule in result.solution.rules:
            if rule.target_type == CellType.IGNORE:
                continue
            print(rule.reaction.name)
            print(rule.visualize())
    else:
        print(USAGE)
        sys.exit(1)


if __name__ == "__main__":
    main()
