import os
import subprocess
import tempfile
import json
import re
import urllib.request
import urllib.parse
from typing import List, Dict, Any, Optional


from .ffmpeg_utils import run_cmd, get_duration
from .sticker_helpers import ensure_dirs_exist

JAMENDO_CLIENT_ID = "f24ed52c"
DEFAULT_MUSIC_DIRS = ["./music"]
for md in DEFAULT_MUSIC_DIRS:
    try:
        os.makedirs(md, exist_ok=True)
    except Exception:
        pass


def download_url_to_temp_audio(url: str) -> Optional[str]:
    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return None
        ext = os.path.splitext(parsed.path)[1] or ".mp3"
        fd, tmp = tempfile.mkstemp(suffix=ext)
        os.close(fd)
        print(f"Downloading audio from {url} -> {tmp}")
        urllib.request.urlretrieve(url, tmp)
        if os.path.getsize(tmp) > 0:
            return tmp
        else:
            os.remove(tmp)
            return None
    except Exception as e:
        print("download_url_to_temp_audio failed:", e)
        return None


def find_local_music_by_query(query: str, search_dirs: Optional[List[str]] = None) -> Optional[str]:
    if search_dirs is None:
        search_dirs = DEFAULT_MUSIC_DIRS
    ensure_dirs_exist(search_dirs)
    tokens = re.findall(r"[a-z0-9]+", (query or "").lower())
    if not tokens:
        return None
    joined = "".join(tokens)
    for d in search_dirs:
        if not os.path.isdir(d):
            continue
        for fname in os.listdir(d):
            full = os.path.join(d, fname)
            if not os.path.isfile(full):
                continue
            lf = fname.lower()
            if not lf.endswith((".mp3", ".m4a", ".wav", ".aac", ".ogg")):
                continue
            base = lf.rsplit(".", 1)[0]
            if all(token in base for token in tokens):
                return full
            compact = re.sub(r"[^a-z0-9]", "", base)
            if joined and joined in compact:
                return full
    return None


def search_and_fetch_music(edit: Dict[str, Any]) -> Optional[str]:
    if edit.get("file"):
        if os.path.isfile(edit["file"]):
            return os.path.abspath(edit["file"])
    if edit.get("url"):
        maybe = download_url_to_temp_audio(edit["url"])
        if maybe:
            return maybe
    if edit.get("query"):
        q = edit["query"]
        local = find_local_music_by_query(q)
        if local:
            return local
        # Jamendo attempt
        if JAMENDO_CLIENT_ID:
            try:
                qenc = urllib.parse.quote(q)
                url = f"https://api.jamendo.com/v3.0/tracks/?client_id={JAMENDO_CLIENT_ID}&format=json&limit=1&audioformat=mp32&search={qenc}"
                res = urllib.request.urlopen(url, timeout=15)
                data = json.loads(res.read().decode('utf-8'))
                if 'results' in data and data['results']:
                    track = data['results'][0]
                    audio_url = track.get('audio') or next((v for v in track.values() if isinstance(v, str) and v.startswith('http')), None)
                    if audio_url:
                        return download_url_to_temp_audio(audio_url)
            except Exception:
                pass
    return None


def prepare_music_for_duration(music_path: str, duration: float, volume: float = 0.4, loop: bool = True) -> Optional[str]:
    if not os.path.isfile(music_path):
        print("prepare_music_for_duration: music_path not found:", music_path)
        return None

    def _try_encode(out_path: str, codec_args: List[str]) -> bool:
        cmd = ["ffmpeg", "-y"]
        if loop:
            cmd += ["-stream_loop", "-1"]
        cmd += ["-vn", "-i", music_path, "-t", f"{duration:.3f}", "-af", f"volume={volume:.6f}"]
        cmd += codec_args + [out_path]
        try:
            run_cmd(cmd)
            if os.path.isfile(out_path) and os.path.getsize(out_path) > 1000:
                return True
            return False
        except Exception as e:
            print("prepare_music_for_duration: encoding attempt failed:", e)
            try:
                if os.path.exists(out_path):
                    os.remove(out_path)
            except Exception:
                pass
            return False

    fd, out_m4a = tempfile.mkstemp(suffix=".m4a")
    os.close(fd)
    if _try_encode(out_m4a, ["-c:a", "aac", "-b:a", "192k"]):
        return out_m4a

    try:
        if os.path.exists(out_m4a):
            os.remove(out_m4a)
    except Exception:
        pass

    fd2, out_mp3 = tempfile.mkstemp(suffix=".mp3")
    os.close(fd2)
    if _try_encode(out_mp3, ["-c:a", "libmp3lame", "-b:a", "192k"]):
        return out_mp3

    for p in (out_m4a, out_mp3):
        try:
            if p and os.path.exists(p):
                os.remove(p)
        except Exception:
            pass
    return None


