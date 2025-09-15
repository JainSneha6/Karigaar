# ffmpeg_utils.py
"""
Robust helpers for ffmpeg/ffprobe usage.

Replacements / improvements over the original:
- Checks that `ffprobe` is available on PATH and raises a clear FileNotFoundError with actionable guidance.
- Validates that the input file exists before calling ffprobe.
- Returns detailed RuntimeError when ffprobe fails, including stderr output.
- Keeps a simple `run_cmd` helper but validates the executable is present before attempting to run.
- `secs` helper unchanged except small robustness tweaks.
"""

from pathlib import Path
import shutil
import shlex
import subprocess
from typing import List, Union


def _find_executable(name: str) -> str:
    """
    Return the absolute path to an executable or raise FileNotFoundError with guidance.
    """
    p = shutil.which(name)
    if p:
        return p
    raise FileNotFoundError(
        f"'{name}' not found in PATH. Please install FFmpeg (which provides {name}) and add it to your PATH.\n"
        "On Windows: download a static build from https://ffmpeg.org/download.html and add the `bin` directory to PATH,\n"
        "or use Chocolatey: `choco install ffmpeg -y`.\n"
        "On macOS: `brew install ffmpeg`.\n"
        "After installing, restart your terminal / service so PATH changes take effect."
    )


def run_cmd(cmd: List[str], check: bool = True):
    """
    Run a command (list form). Prints the command (shell-escaped) and runs subprocess.run().
    Validates that the executable exists on PATH before running to give a clearer error.
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
    subprocess.run(cmd, check=check)


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
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
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
