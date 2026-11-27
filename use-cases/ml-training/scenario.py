"""Record one training run, and compute what happened in it.

    python scenario.py /tmp/ml-training

The folder gets the program, `model.pt` and the recording `r1` of
`python train.py`. Then the same program runs again in another copy, without
Ormaos, under `sys.settrace`; the shape and the number of NaN of every
tensor that entered or left a function are counted there with
`torch.isnan`, and the answers in `questions.json` come from those counts.

Needs, in the Python that runs it: ormaos, and the requirements.txt.
"""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import common  # noqa: E402

FILES = ["README.md", "requirements.txt", "train.py"]
SHOW = ["ormaos", "show", "r1"]


def main():
    args = common.arguments(__doc__)
    common.need("torch")
    common.copy_program(HERE, args.target, FILES)
    common.record(args.target, "python", "train.py")

    found = common.trace(HERE, FILES, "train.py")
    steps = common.calls(found, "train_step")
    with_nan = [
        call
        for call in found["calls"]
        if call.get("result", {}).get("type") == "Tensor" and call["result"]["nan"] > 0
    ]
    nan_losses = [c for c in common.calls(found, "loss_of") if c["result"]["nan"] > 0]
    first_step = next(
        n for n, step in enumerate(steps, 1) if any(c["parent"] == step["id"] for c in with_nan)
    )

    questions = [
        {
            "id": "q1",
            "question": "How many times did train_step run?",
            "answer": len(steps),
            "oracle": "sys.settrace",
        },
        {
            "id": "q2",
            "question": "In how many calls of loss_of was the returned loss NaN?",
            "answer": len(nan_losses),
            "oracle": "sys.settrace return event, torch.isnan",
        },
        {
            "id": "q3",
            "question": "Which function was the first to return a tensor with NaN in it?",
            "answer": with_nan[0]["fn"],
            "oracle": "sys.settrace return events in order, torch.isnan",
        },
        {
            "id": "q4",
            "question": "In which call of train_step, counted from 1, did a tensor with NaN first appear?",
            "answer": first_step,
            "oracle": "sys.settrace return events in order, torch.isnan",
        },
        {
            "id": "q5",
            "question": "How many times did apply_update run?",
            "answer": len(common.calls(found, "apply_update")),
            "oracle": "sys.settrace",
        },
        {
            "id": "q6",
            "question": "What was the shape of the batch tensor passed to standardize?",
            "answer": sorted({tuple(c["args"]["batch"]["shape"]) for c in common.calls(found, "standardize")}),
            "oracle": "sys.settrace call event, Tensor.shape",
        },
        {
            "id": "q7",
            "question": "How many times did save_checkpoint run?",
            "answer": len(common.calls(found, "save_checkpoint")),
            "oracle": "sys.settrace",
        },
    ]
    for item in questions:
        if item["id"] == "q6":
            item["answer"] = [list(shape) for shape in item["answer"]]
    common.finish(args, HERE, "ml-training", ["r1"], questions, SHOW)


if __name__ == "__main__":
    main()
