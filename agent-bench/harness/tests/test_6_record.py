"""6. Same record: an adapter turns what its command line prints into one
schema of events, and results and reports read only that."""

import io
import json
import unittest

from support import HARNESS, Sandbox

import adapters
from core import events, report

# What `claude -p --output-format stream-json --verbose` prints, shortened.
CLAUDE = [
    {"type": "system", "subtype": "init", "model": "claude-opus-5-5", "claude_code_version": "2.1.322",
     "tools": ["Bash", "Read", "Grep", "Glob", "Edit", "Write"], "mcp_servers": []},
    {"type": "assistant", "message": {"content": [
        {"type": "thinking", "thinking": "hm"}, {"type": "text", "text": "I will look."},
        {"type": "tool_use", "id": "t1", "name": "Bash", "input": {"command": "ls"}}]}},
    {"type": "user", "message": {"content": [
        {"type": "tool_result", "tool_use_id": "t1", "content": [{"type": "text", "text": "job.py"}]}]}},
    {"type": "rate_limit_event", "rate_limit_info": {}},
    {"type": "assistant", "message": {"content": [
        {"type": "tool_use", "id": "t2", "name": "Write", "input": {"file_path": "answers.json", "content": "{}"}}]}},
    {"type": "user", "message": {"content": [
        {"type": "tool_result", "tool_use_id": "t2", "content": "no", "is_error": True}]}},
    {"type": "result", "subtype": "success", "is_error": False, "result": "Done.", "num_turns": 3,
     "total_cost_usd": 0.25, "usage": {"input_tokens": 12, "output_tokens": 34,
                                       "cache_read_input_tokens": 56, "cache_creation_input_tokens": 78}},
]


def through(lines, wall=12.34, timed_out=False):
    adapter = adapters.load("claude-code")
    out, parser = io.StringIO(), adapter.parser()
    writer = events.Writer(out, lambda: 1.0)
    for line in lines:
        for event in parser.feed(line if isinstance(line, str) else json.dumps(line)):
            writer.add(event)
    writer.close(wall, timed_out)
    return [json.loads(line) for line in out.getvalue().splitlines()], adapter


class ClaudeCode(unittest.TestCase):
    def test_the_stream_becomes_the_common_events(self):
        stream, adapter = through(["not json", *CLAUDE])
        self.assertEqual(events.stream_problems(stream), [])
        self.assertEqual([e["type"] for e in stream], ["start", "assistant_text", "tool_call", "tool_result",
                                                      "tool_call", "tool_result", "final", "usage"])
        self.assertEqual(stream[0]["tools"], list(adapter.tools))
        self.assertEqual((stream[2]["tool"], stream[2]["kind"], stream[2]["input"]), ("Bash", "shell", {"command": "ls"}))
        self.assertEqual((stream[3]["id"], stream[3]["output"], stream[3]["is_error"]), ("t1", "job.py", False))
        self.assertEqual((stream[4]["kind"], stream[5]["is_error"]), ("file", True))
        self.assertEqual(stream[6], {"v": 1, "seq": 6, "t": 1.0, "type": "final", "text": "Done.",
                                     "is_error": False, "reason": "done"})
        self.assertEqual(stream[7], {"v": 1, "seq": 7, "t": 1.0, "type": "usage", "input_tokens": 12,
                                     "output_tokens": 34, "cache_read_tokens": 56, "cache_write_tokens": 78,
                                     "cost_usd": 0.25, "turns": 3, "wall_seconds": 12.3})

    def test_the_summary_of_a_result_comes_from_the_events(self):
        stream, adapter = through(CLAUDE)
        facts = events.summary(stream, adapter.tools)
        self.assertEqual(facts["tool_calls"], 2)
        self.assertEqual(facts["tools"], {"Bash": 1, "Write": 1})
        self.assertEqual(facts["tokens"], {"input": 12, "output": 34, "cache_read": 56, "cache_write": 78})
        self.assertEqual((facts["cost_usd"], facts["turns"], facts["wall_seconds"]), (0.25, 3, 12.3))
        self.assertEqual((facts["final"], facts["error"], facts["violations"]), ("done", None, []))

    def test_a_run_out_of_time_ends_with_final_and_usage_too(self):
        stream, adapter = through(CLAUDE[:3], wall=900.0, timed_out=True)
        self.assertEqual(events.stream_problems(stream), [])
        facts = events.summary(stream, adapter.tools)
        self.assertEqual((facts["final"], facts["timed_out"], facts["tokens"], facts["cost_usd"]),
                         ("time_limit", True, None, None))
        stream, _ = through([], wall=1.0)
        self.assertEqual([e["type"] for e in stream], ["final", "usage"])
        self.assertEqual(stream[0]["reason"], "no_result")

    def test_tools_and_servers_outside_the_plan_are_violations(self):
        lines = json.loads(json.dumps(CLAUDE))
        lines[0]["tools"].append("WebSearch")
        lines[0]["mcp_servers"] = [{"name": "github", "status": "connected"}]
        lines[4]["message"]["content"][0]["name"] = "WebFetch"
        stream, adapter = through(lines)
        self.assertEqual(events.summary(stream, adapter.tools)["violations"],
                         ["tools beyond shell and files: WebSearch", "extensions connected: github",
                          "called tools beyond shell and files: WebFetch"])


class Schema(unittest.TestCase):
    def test_an_event_outside_the_schema_is_a_problem(self):
        good = {"v": 1, "seq": 0, "t": 0.5, "type": "assistant_text", "text": "x"}
        self.assertEqual(events.problems(good), [])
        for change in ({"type": "thinking"}, {"text": 5}, {"extra": 1}, {"v": 2}, {"t": True}):
            self.assertNotEqual(events.problems({**good, **change}), [], change)
        call = {"v": 1, "seq": 0, "t": 0, "type": "tool_call", "id": "a", "tool": "x", "kind": "web", "input": {}}
        self.assertEqual(events.problems(call), ["tool_call: kind 'web'"])

    def test_the_document_names_every_type_and_field(self):
        document = (HARNESS / "EVENTS.md").read_text()
        for kind, fields in events.FIELDS.items():
            self.assertIn(f"`{kind}`", document)
            for field in fields:
                self.assertIn(f"`{field}`", document, f"{kind}.{field}")


class Report(Sandbox):
    def test_results_and_report_do_not_need_the_command_lines_own_output(self):
        out = self.batch().run()
        for path in (out / "streams").iterdir():
            path.write_text("gone\n")  # the vendor's format is not read again
        text = report.write(out, self.root)
        self.assertIn("| right | 1 | 1.00 |", text)
        self.assertIn("| wrong | 1 | 0.00 |", text)

    def test_a_result_that_differs_from_its_events_fails_the_report(self):
        from core.spec import Refused

        out = self.batch().run()
        lines = self.results(out)
        lines[0]["tool_calls"] = 99
        (out / "results.jsonl").write_text("".join(json.dumps(line) + "\n" for line in lines))
        with self.assertRaises(Refused):
            report.write(out, self.root)

    def test_every_run_has_a_stream_and_events_that_fit_the_schema(self):
        out = self.batch().run()
        for record in self.results(out):
            self.assertTrue((out / record["stream"]).exists())
            self.assertEqual(events.stream_problems(events.read(out / record["events"])), [])
            self.assertEqual(record["tokens"], {"input": 10, "output": 5, "cache_read": None, "cache_write": None})


if __name__ == "__main__":
    unittest.main()
