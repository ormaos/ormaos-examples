"""The container program (podman or docker, whichever is installed) and the
few things the harness asks of it."""

import os
import shutil
import subprocess
from pathlib import Path

HARNESS = Path(__file__).resolve().parents[1]
BASE_TAG = "ormaos-harness-base"
PROXY_PORT = 8080


class RuntimeError_(Exception):
    pass


def find():
    """podman or docker, whichever is installed (HARNESS_RUNTIME chooses
    when both are)."""
    for program in filter(None, [os.environ.get("HARNESS_RUNTIME"), "podman", "docker"]):
        if shutil.which(program):
            return program
    return None


class Runtime:
    def __init__(self, program=None):
        self.program = program or find()
        if not self.program:
            raise RuntimeError_("neither podman nor docker is installed")
        self.podman = Path(self.program).name == "podman"

    def do(self, *args, check=True, **options):
        done = subprocess.run([self.program, *args], capture_output=True, text=True, check=False, **options)
        if check and done.returncode != 0:
            raise RuntimeError_(f"{self.program} {' '.join(args[:3])} ...: {done.stderr.strip() or done.stdout.strip()}")
        return done

    # images

    def image(self, tag):
        """{"id", "layers"} of an image, or None when it is not built."""
        done = self.do("image", "inspect", tag, "--format", "{{.Id}} {{json .RootFS.Layers}}", check=False)
        if done.returncode != 0:
            return None
        import json

        identity, layers = done.stdout.strip().split(" ", 1)
        return {"tag": tag, "id": identity, "layers": json.loads(layers)}

    def build(self, tag, containerfile, context, args=None):
        command = ["build", "-q", "-t", tag, "-f", str(containerfile)]
        for key, value in (args or {}).items():
            command += ["--build-arg", f"{key}={value}"]
        self.do(*command, str(context))
        return self.image(tag)

    def agent_tag(self, adapter):
        return f"ormaos-harness-{adapter.name}:{adapter.cli_version}"

    def images(self, adapter, rebuild=False):
        """The base image and the image of an agent: built when missing."""
        base = None if rebuild else self.image(BASE_TAG)
        base = base or self.build(BASE_TAG, HARNESS / "image" / "Containerfile", HARNESS / "image")
        tag = self.agent_tag(adapter)
        agent = None if rebuild else self.image(tag)
        if agent is None or agent["layers"][:len(base["layers"])] != base["layers"]:
            agent = self.build(tag, adapter.containerfile, adapter.containerfile.parent,
                               {"BASE": BASE_TAG, **adapter.build_args})
        return base, agent

    # the network of a batch: no way out, and the proxy

    def network_up(self, name, allow):
        """A network without a route out, and on it the proxy, which also
        stands on the default network. Returns the proxy's address inside."""
        self.do("network", "create", "--internal", name)
        proxy = f"{name}-proxy"
        command = ["run", "-d", "--name", proxy, "--network", "podman" if self.podman else "bridge",
                   "-v", f"{HARNESS / 'core' / 'proxy.py'}:/proxy.py:ro", BASE_TAG,
                   "python3", "/proxy.py", "--port", str(PROXY_PORT)]
        for host in allow:
            command += ["--allow", f"{host}:443"]
        self.do(*command)
        self.do("network", "connect", name, proxy)
        address = self.do("inspect", proxy, "--format",
                          f'{{{{(index .NetworkSettings.Networks "{name}").IPAddress}}}}').stdout.strip()
        if not address:
            raise RuntimeError_("the proxy has no address on the agents' network")
        return f"http://{address}:{PROXY_PORT}"

    def proxy_log(self, name):
        return self.do("logs", f"{name}-proxy", check=False).stdout

    def network_down(self, name):
        self.do("rm", "-f", f"{name}-proxy", check=False)
        self.do("network", "rm", name, check=False)

    # one container

    def command(self, name, image, network, env, mounts, workdir, argv):
        """The command line that runs ``argv`` in a new container. ``mounts``
        is a list of (host path, path inside, "ro" or "rw")."""
        command = [self.program, "run", "--rm", "--init", "--name", name, "--network", network,
                   "--user", f"{os.getuid()}:{os.getgid()}", "--cap-drop", "ALL",
                   "--security-opt", "no-new-privileges"]
        if self.podman:
            command += ["--userns", "keep-id"]
        for key, value in env.items():
            command += ["-e", f"{key}={value}"]
        for source, inside, mode in mounts:
            command += ["-v", f"{source}:{inside}:{mode}"]
        return command + ["-w", workdir, image, *argv]

    def kill(self, name):
        self.do("kill", name, check=False)


def proxy_env(proxy):
    """The environment that sends a program through the proxy. Programs on
    the machine itself (the jobs' own local servers) are not sent there."""
    env = {}
    for key in ("HTTPS_PROXY", "HTTP_PROXY"):
        env[key] = env[key.lower()] = proxy
    env["NO_PROXY"] = env["no_proxy"] = "localhost,127.0.0.1,::1"
    return env
