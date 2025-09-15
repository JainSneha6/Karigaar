# ffmpeg_utils.py
"""
Robust helpers for ffmpeg/ffprobe usage.

Improvements:
- Checks that `ffprobe` is available on PATH and raises a clear FileNotFoundError with actionable guidance.
- Validates that the input file exists before calling ffprobe.
- Returns detailed RuntimeError when ffprobe fails, including stderr output.
- Keeps a simple `run_cmd` helper but validates the executable is present before attempting to run.
- Ensures subprocesses use a writable TMPDIR (defaults to /tmp) by providing helper functions:
    - get_tmp_dir()
    - make_tmp_file()
    - make_tmp_dir()
- `secs` helper unchanged except small robustness tweaks.
"""
from pathlib import Path
import shutil
import shlex
import subprocess
import tempfile
import os
import re
from typing import List, Union, Optional, Dict


def get_tmp_dir() -> str:
    """
    Return a writable temporary directory for the environment.
    Priority:
      1) $TMPDIR (if set)
      2) /tmp
    Ensures the directory exists.
    """
    tmp = os.environ.get("TMPDIR") or "/tmp"
    try:
        os.makedirs(tmp, exist_ok=True)
    except Exception:
        # If creation fails, fall back to tempfile.gettempdir()
        tmp = tempfile.gettempdir()
    return tmp


def make_tmp_file(suffix: str = "", prefix: str = "ffmpeg_", dir: Optional[str] = None) -> str:
    """
    Create a temporary file inside the environment's tmp dir and return its path.
    The file descriptor is closed and the file is unlinked (so callers can safely write with
    tools that expect to create/write a file path). This matches the pattern used elsewhere.
    """
    d = dir or get_tmp_dir()
    fd, tmp_path = tempfile.mkstemp(suffix=suffix, prefix=prefix, dir=d)
    os.close(fd)
    # remove the empty file — caller will create/write to this path
    try:
        os.unlink(tmp_path)
    except Exception:
        # If unlink fails, we still return the path (some systems may not allow unlink)
        pass
    return tmp_path


def make_tmp_dir(prefix: str = "ffmpeg_tmp_", dir: Optional[str] = None) -> str:
    """
    Create and return a temporary directory inside the environment's tmp dir.
    """
    d = dir or get_tmp_dir()
    return tempfile.mkdtemp(prefix=prefix, dir=d)


def _find_executable(name: str) -> str:
    # Try FFMPEG_BINARY first (exact path)
    bin_path = os.environ.get("FFMPEG_BINARY")
    if bin_path and Path(bin_path).exists():
        return bin_path

    # Try FFMPEG_BIN_DIR
    bin_dir = ".vercel_build_output/bin"
    if bin_dir:
        candidate = Path(bin_dir) / name
        if candidate.exists() and os.access(candidate, os.X_OK):
            return str(candidate)

    # Fallback to PATH
    path_exec = shutil.which(name)
    if path_exec:
        return path_exec

    raise FileNotFoundError(
        f"'{name}' not found. Tried:\n"
        f" - FFMPEG_BINARY={bin_path!r}\n"
        f" - FFMPEG_BIN_DIR={bin_dir!r}\n"
        f" - PATH lookup (shutil.which)\n\n"
        "Please provide ffmpeg/ffprobe binaries."
    )


def _prepare_env_for_subprocess(extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """
    Prepare an environment dict for subprocess calls that ensures TMPDIR is set
    to a writable temp folder (useful for serverless platforms).
    """
    env = os.environ.copy()
    env["TMPDIR"] = get_tmp_dir()
    if extra:
        env.update(extra)
    return env


def run_cmd(cmd: List[str], check: bool = True, env_extra: Optional[Dict[str, str]] = None):
    """
    Run a command (list form). Prints the command (shell-escaped) and runs subprocess.run().
    Validates that the executable exists on PATH before running to give a clearer error.

    `env_extra` can be used to pass additional environment variables to the subprocess.
    """
    if not cmd:
        raise ValueError("Empty command provided to run_cmd()")

    exe = cmd[0]
    if shutil.which(exe) is None:
        # If exe is already an absolute path, let it fail normally to preserve behavior,
        # otherwise provide a helpful FileNotFoundError.
        if Path(exe).is_absolute():
            pass
        else:
            raise FileNotFoundError(
                f"Executable '{exe}' not found in PATH. Install it or provide a full path.\n"
                "If this is ffmpeg/ffprobe, see: https://ffmpeg.org/download.html"
            )

    print("RUN:", " ".join(shlex.quote(x) for x in cmd))
    env = _prepare_env_for_subprocess(env_extra)
    subprocess.run(cmd, check=check, env=env)


def get_duration(path: str) -> float:
    """
    Uses ffprobe to get the duration (in seconds) of the given media file.
    Raises:
      - FileNotFoundError: if input file does not exist or ffprobe isn't available
      - RuntimeError: if ffprobe returns a non-zero exit code or output can't be parsed
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Input file not found: {path}")

    ffprobe = _find_executable("ffprobe")

    cmd = [
        ffprobe,
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(path)
    ]

    try:
        env = _prepare_env_for_subprocess()
        res = subprocess.run(cmd, capture_output=True, text=True, check=True, env=env)
    except subprocess.CalledProcessError as e:
        stderr = (e.stderr or e.stdout or "").strip()
        raise RuntimeError(f"ffprobe failed for '{path}': {stderr}") from e
    except FileNotFoundError:
        # In case ffprobe path got removed between the which check and call
        raise FileNotFoundError(f"ffprobe executable not found when attempting to run: {ffprobe}")

    out = (res.stdout or "").strip()
    if not out:
        raise RuntimeError(f"ffprobe returned empty output for '{path}'. stdout/stderr: {res.stdout!r} / {res.stderr!r}")

    try:
        return float(out)
    except ValueError as e:
        raise RuntimeError(f"Could not parse duration from ffprobe output: {out!r}") from e


def secs(t: Union[str, int, float]) -> float:
    """
    Convert a time string like 'HH:MM:SS', 'MM:SS', 'SS' or numeric input to seconds (float).
    """
    if isinstance(t, (int, float)):
        return float(t)
    s = str(t).strip()
    if not s:
        raise ValueError("Empty time string passed to secs()")

    # Accept "HH:MM:SS", "MM:SS" or "SS" and also floats
    if ":" in s:
        parts = [float(p) for p in s.split(":")]
        parts = list(reversed(parts))
        total = 0.0
        mul = 1.0
        for p in parts:
            total += p * mul
            mul *= 60.0
        return total
    return float(s)
