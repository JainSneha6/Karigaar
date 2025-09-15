"""
Robust helpers for ffmpeg/ffprobe usage using imageio-ffmpeg.

Behavior:
- Uses imageio-ffmpeg's get_ffmpeg_exe() to obtain a bundled ffmpeg binary.
- Attempts to locate ffprobe in the same directory as ffmpeg, via PATH,
  or via IMAGEIO_FFPROBE_EXE if set.
- Provides clear FileNotFoundError messages with actionable guidance.
- Validates absolute executable paths before running.
- Ensures subprocesses use a writable TMPDIR (defaults to /tmp).
- Small helpers: get_tmp_dir(), make_tmp_file(), make_tmp_dir(), secs().
"""
from pathlib import Path
import shutil
import shlex
import subprocess
import tempfile
import os
import re
from typing import List, Union, Optional, Dict

# imageio-ffmpeg provides get_ffmpeg_exe()
import imageio_ffmpeg


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
    tools that expect to create/write a file path).
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
    """
    Return a path to the ffmpeg/ffprobe executable.

    Strategy:
      - If IMAGEIO_FFMPEG_EXE / IMAGEIO_FFPROBE_EXE env var set and points to executable, use it.
      - For ffmpeg: use imageio-ffmpeg.get_ffmpeg_exe()
      - For ffprobe: try same directory as ffmpeg, then shutil.which('ffprobe'), then raise.

    Raises FileNotFoundError with actionable guidance if not found.
    """
    if name not in ("ffmpeg", "ffprobe"):
        raise FileNotFoundError(f"Unknown executable requested: {name}")

    # explicit environment overrides
    if name == "ffmpeg":
        env_exe = os.environ.get("IMAGEIO_FFMPEG_EXE")
        if env_exe:
            p = Path(env_exe)
            if p.exists() and os.access(p, os.X_OK):
                return str(p)
            raise FileNotFoundError(f"IMAGEIO_FFMPEG_EXE is set but not executable: {env_exe}")

        # Use imageio-ffmpeg's bundled ffmpeg (preferred on serverless)
        try:
            ff = imageio_ffmpeg.get_ffmpeg_exe()
        except Exception as e:
            raise FileNotFoundError(
                "Could not locate ffmpeg via imageio-ffmpeg. Install imageio-ffmpeg "
                "(`pip install imageio-ffmpeg`) or set IMAGEIO_FFMPEG_EXE to a valid ffmpeg binary."
            ) from e

        if not Path(ff).exists() or not os.access(ff, os.X_OK):
            raise FileNotFoundError(f"ffmpeg executable not found or not executable: {ff}")

        return str(ff)

    # name == "ffprobe"
    env_exe = os.environ.get("IMAGEIO_FFPROBE_EXE")
    if env_exe:
        p = Path(env_exe)
        if p.exists() and os.access(p, os.X_OK):
            return str(p)
        raise FileNotFoundError(f"IMAGEIO_FFPROBE_EXE is set but not executable: {env_exe}")

    # Try to find ffprobe next to the ffmpeg binary (common in bundled distributions)
    try:
        ffexe = imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        ffexe = None

    if ffexe:
        candidate = Path(ffexe).resolve().parent / "ffprobe"
        if candidate.exists() and os.access(candidate, os.X_OK):
            return str(candidate)

    # Fall back to PATH
    path_exec = shutil.which("ffprobe")
    if path_exec:
        return path_exec

    # Not found — provide actionable guidance
    raise FileNotFoundError(
        "ffprobe executable not found. Try one of:\n"
        " - Install imageio-ffmpeg (pip install imageio-ffmpeg) which often bundles ffmpeg; "
        "ffprobe may be included alongside it.\n"
        " - Install ffmpeg/ffprobe on the system so ffprobe is on PATH (see https://ffmpeg.org/download.html).\n"
        " - Or set IMAGEIO_FFPROBE_EXE to the full path of a ffprobe binary."
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
    Validates that the executable exists before running to give a clearer error.

    `env_extra` can be used to pass additional environment variables to the subprocess.
    """
    if not cmd:
        raise ValueError("Empty command provided to run_cmd()")

    exe = cmd[0]

    # If exe is an absolute path, ensure it exists and is executable
    exe_path = Path(exe)
    if exe_path.is_absolute():
        if not (exe_path.exists() and os.access(str(exe_path), os.X_OK)):
            raise FileNotFoundError(f"Executable '{exe}' not found or not executable.")
    else:
        # If it's not absolute, ensure it's on PATH
        if shutil.which(exe) is None:
            raise FileNotFoundError(
                f"Executable '{exe}' not found in PATH. Install it or provide a full path.\n"
                "If this is ffmpeg/ffprobe, consider installing 'imageio-ffmpeg' or setting "
                "IMAGEIO_FFMPEG_EXE / IMAGEIO_FFPROBE_EXE environment variables."
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
        # In case ffprobe path got removed between the which/check and call
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
