# video_edit/core.py
"""
Core video editing functions.

Exposes:
  - process_with_gemini(input_path, user_prompt, output_path, api_key)
  - process_with_manual_edits(input_path, edits_json_text, output_path)

Note: This module depends on ffmpeg/ffprobe being available on PATH.
"""
import os
import tempfile
import json
from typing import List


from .ffmpeg_utils import get_duration
from .llm import call_gemini_json
from .timeline import normalize_and_validate_edits, build_segments_to_keep,concat_segments,create_segment
from .stickers import apply_stickers_to_video
from .music import search_and_fetch_music,mix_background_music


def process_with_gemini(input_path: str, user_prompt: str, output_path: str,
                        api_key: str, model_name: str = "gemini-2.0-flash"):
    print("Requesting edits from Gemini...")
    json_text = call_gemini_json(user_prompt, api_key=api_key, model_name=model_name)
    edits = json.loads(json_text)

    duration = get_duration(input_path)
    print(f"Input duration: {duration:.3f} seconds")

    edits = normalize_and_validate_edits(edits, duration)
    print("Parsed edits:", json.dumps(edits, indent=2))

    sticker_edits = [e for e in edits if e["action"] == "sticker"]
    music_edits = [e for e in edits if e["action"] == "music"]
    timeline_edits = [e for e in edits if e["action"] in ("cut", "speed")]

    segments = build_segments_to_keep(timeline_edits, duration)
    print("Planned segments:", json.dumps(segments, indent=2))

    temp_files: List[str] = []
    try:
        for i, seg in enumerate(segments):
            fd, tmp = tempfile.mkstemp(suffix='.mp4')
            os.close(fd)
            os.unlink(tmp)
            out_path_tmp = tmp
            create_segment(input_path, seg, out_path_tmp)
            temp_files.append(out_path_tmp)

        if not temp_files:
            raise RuntimeError("No output segments created (maybe the entire video was cut?).")

        intermediate = output_path + ".intermediate.mp4"
        concat_segments(temp_files, intermediate)
        print("Intermediate (timeline edits applied) written to", intermediate)

        after_stickers_path = intermediate
        if sticker_edits:
            print("Applying sticker overlays:", json.dumps(sticker_edits, indent=2))
            tmp_with_stickers = output_path + ".withstickers.mp4"
            apply_stickers_to_video(intermediate, sticker_edits, tmp_with_stickers)
            after_stickers_path = tmp_with_stickers
            try:
                os.remove(intermediate)
            except Exception:
                pass

        if music_edits:
            m = music_edits[0]
            print("Processing music edit:", json.dumps(m, indent=2))
            music_file = search_and_fetch_music(m)
            if not music_file:
                raise RuntimeError("Could not find or download music for query/url/file in edit: " + str(m))
            mix_background_music(after_stickers_path, music_file, output_path,
                                 music_start=m["start"], music_end=m["end"],
                                 music_volume=m.get("volume", 0.4), reduce_original_volume=1.0,
                                 music_loop=m.get("loop", True), fade=1.0)
            if after_stickers_path != intermediate:
                try:
                    os.remove(after_stickers_path)
                except Exception:
                    pass
        else:
            os.replace(after_stickers_path, output_path)
            print("Output written to", output_path)
    finally:
        for p in temp_files:
            try:
                os.remove(p)
            except Exception:
                pass


def process_with_manual_edits(input_path: str, edits_json_text: str, output_path: str):
    edits = json.loads(edits_json_text)
    duration = get_duration(input_path)
    edits = normalize_and_validate_edits(edits, duration)
    sticker_edits = [e for e in edits if e["action"] == "sticker"]
    music_edits = [e for e in edits if e["action"] == "music"]
    timeline_edits = [e for e in edits if e["action"] in ("cut", "speed")]
    segments = build_segments_to_keep(timeline_edits, duration)

    temp_files: List[str] = []
    try:
        for i, seg in enumerate(segments):
            fd, tmp = tempfile.mkstemp(suffix='.mp4')
            os.close(fd)
            os.unlink(tmp)
            create_segment(input_path, seg, tmp)
            temp_files.append(tmp)
        intermediate = output_path + ".intermediate.mp4"
        concat_segments(temp_files, intermediate)

        after_stickers_path = intermediate
        if sticker_edits:
            tmp_with_stickers = output_path + ".withstickers.mp4"
            apply_stickers_to_video(intermediate, sticker_edits, tmp_with_stickers)
            after_stickers_path = tmp_with_stickers
            try:
                os.remove(intermediate)
            except Exception:
                pass

        if music_edits:
            m = music_edits[0]
            music_file = search_and_fetch_music(m)
            if not music_file:
                raise RuntimeError("Could not find or download music for query/url/file in edit: " + str(m))
            mix_background_music(after_stickers_path, music_file, output_path,
                                 music_start=m["start"], music_end=m["end"],
                                 music_volume=m.get("volume", 0.4), reduce_original_volume=1.0,
                                 music_loop=m.get("loop", True), fade=1.0)
            if after_stickers_path != intermediate:
                try:
                    os.remove(after_stickers_path)
                except Exception:
                    pass
        else:
            os.replace(after_stickers_path, output_path)
        print("Output written to", output_path)
    finally:
        for p in temp_files:
            try:
                os.remove(p)
            except Exception:
                pass
