import os
import tempfile
from typing import List, Dict, Any

from .ffmpeg_utils import run_cmd


def normalize_and_validate_edits(edits: List[Dict[str, Any]], duration: float) -> List[Dict[str, Any]]:
    norm: List[Dict[str, Any]] = []
    for e in edits:
        a = e.get("action")
        if a not in ("cut", "speed", "sticker", "music"):
            continue
        if a == "sticker" or a == "music":
            s = float(e.get("start", 0.0))
            if "end" in e:
                t = float(e.get("end"))
            elif "duration" in e:
                t = s + float(e.get("duration", 2.0))
            else:
                t = s + 2.0
            s = max(0.0, min(s, duration))
            t = max(0.0, min(t, duration))
            if t - s < 0.05:
                continue
            newe = {"action": a, "start": s, "end": t}
            if "content" in e:
                newe["content"] = e["content"]
            if "position" in e:
                newe["position"] = e["position"]
            if "x" in e:
                newe["x"] = e["x"]
            if "y" in e:
                newe["y"] = e["y"]
            if "fontsize" in e:
                newe["fontsize"] = int(e["fontsize"])
            if a == "music":
                newe["query"] = e.get("query")
                newe["url"] = e.get("url")
                newe["file"] = e.get("file")
                newe["volume"] = float(e.get("volume", 0.4))
                newe["loop"] = bool(e.get("loop", True))
                newe["source"] = e.get("source")
            norm.append(newe)
        else:
            s = float(e.get("start", 0.0))
            t = float(e.get("end", s))
            if t <= s:
                continue
            s = max(0.0, min(s, duration))
            t = max(0.0, min(t, duration))
            if t - s < 0.05:
                continue
            newe = {"action": a, "start": s, "end": t}
            if a == "speed":
                newe["rate"] = float(e.get("rate", 1.0))
            norm.append(newe)
    non_sticker = [x for x in norm if x["action"] in ("cut", "speed")]
    non_sticker.sort(key=lambda z: z["start"])
    for i in range(len(non_sticker)-1):
        if non_sticker[i]["end"] > non_sticker[i+1]["start"] - 1e-6:
            raise ValueError(f"Overlapping edits detected: {non_sticker[i]} and {non_sticker[i+1]}. Please have model output non-overlapping edits.")
    stickers = [x for x in norm if x["action"] == "sticker"]
    musics = [x for x in norm if x["action"] == "music"]
    final = non_sticker + stickers + musics
    final.sort(key=lambda z: z["start"])
    return final


def build_segments_to_keep(edits: List[Dict[str, Any]], duration: float) -> List[Dict[str, Any]]:
    segments = []
    cur = 0.0
    timeline_edits = [e for e in edits if e["action"] in ("cut", "speed")]
    timeline_edits.sort(key=lambda x: x["start"])
    for e in timeline_edits:
        if cur < e["start"]:
            segments.append({"start": cur, "end": e["start"], "action": "keep"})
        if e["action"] == "cut":
            cur = e["end"]
        elif e["action"] == "speed":
            segments.append({"start": e["start"], "end": e["end"], "action": "speed", "rate": e["rate"]})
            cur = e["end"]
    if cur < duration:
        segments.append({"start": cur, "end": duration, "action": "keep"})
    segments = [s for s in segments if s["end"] - s["start"] > 0.04]
    return segments


def atempo_filter_chain(rate: float) -> str:
    if rate <= 0:
        raise ValueError("rate must be > 0")
    parts = []
    remaining = rate
    if remaining >= 2.0:
        while remaining > 2.0001:
            parts.append("atempo=2.0")
            remaining /= 2.0
            if remaining < 2.0:
                break
    parts.append(f"atempo={remaining:.6f}")
    return ",".join(parts)


def create_segment(input_path: str, seg: Dict[str, Any], out_path: str):
    s = seg["start"]
    e = seg["end"]
    duration = e - s
    if seg["action"] == "keep":
        cmd = [
            "ffmpeg", "-y",
            "-ss", f"{s:.3f}",
            "-t", f"{duration:.3f}",
            "-i", input_path,
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
            "-c:a", "aac", "-b:a", "128k",
            out_path
        ]
        run_cmd(cmd)
    elif seg["action"] == "speed":
        rate = float(seg.get("rate", 1.0))
        if rate <= 0:
            raise ValueError("Invalid rate")
        atempo_chain = atempo_filter_chain(rate)
        filter_complex = f"[0:v]setpts=PTS/{rate}[v];[0:a]{atempo_chain}[a]"
        cmd = [
            "ffmpeg", "-y",
            "-ss", f"{s:.3f}",
            "-t", f"{duration:.3f}",
            "-i", input_path,
            "-filter_complex", filter_complex,
            "-map", "[v]", "-map", "[a]",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
            "-c:a", "aac", "-b:a", "128k",
            out_path
        ]
        run_cmd(cmd)
    else:
        raise ValueError("Unknown segment action")


def concat_segments(segment_files: List[str], final_out: str):
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt") as f:
        list_path = f.name
        for p in segment_files:
            f.write(f"file '{os.path.abspath(p)}'\n")
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", list_path,
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
        "-c:a", "aac", "-b:a", "128k",
        final_out
    ]
    try:
        run_cmd(cmd)
    finally:
        try:
            os.remove(list_path)
        except Exception:
            pass