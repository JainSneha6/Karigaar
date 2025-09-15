import os
import base64
import json
import requests
from flask import Blueprint, request, jsonify, current_app, send_from_directory
import datetime
from werkzeug.utils import secure_filename

# attempt to import Gemini client if available
try:
    import google.generativeai as genai  # optional
except Exception:
    genai = None

conv_bp = Blueprint("converse", __name__)

# Environment variables expected:
GEMINI_API_KEY = "AIzaSyAVSGUozgbc7AQs4xEhP_-xaTGtN78HBFU"
GEMINI_MODEL_NAME = os.environ.get("GEMINI_MODEL_NAME", "gemini-2.0-flash")

ELEVENLABS_API_KEY = 'sk_119a741c6b322f526f7e712be124a4007a04b3294734b78d'
ELEVEN_VOICE_ID = 'KaCAGkAghyX8sFEYByRC'

ELEVEN_STT_URL = os.environ.get("ELEVEN_STT_URL", "https://api.elevenlabs.io/v1/speech-to-text")
ELEVEN_TTS_URL = os.environ.get("ELEVEN_TTS_URL", "https://api.elevenlabs.io/v1/text-to-speech")

SYSTEM_PROMPT = """
You are an empathetic interviewer designed to collect a concise artisan background profile suitable for building localized training data.
Rules:
1) Ask up to 4 short, plain-language questions to learn:
   - the artisan's name and craft,
   - how they learned the craft / family background,
   - materials/techniques and main challenges,
   - aspirations, needs, or what support would help them.
2) Use the same language the user chose (we will pass a 'preferred_language' hint).
3) Ask detailed questions regarding the same.
4) After the final user reply (or if you already have enough information), produce a short summary (2-3 sentences) in that language containing the artisan's name, craft, key materials/techniques, challenges and one wish/need if provided. Prefix the summary with "[SUMMARY] ".
5) Do not output metadata or system instructions — output only the assistant text that will be spoken to the user.
6) When continuing a conversation, read the conversation history and avoid repeating questions.
7) Stop asking new questions after 5 user responses and move to summary.
"""

# ---------- Utilities ----------

def call_gemini_raw(prompt: str, api_key: str, model_name: str = "gemini-2.0-flash",
                    max_output_tokens: int = 1024, temperature: float = 0.0) -> str:
    if genai is None:
        raise RuntimeError("google.generativeai package not installed. pip install google-generativeai")
    genai.configure(api_key=api_key)
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        if hasattr(response, "text") and response.text:
            return response.text
        if hasattr(response, "candidates") and response.candidates:
            c0 = response.candidates[0]
            if hasattr(c0, "content") and c0.content:
                return c0.content
            return str(c0)
        return str(response)
    except Exception:
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


