# The event schema

Every run leaves `events/<task>-<arm>-<run>.jsonl`: one JSON object per line, the same for every agent. An adapter makes the events from what its command line prints; the runner numbers them, times them and closes the stream. Results, reports and pages read these events. What the command line printed is kept as it was in `streams/`, for people, and is not read by any of them.

Version 1. [`core/events.py`](core/events.py) checks it.

## In every event

| Field | Type | |
|---|---|---|
| `v` | integer | the version of the schema: 1 |
| `seq` | integer | 0, 1, 2, ... in the order the runner got them |
| `t` | number | seconds since the container was started, on the runner's clock, when the runner got the line |
| `type` | string | one of the six below |

## The six types

`start`: what the command line says it started with. Once, first.

| Field | Type | |
|---|---|---|
| `agent` | string | the name of the adapter |
| `cli_version` | string or null | as the command line reports it |
| `model` | string or null | as the command line reports it |
| `tools` | list of strings | every tool it has, by its own names |
| `extensions` | list of strings | MCP servers, plugins or the like that it reports as connected; a run is as planned only when this is empty |

`assistant_text`: text the model wrote for the reader.

| Field | Type | |
|---|---|---|
| `text` | string | |

`tool_call`: the model asked for a tool.

| Field | Type | |
|---|---|---|
| `id` | string or null | joins the call and its result |
| `tool` | string | the command line's own name of the tool |
| `kind` | string | `shell`, `file`, or `other` for a tool the adapter does not list |
| `input` | object | the arguments, as the command line gives them |

`tool_result`: what the tool gave back.

| Field | Type | |
|---|---|---|
| `id` | string or null | the `id` of the call |
| `is_error` | boolean | |
| `output` | string | as text |

`final`: how the run ended. Exactly once, the last but one event.

| Field | Type | |
|---|---|---|
| `text` | string | the last answer of the agent, or what the command line said of its error |
| `is_error` | boolean | |
| `reason` | string | `done`; `error`, the command line or the model reported one; `time_limit`, the runner stopped the container; `no_result`, the command line ended without saying how |

`usage`: the totals of the run. Exactly once, the last event.

| Field | Type | |
|---|---|---|
| `input_tokens` | number or null | as the command line reports them; null when it does not, or did not get to |
| `output_tokens` | number or null | |
| `cache_read_tokens` | number or null | |
| `cache_write_tokens` | number or null | |
| `cost_usd` | number or null | only if the command line reports a cost |
| `turns` | number or null | only if the command line reports them |
| `wall_seconds` | number | from the start of the container to its end, on the runner's clock; never the command line's own figure |

## What is not in it

- The model's reasoning ("thinking"): some command lines print it, some a summary, some nothing.
- Anything else a command line prints: progress, rate-limit notices, its own session ids.
- Tokens per step. Vendors count tokens differently; the totals are each vendor's own count.

A line of a result (`results.jsonl`) takes these from the events and from nowhere else: `wall_seconds`, `timed_out`, `final`, `error`, `tool_calls`, `tools`, `turns`, `tokens`, `cost_usd`, `model`, `cli_version`, and the `violations` that the events show. The report checks that they still agree.
