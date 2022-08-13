import sys

from models import *
from savefile import *
from levels import *
from simulator import *


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <save_file_path> (- for stdin)")
        return
    fname = sys.argv[1]

    with sys.stdin if fname == "-" else open(fname) as f:
        solutions = parse_save_file(f)

    for level in LEVELS:
        assert level.target_state == State.from_visualize(
            level.target_state.visualize()
        )
        for slot, solution in solutions[level.level_id].items():
            print(f"Testing Level {level.level_name} (Slot {slot})")
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


if __name__ == "__main__":
    main()
