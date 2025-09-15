# llm.py
import json
import re
import os

# attempt to import Gemini client if available
try:
    import google.generativeai as genai  # optional
except Exception:
    genai = None

from .ffmpeg_utils import secs, get_tmp_dir, make_tmp_file


def extract_json_from_text(text: str) -> str:
    array_match = re.search(r"\[.*\]", text, flags=re.DOTALL)
    if array_match:
        return array_match.group(0)
    obj_match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if obj_match:
        return obj_match.group(0)
    return text


def call_gemini_raw(prompt: str, api_key: str, model_name: str = "gemini-2.0-flash",
                    max_output_tokens: int = 1024, temperature: float = 0.0) -> str:
    """
    Minimal wrapper around google.generativeai. Raises if package missing or call fails.
    """
    if genai is None:
        raise RuntimeError("google.generativeai package not installed. pip install google-generativeai")
    if not api_key:
        raise RuntimeError("No API key provided for Gemini.")
    genai.configure(api_key=api_key)
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        # try standard access patterns
        if hasattr(response, "text") and response.text:
            return response.text
        if hasattr(response, "candidates") and response.candidates:
            c0 = response.candidates[0]
            if hasattr(c0, "content") and c0.content:
                return c0.content
            return str(c0)
        return str(response)
    except Exception:
        # fallback to older API if available
        try:
            res = genai.generate(model=model_name, prompt=prompt, max_output_tokens=max_output_tokens, temperature=temperature)
            if isinstance(res, str):
                return res
            if hasattr(res, "candidates") and res.candidates:
                cand = res.candidates[0]
                if hasattr(cand, "content"):
                    return cand.content
                return str(cand)
            if isinstance(res, dict):
                if "candidates" in res and len(res["candidates"]) > 0:
                    c0 = res["candidates"][0]
                    if isinstance(c0, dict) and "content" in c0:
                        return c0["content"]
                    return json.dumps(c0)
                if "output" in res:
                    return res["output"]
            return str(res)
        except Exception as exc:
            raise RuntimeError(f"Failed to call Gemini: {exc}") from exc


def _write_debug_tmp(prefix: str, content: str) -> str:
    """
    Write `content` to a writable tmp file and return its path. Silently fails if write not possible.
    """
    try:
        tmp_path = make_tmp_file(suffix=".txt", prefix=prefix)
        with open(tmp_path, "w", encoding="utf-8") as fh:
            fh.write(content or "")
        return tmp_path
    except Exception:
        # best-effort only; don't crash the main flow if debugging write fails
        try:
            # fallback to system tmpdir if make_tmp_file didn't work
            alt = os.path.join(get_tmp_dir(), f"{prefix}{os.getpid()}.txt")
            with open(alt, "w", encoding="utf-8") as fh:
                fh.write(content or "")
            return alt
        except Exception:
            return ""


