"""Summarize support tickets with a model API, one line per ticket."""

import json
import urllib.error
import urllib.request
from pathlib import Path

import model_server

HERE = Path(__file__).parent
INSTRUCTION = "Summarize this support ticket in one sentence.\n\n"


def ask(base, model, prompt):
    request = urllib.request.Request(
        f"{base}/v1/models/{model}/generate",
        data=json.dumps({"prompt": prompt}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.load(response)["text"]


def summarize(base, ticket):
    prompt = INSTRUCTION + ticket["text"]
    try:
        return ask(base, "small-1", prompt)
    except urllib.error.HTTPError:
        return ask(base, "large-1", prompt)


def load_tickets(path):
    return json.loads(path.read_text())


def save(summaries, path):
    with open(path, "w") as out:
        json.dump(summaries, out, indent=2)


def main():
    server, base = model_server.start()
    try:
        tickets = load_tickets(HERE / "tickets.json")
        summaries = [{"id": t["id"], "summary": summarize(base, t)} for t in tickets]
    finally:
        server.shutdown()
    save(summaries, HERE / "summaries.json")
    print(f"{len(summaries)} tickets summarized, summaries.json written")


if __name__ == "__main__":
    main()