def has_audio(path: str) -> bool:
    cmd = ["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index", "-of", "default=noprint_wrappers=1:nokey=1", path]
    res = subprocess.run(cmd, capture_output=True, text=True)
    return bool(res.stdout.strip())


def mix_background_music(input_video: str, music_source_path: str, out_video: str,
                         music_query: Optional[str] = None, music_duration: Optional[float] = None,
                         music_volume: float = 0.4, loop: bool = True,
                         music_start: float = 0.0, music_end: Optional[float] = None,
                         reduce_original_volume: float = 1.0, music_loop: bool = True,
                         fade: float = 0.0):
    # 1) Get video duration
    try:
        vid_dur = get_duration(input_video)
    except Exception as e:
        raise RuntimeError(f"Unable to get duration of input video: {e}")

    if music_end is None:
        music_end = vid_dur

    music_start = max(0.0, min(music_start, vid_dur))
    music_end = max(0.0, min(music_end, vid_dur))
    if music_end <= music_start:
        raise ValueError("music_end must be greater than music_start after clamping to video duration")

    music_segment_duration = music_end - music_start
    if music_segment_duration <= 0:
        raise ValueError("music segment duration <= 0")

    # 2) resolve music_source_path (if URL, download)
    music_file = None
    parsed = urllib.parse.urlparse(music_source_path)
    if parsed.scheme in ("http", "https"):
        music_file = download_url_to_temp_audio(music_source_path)
        if not music_file:
            raise RuntimeError("Failed to download music from URL: " + music_source_path)
    else:
        if os.path.isfile(music_source_path):
            music_file = os.path.abspath(music_source_path)
        else:
            raise RuntimeError(f"Music file not found: {music_source_path}")

    # 3) prepare trimmed/looped/volume-adjusted music (audio-only)
    prepared = prepare_music_for_duration(music_file, duration=music_segment_duration, volume=music_volume, loop=music_loop)
    if not prepared:
        raise RuntimeError("Failed to prepare music file")

    # 4) build filter_complex: delay music by music_start (ms)
    adelay_ms = int(round(music_start * 1000.0))
    stereo_delay = f"{adelay_ms}|{adelay_ms}"

    video_has_audio = has_audio(input_video)

    if video_has_audio:
        filter_parts = []
        filter_parts.append(f"[0:a]volume={reduce_original_volume:.6f}[va]")

        if adelay_ms > 0:
            filter_parts.append(f"[1:a]adelay={stereo_delay},apad[mv]")
        else:
            filter_parts.append(f"[1:a]apad[mv]")

        filter_parts.append("[va][mv]amix=inputs=2:duration=first:dropout_transition=2[aout]")

        filter_complex = ";".join(filter_parts)

        cmd = [
            "ffmpeg", "-y",
            "-i", input_video,
            "-i", prepared,
            "-filter_complex", filter_complex,
            "-map", "0:v",
            "-map", "[aout]",
            "-c:v", "copy",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest",
            out_video
        ]
    else:
        if adelay_ms > 0:
            filter_complex = f"[1:a]adelay={stereo_delay},apad[aout]"
        else:
            filter_complex = f"[1:a]apad[aout]"

        cmd = [
            "ffmpeg", "-y",
            "-i", input_video,
            "-i", prepared,
            "-filter_complex", filter_complex,
            "-map", "0:v",
            "-map", "[aout]",
            "-c:v", "copy",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest",
            out_video
        ]

    try:
        run_cmd(cmd)
    finally:
        try:
            if prepared and prepared.startswith(tempfile.gettempdir()):
                os.remove(prepared)
        except Exception:
            pass