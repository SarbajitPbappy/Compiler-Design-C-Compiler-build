from __future__ import annotations

import os
import signal
import subprocess
import time
from dataclasses import dataclass
from typing import List, Optional

try:
    import resource  # POSIX only
except Exception:  # pragma: no cover
    resource = None  # type: ignore


@dataclass
class RunLimits:
    cpu_time_seconds: int = 2
    wall_time_seconds: int = 3
    memory_megabytes: int = 256
    file_size_megabytes: int = 64


@dataclass
class RunOutcome:
    stdout: str
    stderr: str
    exit_code: int
    duration_ms: int
    was_killed_by_timeout: bool


def _set_resource_limits(limits: RunLimits) -> None:
    if resource is None:
        return
    # CPU time limit (seconds)
    resource.setrlimit(resource.RLIMIT_CPU, (limits.cpu_time_seconds, limits.cpu_time_seconds))
    # Address space (approx memory) in bytes
    mem_bytes = limits.memory_megabytes * 1024 * 1024
    resource.setrlimit(resource.RLIMIT_AS, (mem_bytes, mem_bytes))
    # Max file size created by process
    fsize_bytes = limits.file_size_megabytes * 1024 * 1024
    resource.setrlimit(resource.RLIMIT_FSIZE, (fsize_bytes, fsize_bytes))
    # Prevent forking too much
    resource.setrlimit(resource.RLIMIT_NPROC, (256, 256))
    # Create new session for easier kill (POSIX only)
    try:
        os.setsid()
    except Exception:
        pass


def run_command(
    argv: List[str],
    input_data: Optional[str] = None,
    working_directory: Optional[str] = None,
    env: Optional[dict[str, str]] = None,
    limits: Optional[RunLimits] = None,
) -> RunOutcome:
    if limits is None:
        limits = RunLimits()

    start = time.monotonic()
    was_killed_by_timeout = False

    # Start with current PATH for portability; normalize LANG on POSIX
    safe_env = dict(os.environ)
    if os.name == "posix":
        safe_env.update({
            "LANG": "C",
            "LC_ALL": "C",
        })
    if env:
        safe_env.update(env)

    preexec = (lambda: _set_resource_limits(limits)) if (resource is not None and os.name == "posix") else None

    try:
        proc = subprocess.Popen(
            argv,
            stdin=subprocess.PIPE if input_data is not None else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=working_directory,
            text=True,
            preexec_fn=preexec,
            env=safe_env,
        )
        try:
            stdout, stderr = proc.communicate(
                input=input_data, timeout=limits.wall_time_seconds
            )
        except subprocess.TimeoutExpired:
            was_killed_by_timeout = True
            # Kill the process (and group if POSIX)
            try:
                if os.name == "posix":
                    os.killpg(proc.pid, signal.SIGKILL)
                else:
                    proc.kill()
            except Exception:
                pass
            stdout, stderr = proc.communicate()
    finally:
        end = time.monotonic()

    exit_code = proc.returncode if 'proc' in locals() and proc.returncode is not None else -1

    return RunOutcome(
        stdout=stdout or "",
        stderr=stderr or "",
        exit_code=exit_code,
        duration_ms=int((end - start) * 1000),
        was_killed_by_timeout=was_killed_by_timeout,
    )
