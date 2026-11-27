# agent-bench/knows2

The run of 2026-11-27: N = 108 runs (9 tasks x 4 arms x 3 runs), model claude-opus-5-5. Mean score, with its 95% bootstrap interval: none 0.71 (0.59 to 0.83), raw 0.87 (0.79 to 0.95), ormaos 0.93 (0.88 to 0.97), ormaos-values 0.95 (0.90 to 0.99). Of the 213 answers of each arm, right, null and wrong: none 153, 60, 0; raw 186, 27, 0; ormaos 198, 14, 1; ormaos-values 202, 11, 0. The report, with its limits: [`results/20261127-165801/report.md`](results/20261127-165801/report.md).

The benchmark of [`../knows`](../knows), with questions written by someone who was not told what Ormaos records: does an agent know what happened in an execution, with nothing but the folder it left, with a raw trace of it, with an Ormaos recording of it, or with an Ormaos recording that also has values?

Ormaos records and shows what happened inside your Python execution — the runtime context for your agent and for you.

## The tasks

The nine executions of `knows`, unchanged: the seven programs of [`../../use-cases`](../../use-cases) and the jobs [`order-sync`](../../order-sync) and [`freight-quote`](../../freight-quote) on the night that [`../bugs`](../bugs) plays. The folder an agent gets, and the input taken out of it, are as in `knows`.

## The questions

For each task, `claude -p --model claude-opus-5-5` wrote eight questions ([`writer.py`](writer.py)), in bubblewrap, with `--strict-mcp-config`, in a folder that held only:

- the source files of the program (`.py`, `.ipynb`), and its README;
- what the execution printed: `stdout.txt` and `stderr.txt`.

No input file, no file the execution wrote, no `.venv`, no `.ormaos`, no trace. Nothing in the folder or in the prompt names Ormaos or says that the execution was recorded or traced. Three READMEs and the notebook do speak of Ormaos; for the writer those words were taken out (`without_mentions` in `writer.py`): the section "Recording a run with Ormaos" of the two jobs' READMEs, one sentence and one `pip install` line of the notebook's README, and in the notebook's cells `import ormaos` and the `with ormaos.record():` lines (their blocks are kept, not indented). The agents get the programs as they are.

The prompt, the same for every task after its first sentence (what ran) and its second (what the folder holds):

> Write 8 factual questions about what happened inside this execution that the output alone does not answer, each with one unambiguous answer and its expected format. Write them to questions.json in this folder: a JSON list of 8 objects, each with the keys "id" ("q1" to "q8"), "question" and "format".

[`writer/<task>/`](writer) has, as they were: `folder/` (what the writer was given), `prompt.txt`, `transcript.jsonl` (everything the command line printed) and `questions.json` (the file the writer left). Each writer ran once; no question was edited, reworded or replaced.

An agent gets each question with the writer's words and the writer's format.

## The oracle, and the one rule for dropping a question

The answers come from one more execution of the same program, independent of the arms, under `sys.settrace`: the tracer of [`../../use-cases/common.py`](../../use-cases/common.py) with its wrappers around `open` and `sqlite3.connect`, extended in [`tracer.py`](tracer.py) with what these questions need (values of arguments, results and local variables, the lines each call ran, the messages of exceptions). [`oracle.py`](oracle.py) computes every answer from that trace and from the files that execution left. It never reads an Ormaos recording or a VizTracer trace.

**A question is dropped only when the oracle cannot give one unambiguous answer to it.** Not because an arm cannot answer it, not because it is hard, not because of what any agent answered. This rule, the oracle and the rule of every question were written before any agent ran. The dropped questions and their reasons are in [`dropped.json`](dropped.json), written by `build.py`, and are listed in every report.

Of the 72 questions, 1 is dropped:

- `ai-app`, q1, "On which TCP port on 127.0.0.1 did the model_server stand-in listen during this run?": the server listens on a free port the system picks, so the oracle's execution and the execution of each arm got different ports.

## The arms

All four arms have the same task text as in `knows`. Three arms add one thing to the folder and one sentence to the text:

| Arm | Added to the folder | Added to the text |
|---|---|---|
| `none` | nothing | nothing |
| `raw` | `result.json`: a [VizTracer](https://github.com/gaogaotiantian/viztracer) trace of the execution, default settings | that the file is there and how to read it |
| `ormaos` | `.ormaos/`: the recording of `ormaos run`, default settings, and the `ormaos` command line in `.venv/` | that the recording is there, and to run `.venv/bin/ormaos guide` first |
| `ormaos-values` | `.ormaos/`: the recording of `ormaos run --values`, and the same command line | the sentence of `ormaos`, with "values included" |

The execution is played once per arm, and once more for the oracle, in separate copies mounted at the same path, `/srv/<task>`. `build.py` stops if the copies do not leave the same files, or if `ormaos show` does not say of the `ormaos-values` recording, and only of it, that values were recorded.

The cells of the notebook record themselves with `ormaos.record()`. In `ormaos-values` a cell that is not of the notebook and gets no execution count runs first and makes that call record values ([`session.py`](session.py)); the notebook is the same file in every arm.

## Grading

As in `knows`: `answers.json` is one JSON object, an answer is right or wrong as a whole, and the score of a run is the share of the task's kept questions that are right. The rules are those of [`../knows/grade.py`](../knows/grade.py) and three more for the writers' formats ([`rules.py`](rules.py)): a word out of a few, without regard to capitals; a number rounded to the decimals the format names; several values in one string with commas between them ("7, no"), each by its own rule. [`rules.json`](rules.json) has the rule of every question.

## Running it

Needs what `knows` needs. `knows` does not have to be built.

```bash
python3 build.py                              # the folders of every task and arm, in .build/
python3 run.py --runs 3 --replacements 0      # 9 tasks x 4 arms x 3 runs
```

The runner and the report are those of [`../knows/run.py`](../knows/run.py): the first attempt of every slot counts, nothing is run again, nothing is left out. `--replacements` takes only 0. The report adds the answers that were right, null and wrong, every wrong one, the cost, the dropped questions and the limits below. Other options as in `knows`; `python3 run.py --grade <task> <answers.json>` grades one file.

The questions are written once: `writer.py` refuses a task that already has a `questions.json`.

## Limits

- The questions were written by a model from the source, the README and the printed output, one writer per task, one attempt. The programs and the executions are still those the makers of Ormaos wrote for `knows`.
- The agents and the question writer are the same model.
- The oracle and the rule of each question were written by the makers of Ormaos, after reading the questions and before any agent ran. Where a question can be read in two ways, the oracle answers one of them.
- The writer's folder had no input file, so some questions ask for what the removed input held. The writer of `rl-env` ran the program in its folder before writing.
- `notebook`: values are recorded through `ormaos.record(values=True)`, not `ormaos run --values`; the printed output given to the writer is that of the process that ran the kernel, not of the cells.
- Values in a recording are cut at 200 characters, and likely secrets are written as `***`.
- Four of the nine programs read no input that can be taken away, so an agent can run them again; the report says how many runs did.
- One model, one prompt per arm, one tracer with its default settings.
- The dates in the data of the two jobs are relative to the day `build.py` ran: build on the day of the run.
