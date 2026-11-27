"""Record twenty episodes of the grid world, and compute what happened in them.

    python scenario.py /tmp/rl-env

The folder gets the program and the recording `r1` of `python run.py`, with
the lines of `GridEnv.step` recorded (`--path env.py:GridEnv.step`). Then
the same program runs again in another copy, without Ormaos, under
`sys.settrace`; the answers in `questions.json` come from the calls seen
there and their order.

Needs, in the Python that runs it: ormaos.
"""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import common  # noqa: E402

FILES = ["README.md", "env.py", "run.py"]


def main():
    args = common.arguments(__doc__)
    common.copy_program(HERE, args.target, FILES)
    common.record(args.target, "python", "run.py", options=["--path", "env.py:GridEnv.step"])

    found = common.trace(HERE, FILES, "run.py")
    steps = common.calls(found, "GridEnv.step")
    children = {}
    for call in found["calls"]:
        children.setdefault(call["parent"], []).append(call["fn"])
    reward_first = sum(
        1
        for step in steps
        if children[step["id"]].index("GridEnv._reward") < children[step["id"]].index("GridEnv._move")
    )
    per_episode = [
        sum(1 for step in steps if step["parent"] == episode["id"])
        for episode in common.calls(found, "run_episode")
    ]

    questions = [
        {
            "id": "q1",
            "question": "How many times did GridEnv.reset run, and how many times GridEnv.step?",
            "answer": {
                "reset": len(common.calls(found, "GridEnv.reset")),
                "step": len(steps),
            },
            "oracle": "sys.settrace",
        },
        {
            "id": "q2",
            "question": "In how many calls of GridEnv.step did _reward run before _move, and in how many after?",
            "answer": {"before": reward_first, "after": len(steps) - reward_first},
            "oracle": "sys.settrace, the order of the calls made from each step",
        },
        {
            "id": "q3",
            "question": "How many episodes ended in ended_at_goal and how many in ended_at_limit?",
            "answer": {
                "ended_at_goal": len(common.calls(found, "ended_at_goal")),
                "ended_at_limit": len(common.calls(found, "ended_at_limit")),
            },
            "oracle": "sys.settrace",
        },
        {
            "id": "q4",
            "question": "How many times did GridEnv._arrival_bonus run?",
            "answer": len(common.calls(found, "GridEnv._arrival_bonus")),
            "oracle": "sys.settrace",
        },
        {
            "id": "q5",
            "question": "How many times did GridEnv._bump run?",
            "answer": len(common.calls(found, "GridEnv._bump")),
            "oracle": "sys.settrace",
        },
        {
            "id": "q6",
            "question": "How many calls of GridEnv.step did the shortest and the longest episode make?",
            "answer": {"shortest": min(per_episode), "longest": max(per_episode)},
            "oracle": "sys.settrace, the calls made from each run_episode",
        },
    ]
    show = ["ormaos", "path", common.address(args.target, "r1", "step")]
    common.finish(args, HERE, "rl-env", ["r1"], questions, show)


if __name__ == "__main__":
    main()
