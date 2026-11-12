"""Owned subprocess lifecycle and dashboard process identities on native Windows."""

import ctypes
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
from datetime import datetime


def popen_options():
    if os.name == "nt":
        return {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW}
    return {"start_new_session": True}


def terminate_owned(process):
    """Stop only this Popen child's process tree, never an arbitrary user PID."""
    job = getattr(process, "_native_job", None)
    if job is not None:
        job.terminate()
        return
    if process.poll() is not None:
        return
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        if process.poll() is None:
            try:
                process.kill()
            except (ProcessLookupError, PermissionError):
                pass


class OwnedPopen(subprocess.Popen):
    """Own a Windows job before running the CLI; POSIX keeps its own session."""

    def __init__(self, command, **kwargs):
        self._native_job = None
        kwargs.pop("start_new_session", None)
        kwargs.update(popen_options())
        if os.name == "nt":
            from .windows_job import WindowsJob

            self._native_job = WindowsJob()
            kwargs["creationflags"] |= 4
        try:
            super().__init__(command, **kwargs)
            if self._native_job is not None:
                self._native_job.attach_and_resume(self.pid)
        except BaseException:
            if getattr(self, "pid", None) is not None:
                super().kill()
                super().wait()
            if self._native_job is not None:
                self._native_job.close()
            raise

    def wait(self, timeout=None):
        result = super().wait(timeout=timeout)
        if self._native_job is not None:
            self._native_job.close()
        return result


class OwnedSubprocess:
    """A private proxy assigned only to codex_client, never global subprocess."""

    TimeoutExpired = subprocess.TimeoutExpired
    PIPE = subprocess.PIPE
    Popen = OwnedPopen


def find_codex(cls, executable):
    from .codex_client import CodexCLIError

    explicit = executable or os.environ.get("PROSELEDGER_CODEX_PATH")
    candidates = (
        [str(explicit)]
        if explicit
        else [shutil.which("codex.exe") if os.name == "nt" else shutil.which("codex")]
    )
    with tempfile.TemporaryDirectory(prefix="proseledger-codex-version-") as cwd:
        for candidate in candidates:
            if not candidate:
                continue
            path = Path(shutil.which(candidate) or candidate).expanduser().absolute()
            if os.name == "nt" and path.suffix.lower() != ".exe":
                continue
            if not path.is_file():
                continue
            try:
                check = subprocess.run(
                    [str(path), "--version"],
                    cwd=cwd,
                    env=cls._environment(),
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=5,
                    check=False,
                    **{"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}
                )
            except (OSError, subprocess.TimeoutExpired):
                continue
            if check.returncode == 0 and "codex" in check.stdout.lower():
                return str(path)
    raise CodexCLIError(
        "No working native Codex executable found. Install the official CLI or set PROSELEDGER_CODEX_PATH to its native executable, then run codex login."
    )


def install_codex(module):
    module.subprocess = OwnedSubprocess
    module.CodexCLIModel._find_executable = classmethod(find_codex)
    module.CodexCLIModel._terminate = staticmethod(terminate_owned)