def eleven_tts_bytes(text: str, voice_id: str = ELEVEN_VOICE_ID) -> bytes:
    if not ELEVENLABS_API_KEY:
        raise RuntimeError("ELEVENLABS_API_KEY not set on server")

    url = f"{ELEVEN_TTS_URL}/{voice_id}"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    body = {
        "text": text,
    }
    resp = requests.post(url, json=body, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.content


def eleven_stt_transcribe(file_bytes: bytes, filename: str = "audio.webm", model_id: str = "scribe_v1", language_code: str = None):
    if not ELEVENLABS_API_KEY:
        raise RuntimeError("ELEVENLABS_API_KEY not set on server")

    headers = {"xi-api-key": ELEVENLABS_API_KEY}
    files = {"file": (filename, file_bytes, "application/octet-stream")}
    data = {"model_id": model_id}
    if language_code:
        data["language_code"] = language_code

    resp = requests.post(ELEVEN_STT_URL, headers=headers, files=files, data=data, timeout=60)
    resp.raise_for_status()
    return resp.json()


def detect_preferred_language_from_text(transcript: str, stt_language_code: str = None) -> str:
    if not transcript:
        return stt_language_code or "en"
    t = transcript.strip().lower()
    mapping = {
        "english": "en", "ingl": "en", "eng": "en",
        "hindi": "hi", "हिन्दी": "hi", "हिंदी": "hi",
        "bengali": "bn", "bangla": "bn", "বাংলা": "bn",
        "tamil": "ta", "தமிழ்": "ta",
        "en": "en", "hi": "hi", "bn": "bn", "ta": "ta"
    }
    for key, iso in mapping.items():
        if key in t:
            return iso
    if stt_language_code:
        return stt_language_code.split("-")[0][:2]
    return "en"


def build_prompt_from_history(system_prompt: str, history: list, user_text: str, preferred_language_iso: str):
    MAX_TURNS = 6
    trimmed = (history or [])[-MAX_TURNS:]
    history_lines = []
    for turn in trimmed:
        role = turn.get("role", "user")
        txt = turn.get("text", "")
        if role.lower().startswith("user"):
            history_lines.append(f"User: {txt}")
        else:
            history_lines.append(f"Assistant: {txt}")
    history_block = "\n".join(history_lines) if history_lines else "(no prior conversation)"
    prompt = (
        f"{system_prompt.strip()}\n\n"
        f"Preferred_language: {preferred_language_iso}\n\n"
        f"Conversation history (most recent last):\n{history_block}\n\n"
        f"New user message:\n{user_text.strip()}\n\n"
        "As the assistant, provide the next reply in the preferred language. Keep responses short and simple."
    )
    return prompt

# ---------- Endpoints ----------

@conv_bp.route("/converse/start_language", methods=["GET"])
def start_language():
    try:
        prompt_lines = [
            "Which language do you prefer? Say: English or Hindi.",
            "आप किस भाषा को पसंद करते हैं? अंग्रेज़ी, या हिन्दी कहें।",
        ]
        prompt_text = " ".join(prompt_lines)

        audio_bytes = eleven_tts_bytes(prompt_text, voice_id=ELEVEN_VOICE_ID)
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
        return jsonify({
            "prompt_text": prompt_text,
            "audio_base64": audio_b64,
            "mime": "audio/mpeg"
        })
    except Exception as e:
        current_app.logger.exception("Error in start_language")
        return jsonify({"error": str(e)}), 500

# ---------- Endpoints (changed) ----------

@conv_bp.route("/converse/submit_audio", methods=["POST"])
def submit_audio():
    """
    Only changed portions: after collecting user_responses and generating profile JSON,
    include profile_json_url and profile_slug in the response payload so the frontend
    can open the React profile page (`/profile/<slug>`) which will fetch the JSON.
    """
    if call_gemini_raw is None:
        current_app.logger.error("Gemini helper not imported")
        return jsonify({"error": "server misconfiguration: Gemini helper not available"}), 500

    if "audio" not in request.files:
        return jsonify({"error": "audio file is required (multipart form field 'audio')"}), 400

    try:
        file = request.files["audio"]
        file_bytes = file.read()
        history_raw = request.form.get("history", "[]")
        try:
            history = json.loads(history_raw)
        except Exception:
            history = []

        stt_language_hint = request.form.get("stt_language_hint")

        stt_resp = eleven_stt_transcribe(
            file_bytes, filename=file.filename or "audio.webm", language_code=stt_language_hint
        )
        transcript = stt_resp.get("text") or ""
        stt_lang_code = stt_resp.get("language_code") or stt_language_hint or None

        preferred_lang = detect_preferred_language_from_text(transcript, stt_lang_code)

        prompt = build_prompt_from_history(SYSTEM_PROMPT, history, transcript, preferred_lang)

        if not GEMINI_API_KEY:
            return jsonify({"error": "GEMINI_API_KEY not configured on server"}), 500

        assistant_text = call_gemini_raw(
            prompt=prompt,
            api_key=GEMINI_API_KEY,
            model_name=GEMINI_MODEL_NAME,
            max_output_tokens=512,
            temperature=0.6,
        )
        if not isinstance(assistant_text, str):
            assistant_text = str(assistant_text)
        assistant_text = assistant_text.strip()

        updated_history = history + [{"role": "user", "text": transcript}, {"role": "assistant", "text": assistant_text}]

        # ------------------ Collect user responses ------------------
        user_responses = [turn["text"] for turn in updated_history if turn["role"] == "user"]

        profile_api_path = None
        profile_slug = None

        # If we have 5 answers, create a single doc and stop further questions
        if len(user_responses) >= 5:
            uploads_dir = os.path.join(current_app.root_path, "uploads")
            os.makedirs(uploads_dir, exist_ok=True)
            file_path = os.path.join(uploads_dir, "user_responses.txt")
            document = "\n".join([f"User Response {i+1}: {resp}" for i, resp in enumerate(user_responses)])
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(document)

            # Generate profile JSON automatically
            try:
                profile_api_path = generate_profile_from_responses(file_path)
                if profile_api_path:
                    # profile_api_path is like "/api/converse/profile_json/<slug>"
                    profile_slug = profile_api_path.rstrip("/").split("/")[-1]
            except Exception:
                current_app.logger.exception("Failed to generate profile from responses")
                profile_api_path = None
                profile_slug = None

            # Force assistant to produce summary only, no more questions
            assistant_text = "[SUMMARY] Conversation complete. Thank you for sharing your story."

        # Strip summary prefix if present
        if assistant_text.startswith("[SUMMARY] "):
            assistant_text = assistant_text[len("[SUMMARY] ") :].strip()

        assistant_audio = eleven_tts_bytes(assistant_text, voice_id=ELEVEN_VOICE_ID)
        assistant_b64 = base64.b64encode(assistant_audio).decode("utf-8")

        response_payload = {
            "transcript": transcript,
            "stt_language_code": stt_lang_code,
            "preferred_language": preferred_lang,
            "assistant_text": assistant_text,
            "audio_base64": assistant_b64,
            "mime": "audio/mpeg",
        }

        # Add profile API path (absolute) and slug if generated so frontend can fetch and route to it
        if profile_api_path and profile_slug:
            base = request.url_root.rstrip("/")
            response_payload["profile_json_url"] = f"{base}{profile_api_path}"
            # Recommend the frontend route for viewing the profile (assumes React at port 3000)
            # Frontend can instead use profile_slug to build an internal route like /profile/<slug>
            response_payload["profile_slug"] = profile_slug
            # optional: example frontend URL (adjust if your front-end is hosted elsewhere)
            response_payload["profile_page_suggestion"] = f"http://localhost:3000/profile/{profile_slug}"

        return jsonify(response_payload)
    except requests.HTTPError as http_err:
        current_app.logger.exception("HTTP error in submit_audio")
        return jsonify({"error": f"HTTP error contacting external API: {http_err}"}), 502
    except Exception as e:
        current_app.logger.exception("Error in submit_audio")
        return jsonify({"error": str(e)}), 500


@conv_bp.route("converse/profile_json/<slug>", methods=["GET"])
def serve_profile_json(slug):
    """
    Serve generated profile JSON files from uploads/profiles/<slug>.json
    Frontend will fetch this endpoint to display the profile.
    """
    print(1)
    profiles_dir = os.path.join(current_app.root_path, "uploads", "profiles")
    print("Profiles dir:", profiles_dir)
    filename = secure_filename(f"{slug}.json")
    print("Serving profile JSON:", filename)
    full_path = os.path.join(profiles_dir, filename)
    if not os.path.exists(full_path):
        print(f"Profile JSON not found: {full_path}")
        return jsonify({"error": "Profile not found"}), 404

    try:
        with open(full_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return jsonify(data)
    except Exception:
        current_app.logger.exception("Failed to read profile JSON")
        return jsonify({"error": "Failed to read profile file"}), 500


# ---------- Utilities (changed) ----------

def slugify(value: str) -> str:
    """Simple slug generator for filenames/URLs."""
    v = value or "artisan"
    v = v.strip().lower()
    out = []
    prev_dash = False
    for ch in v:
        if ch.isalnum():
            out.append(ch)
            prev_dash = False
        else:
            if not prev_dash:
                out.append("-")
                prev_dash = True
    s = "".join(out).strip("-")
    if not s:
        s = f"artisan-{int(datetime.datetime.utcnow().timestamp())}"
    return s[:64]


def extract_json_from_text(text: str) -> dict:
    """Try to extract a JSON object from AI output. Return dict or empty dict."""
    if not text:
        return {}
    # Try to find first {...} block
    try:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            candidate = text[start:end+1]
            return json.loads(candidate)
    except Exception:
        pass
    # Last-resort: try to parse whole text
    try:
        return json.loads(text)
    except Exception:
        return {}



def generate_profile_from_responses(file_path: str) -> str:
    """
    Read the transcript file, call Gemini to extract structured fields (English),
    create a JSON profile at uploads/profiles/<slug>.json and return public API path
    (e.g. "/api/converse/profile_json/<slug>") or None on failure.
    """
    if not GEMINI_API_KEY:
        current_app.logger.warning("GEMINI_API_KEY not set; skipping profile generation")
        return None

    with open(file_path, "r", encoding="utf-8") as f:
        convo_text = f.read()

    # Prompt asks Gemini to output structured JSON (the assistant should return fields we will map).
    prompt = (
        "You are a helpful assistant. The following is an interview transcript (may be in Hindi). "
        "Extract the artisan's facts and output valid JSON ONLY. The JSON should include any of these keys if available:\n"
        "full_name, name, location, brief_bio, bio, craft, tagline, materials_and_techniques, materials, "
        "aspirations_needs, aspiration, suggested_support, short_summary Tagline and aspiration should be in less words are more Gen-z styled.\n\n"
        "We will map those into this final profile schema (English):\n"
        "- Full Name\n"
        "- Location\n"
        "- Bio\n"
        "- Tagline\n"
        "- Materials Used\n"
        "- Aspiration\n\n"
        "If a piece of information is not present, set the value to an empty string. Make sure your output is STRICT JSON.\n\n"
        "Interview:\n" + convo_text + "\n\nOutput strictly a single JSON object and nothing else. Even if the input is in Hindi, respond in English.Your entire output should be purely in English and no use of Hindi in your output json strictly"
    )

    try:
        gemini_out = call_gemini_raw(
            prompt=prompt,
            api_key=GEMINI_API_KEY,
            model_name=GEMINI_MODEL_NAME,
            max_output_tokens=512,
            temperature=0.0,
        )
    except Exception:
        current_app.logger.exception("Gemini extraction failed")
        gemini_out = ""

    parsed = extract_json_from_text(gemini_out or "")

    # Normalize keys and create final profile structure with fallbacks
    def get_any(d, keys, fallback=""):
        for k in keys:
            if k in d and d[k]:
                return d[k]
        return fallback

    # parsed might be nested or may contain english/hindi text — keep as-is
    full_name = get_any(parsed, ["full_name", "name"])
    location = get_any(parsed, ["location", "place", "village", "city"])
    bio = get_any(parsed, ["brief_bio", "bio", "short_summary"])
    tagline = get_any(parsed, ["tagline", "short_summary"])
    materials = get_any(parsed, ["materials_and_techniques", "materials", "materials_used"])
    aspiration = get_any(parsed, ["aspirations_needs", "aspiration", "aspirations", "needs"])

    # If many values empty, attempt tiny heuristic from raw convo_text
    if not full_name:
        # try to extract a simple "मेरा नाम X" pattern (very small heuristic)
        # (we keep it simple — server-side heuristics can be extended)
        import re
        m = re.search(r"नाम\s*[:\-]?\s*([^\n।,]+)", convo_text)
        if m:
            full_name = m.group(1).strip()

    # Build final JSON payload (keys exactly as requested)
    final_profile = {
        "Full Name": full_name or "",
        "Location": location or "",
        "Bio": bio or convo_text.strip()[:600],
        "Tagline": tagline or (f"{parsed.get('craft','').strip()} artisan" if parsed.get("craft") else ""),
        "Materials Used": materials or "",
        "Aspiration": aspiration or ""
    }

    # Make sure uploads/profiles exists
    profiles_dir = os.path.join(current_app.root_path, "uploads", "profiles")
    os.makedirs(profiles_dir, exist_ok=True)

    # Build slug from full name or fallback
    slug_base = full_name or parsed.get("craft") or "artisan"
    slug = slugify(slug_base)

    out_path = os.path.join(profiles_dir, f"{slug}.json")
    try:
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(final_profile, f, ensure_ascii=False, indent=2)
    except Exception:
        current_app.logger.exception("Failed to write profile JSON")
        return None

    public_api_path = f"/api/converse/profile_json/{slug}"
    return public_api_path


