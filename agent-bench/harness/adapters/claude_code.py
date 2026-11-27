"""The adapter of Claude Code (the ``claude`` command line)."""

import json
import time

from adapters import Adapter


class ClaudeCode(Adapter):
    name = "claude-code"
    cli_version = "2.1.322"
    build_args = {
        "CLI_VERSION": cli_version,
        # sha256 of the linux-x64 program of that version
        "CLI_SHA256": "bfb3703ad5380242328459bc62ada4bde8ae7ba57c6e1eeadb9c00e08874c478",
    }
    # The model: api.anthropic.com, and no other host. Logging in (getting a
    # new access token with the refresh token) is done at
    # platform.claude.com/v1/oauth/token; a run does not need it, because its
    # copy of the credential has no refresh token (see home_files), so that
    # host is not on the list. Found by running the command line behind the
    # proxy and reading the proxy's log: with the environment below it asks
    # for api.anthropic.com only.
    hosts = ("api.anthropic.com",)
    probe = "https://api.anthropic.com/"
    tools = {"Bash": "shell", "Read": "file", "Grep": "file", "Glob": "file", "Edit": "file", "Write": "file"}
    efforts = ("low", "medium", "high", "xhigh", "max")
    env = {
        "DISABLE_AUTOUPDATER": "1",
        "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",  # no telemetry, no error reports, no update check
        "CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1",
    }
    CREDENTIAL = ".claude/.credentials.json"
    # Of the login, what the command line needs to call the model. Not the
    # refresh token: with it an agent could get new tokens after the run,
    # and a refresh inside a run would end the login on this machine.
    KEPT = ("accessToken", "expiresAt", "scopes", "subscriptionType", "rateLimitTier")

    def _login(self, source_home):
        document = json.loads((source_home / self.CREDENTIAL).read_text(encoding="utf-8"))
        return document["claudeAiOauth"]

    def home_files(self, source_home):
        login = self._login(source_home)
        kept = {key: login[key] for key in self.KEPT if key in login}
        return {self.CREDENTIAL: json.dumps({"claudeAiOauth": kept}).encode()}

    def secrets(self, source_home):
        login = self._login(source_home)
        return [login[key] for key in ("accessToken", "refreshToken") if login.get(key)]

    def credential_seconds(self, source_home):
        expires = self._login(source_home).get("expiresAt")
        return None if expires is None else expires / 1000 - time.time()

    def argv(self, text, model, effort):
        names = ",".join(self.tools)
        argv = ["claude", "-p", "--model", model]
        if effort != "default":
            argv += ["--effort", effort]
        return argv + [
            "--safe-mode", "--strict-mcp-config", "--tools", names, "--allowedTools", names,
            "--no-session-persistence", "--output-format", "stream-json", "--verbose", text,
        ]

    def parser(self):
        return Parser(self)


def text_of(content):
    """The text of a tool result: a string, or a list of blocks."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(block.get("text", "") if isinstance(block, dict) and block.get("type") == "text"
                         else json.dumps(block) for block in content)
    return "" if content is None else json.dumps(content)


class Parser:
    """``claude -p --output-format stream-json --verbose``, line by line."""

    def __init__(self, adapter):
        self.adapter = adapter

    def feed(self, line):
        try:
            raw = json.loads(line)
        except ValueError:
            return []
        if not isinstance(raw, dict):
            return []
        kind = raw.get("type")
        if kind == "system" and raw.get("subtype") == "init":
            return [{
                "type": "start", "agent": self.adapter.name,
                "cli_version": raw.get("claude_code_version"), "model": raw.get("model"),
                "tools": list(raw.get("tools") or []),
                "extensions": [server.get("name", "?") if isinstance(server, dict) else str(server)
                               for server in raw.get("mcp_servers") or []],
            }]
        if kind == "assistant":
            events = []
            for block in (raw.get("message") or {}).get("content") or []:
                if block.get("type") == "text" and block.get("text"):
                    events.append({"type": "assistant_text", "text": block["text"]})
                elif block.get("type") == "tool_use":
                    tool = block.get("name", "?")
                    events.append({"type": "tool_call", "id": block.get("id"), "tool": tool,
                                   "kind": self.adapter.tools.get(tool, "other"), "input": block.get("input") or {}})
            return events
        if kind == "user":
            content = (raw.get("message") or {}).get("content")
            return [{"type": "tool_result", "id": block.get("tool_use_id"),
                     "is_error": bool(block.get("is_error")), "output": text_of(block.get("content"))}
                    for block in (content if isinstance(content, list) else [])
                    if isinstance(block, dict) and block.get("type") == "tool_result"]
        if kind == "result":
            usage = raw.get("usage") or {}
            failed = bool(raw.get("is_error"))
            return [
                {"type": "final", "text": raw.get("result") if isinstance(raw.get("result"), str) else "",
                 "is_error": failed, "reason": "error" if failed else "done"},
                {"type": "usage",
                 "input_tokens": usage.get("input_tokens"), "output_tokens": usage.get("output_tokens"),
                 "cache_read_tokens": usage.get("cache_read_input_tokens"),
                 "cache_write_tokens": usage.get("cache_creation_input_tokens"),
                 "cost_usd": raw.get("total_cost_usd"), "turns": raw.get("num_turns")},
            ]
        return []


ADAPTER = ClaudeCode()