def call_gemini_json(user_instruction: str, api_key: str, model_name: str = "gemini-2.0-flash") -> str:
    """
    Build a strict JSON-only prompt for the Gemini model and return the JSON text
    (a JSON array of edits). Writes raw+extracted outputs to tmp for debugging.
    Raises RuntimeError if parsing fails.
    """
    prompt = f"""
You are a machine assistant that MUST respond with MACHINE-READABLE JSON ONLY (no commentary, no markdown).
Given a user's natural-language video editing instruction, output a JSON array of edits. Each edit is an object with:
 - action: one of "cut", "speed", "sticker", "music"
 - For "cut": include start and end as seconds (float).
 - For "speed": include start, end (seconds), and rate (float).
 - For "sticker": include start and end (seconds) OR start and duration, and a content object:
      either {{ "emoji": "🔥" }}  (the actual emoji character) or {{ "image": "/full/path/to/sticker.png" }} (a local path).
   Optional sticker fields: position (one of top-left, top-right, bottom-left, bottom-right, center),
                        x (px), y (px), fontsize (int).
 - For "music": include start and end (seconds) OR start and duration, and one of:
      {{ "query": "upbeat pop instrumental" }}  (search local music or Jamendo if enabled),
      {{ "file": "./music/track.mp3" }} (local path),
      {{ "url": "https://..." }} (direct URL).
   Optional music fields: volume (0.0-1.0, default 0.4), loop (bool, default true), source (jamendo|local|url)

Rules:
 - Do not include overlapping cut/speed edits. Sticker edits overlay and may overlap. Music edits may overlap timeline but are applied after timeline changes.
 - Use seconds as floats (e.g. 12.5).
 - If the user provides times like "00:01:20", convert them to seconds in the JSON.
 - If you cannot parse any valid edits, return an empty JSON array: [].
 - Output JSON only and nothing else.

Examples:
User instruction: "Add upbeat pop track throughout"
Output:
[{{"action":"music","start":0.0,"end":240.0,"query":"upbeat pop instrumental","volume":0.35,"loop":true}}]

User instruction: "Add instrumental beat with no lyrics from 0:10 to 0:50"
Output:
[{{"action":"music","start":10.0,"end":50.0,"query":"instrumental beat no vocals","volume":0.4,"loop":false}}]

User instruction: "Add fire emoji at 0:20 for 2 seconds"
Output:
[{{"action":"sticker","start":{secs('0:20'):.1f},"end":{secs('0:20')+2.0:.1f},"content":{{"emoji":"🔥"}},"position":"bottom-right","fontsize":72}}]

User instruction: "Add cat sticker at 1:20 for 2 seconds"
Output:
[{{"action":"sticker","start":{secs('1:20'):.1f},"end":{secs('1:20')+2.0:.1f},"content":{{"image": "./stickers/cat.png"}},"position":"bottom-right","fontsize":72}}]

User instruction: "Cut from 00:01:20 to 00:01:45"
Output:
[{{"action":"cut","start":{secs('00:01:20'):.1f},"end":{secs('00:01:45'):.1f}}}]

User instruction: "Make 00:03:10-00:03:20 play at 2x"
Output:
[{{"action":"speed","start":{secs('00:03:10'):.1f},"end":{secs('00:03:20'):.1f},"rate":2.0}}]

User instruction: "Make the speed of the video into 1.5x"
Output:
[{{"action":"speed","start":0.0,"end":240.0,"rate":1.5}}]


Now convert this user instruction to JSON and return JSON only (no extra text, no explanation).

User instruction:
\"\"\"{user_instruction}\"\"\""""
    raw = call_gemini_raw(prompt, api_key=api_key, model_name=model_name)
    # write raw output to tmp for debugging
    raw_tmp = _write_debug_tmp("gemini_raw_", raw)
    if raw_tmp:
        print("Gemini raw output written to:", raw_tmp)

    json_text = extract_json_from_text(raw)
    # write extracted JSON candidate to tmp for debugging
    extracted_tmp = _write_debug_tmp("gemini_extracted_", json_text)
    if extracted_tmp:
        print("Extracted JSON candidate written to:", extracted_tmp)

    print("Raw Gemini output (first 300 chars):", (raw or "")[:300])
    print("Extracted JSON candidate (first 300 chars):", (json_text or "")[:300])

    try:
        parsed = json.loads(json_text)
        print("Parsed Gemini JSON (type):", type(parsed).__name__)
        if not isinstance(parsed, list):
            raise ValueError("Gemini did not return a JSON array.")
        return json_text
    except Exception as ex:
        # On failure, write both raw and extracted to tmp for debugging before raising
        fail_raw_path = _write_debug_tmp("gemini_failed_raw_", raw or "")
        fail_extracted_path = _write_debug_tmp("gemini_failed_extracted_", json_text or "")
        if fail_raw_path or fail_extracted_path:
            print("Gemini parse failure artifacts:", fail_raw_path, fail_extracted_path)
        raise RuntimeError(
            f"Unable to parse Gemini output as JSON. Raw output written to: {fail_raw_path or 'n/a'}. "
            f"Extracted part written to: {fail_extracted_path or 'n/a'}. Error: {ex}"
        ) from ex
