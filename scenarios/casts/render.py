"""Print the stream of `claude -p --output-format stream-json` as it arrives.

One block per step: what the agent says, each tool call, and the first lines
of what the tool returned (the number of lines left out is printed). Nothing
is reordered. The stream itself is kept whole by agent.sh.
"""

import json
import shutil
import sys
import textwrap

SHOWN = 12
BOLD, DIM, CYAN, RESET = "\033[1m", "\033[2m", "\033[36m", "\033[0m"


def wrapped(text, indent=""):
    width = shutil.get_terminal_size((100, 30)).columns - 1
    lines = []
    for line in text.splitlines() or [""]:
        lines.extend(
            textwrap.wrap(
                line,
                width,
                initial_indent=indent,
                subsequent_indent=indent,
                replace_whitespace=False,
                drop_whitespace=False,
            )
            or [indent]
        )
    return lines


def call_text(name, given):
    if name == "Bash":
        return given.get("command", "")
    if name == "Read":
        return given.get("file_path", "")
    return " ".join(f"{key}={value}" for key, value in given.items())


def result_text(content):
    if isinstance(content, list):
        return "\n".join(
            part.get("text", "") for part in content if isinstance(part, dict)
        )
    return str(content)


def main():
    calls = 0
    for raw in sys.stdin:
        try:
            event = json.loads(raw)
        except ValueError:
            print(raw.rstrip())
            continue
        kind = event.get("type")
        if kind == "assistant":
            for block in event["message"].get("content", []):
                if block.get("type") == "text" and block["text"].strip():
                    print("\n".join(wrapped(block["text"].strip())), end="\n\n")
                elif block.get("type") == "tool_use":
                    calls += 1
                    text = call_text(block["name"], block.get("input", {}))
                    lines = wrapped(text, "    ")
                    lines[0] = (
                        f"{CYAN}{BOLD}> {block['name']}{RESET} {lines[0].strip()}"
                    )
                    print("\n".join(lines))
        elif kind == "user":
            content = event["message"].get("content", [])
            for block in content if isinstance(content, list) else []:
                if block.get("type") != "tool_result":
                    continue
                lines = wrapped(result_text(block.get("content", "")), "  ")
                for line in lines[:SHOWN]:
                    print(f"{DIM}{line}{RESET}")
                if len(lines) > SHOWN:
                    print(f"{DIM}  ... {len(lines) - SHOWN} more lines{RESET}")
                print()
        elif kind == "result":
            seconds = round(event.get("duration_ms", 0) / 1000)
            print(f"{DIM}-- end of the run: {calls} tool calls, {seconds} s --{RESET}")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
