"""
Robust helpers for ffmpeg/ffprobe usage using imageio's ffmpeg download.
"""
from pathlib import Path
import shutil
import shlex
import subprocess
import tempfile
import os
import re
from typing import List, Union, Optional, Dict

import imageio.v3 as iio

def get_tmp_dir() -> str:
    tmp = os.environ.get("TMPDIR") or "/tmp"
    try:
        os.makedirs(tmp, exist_ok=True)
    except Exception:
        tmp = tempfile.gettempdir()
    return tmp

def make_tmp_file(suffix: str = "", prefix: str = "ffmpeg_", dir: Optional[str] = None) -> str:
    d = dir or get_tmp_dir()
    fd, tmp_path = tempfile.mkstemp(suffix=suffix, prefix=prefix, dir=d)
    os.close(fd)
    try:
        os.unlink(tmp_path)
    except Exception:
        pass
    return tmp_path

def make_tmp_dir(prefix: str = "ffmpeg_tmp_", dir: Optional[str] = None) -> str:
    d = dir or get_tmp_dir()
    return tempfile.mkdtemp(prefix=prefix, dir=d)

def _find_executable(name: str) -> str:
    """
    Find ffmpeg/ffprobe using imageio's ffmpeg plugin.
    """
    if name not in ("ffmpeg", "ffprobe"):
        raise FileNotFoundError(f"Unknown executable requested: {name}")

    # download binary if missing
    path = iio.plugins.ffmpeg.download()
    if not Path(path).exists():
        raise FileNotFoundError(f"Failed to download {name} via imageio")
    return path

def _prepare_env_for_subprocess(extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    env = os.environ.copy()
    env["TMPDIR"] = get_tmp_dir()
    if extra:
        env.update(extra)
    return env

def run_cmd(cmd: List[str], check: bool = True, env_extra: Optional[Dict[str, str]] = None):
    if not cmd:
        raise ValueError("Empty command provided to run_cmd()")

    exe = cmd[0]
    if shutil.which(exe) is None:
        if Path(exe).is_absolute():
            pass
        else:
            raise FileNotFoundError(
                f"Executable '{exe}' not found in PATH. Install it or provide a full path."
            )

    print("RUN:", " ".join(shlex.quote(x) for x in cmd))
    env = _prepare_env_for_subprocess(env_extra)
    subprocess.run(cmd, check=check, env=env)

def get_duration(path: str) -> float:
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

    out = (res.stdout or "").strip()
    if not out:
        raise RuntimeError(f"ffprobe returned empty output for '{path}'.")

    try:
        return float(out)
    except ValueError as e:
        raise RuntimeError(f"Could not parse duration from ffprobe output: {out!r}") from e

def secs(t: Union[str, int, float]) -> float:
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
