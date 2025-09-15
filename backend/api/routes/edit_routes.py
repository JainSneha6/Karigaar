import os
import requests
import base64
from flask import Blueprint, request, send_file, current_app, jsonify
from werkzeug.utils import secure_filename

from ..video_edit.core import process_with_gemini
from ..video_edit.ffmpeg_utils import make_tmp_file, get_tmp_dir

# prefer reading API keys from env; fallback to existing literal if present
ELEVEN_API_KEY = os.environ.get("ELEVEN_API_KEY", "sk_119a741c6b322f526f7e712be124a4007a04b3294734b78d")
DEFAULT_VOICE_ID = os.environ.get("DEFAULT_VOICE_ID", "KaCAGkAghyX8sFEYByRC")

# ElevenLabs TTS base URL
ELEVEN_TTS_BASE = "https://api.elevenlabs.io/v1/text-to-speech"

edit_bp = Blueprint("edit", __name__)


@edit_bp.route("/edit", methods=["POST"])
def edit_video():
    """
    POST /api/edit
    Form fields (multipart/form-data):
      - video: file blob (required)
      - user_prompt: natural language instruction (required)

    Returns the edited video as an attachment (video/mp4) on success.
    """
    if "video" not in request.files:
        return jsonify({"error": "No 'video' file part"}), 400

    vid_file = request.files["video"]
    if vid_file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    # Determine extension safely
    safe_name = secure_filename(vid_file.filename)
    ext = ".mp4"
    if "." in safe_name:
        ext = "." + safe_name.rsplit(".", 1)[-1]

    # create temp input path inside writable tmp dir
    input_tmp = make_tmp_file(suffix=ext)
    if not input_tmp:
        return jsonify({"error": "Failed to create temporary file for upload"}), 500

    try:
        # Save uploaded file to the tmp path
        vid_file.save(input_tmp)
    except Exception as e:
        try:
            if os.path.exists(input_tmp):
                os.remove(input_tmp)
        except Exception:
            pass
        return jsonify({"error": f"Failed to save uploaded file: {e}"}), 500

    user_prompt = request.form.get("user_prompt", "").strip()
    if not user_prompt:
        try:
            if os.path.exists(input_tmp):
                os.remove(input_tmp)
        except Exception:
            pass
        return jsonify({"error": "user_prompt must be provided."}), 400

    # Prefer GEMINI API key from env
    google_api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or "AIzaSyAVSGUozgbc7AQs4xEhP_-xaTGtN78HBFU"
    if not google_api_key:
        try:
            if os.path.exists(input_tmp):
                os.remove(input_tmp)
        except Exception:
            pass
        return jsonify({"error": "GOOGLE_API_KEY not configured in environment."}), 500

    # Temporary output file inside tmp dir
    out_tmp = make_tmp_file(suffix=".mp4")
    if not out_tmp:
        try:
            if os.path.exists(input_tmp):
                os.remove(input_tmp)
        except Exception:
            pass
        return jsonify({"error": "Failed to create temporary output file"}), 500

    try:
        # Ensure output directory exists (make_tmp_file will place file in tmp dir; parent exists)
        process_with_gemini(input_tmp, user_prompt, out_tmp, api_key=google_api_key)

        # Stream the resulting file back
        # send_file will open the file; we won't delete out_tmp here because the runtime handles /tmp cleanup
        return send_file(out_tmp, as_attachment=True, download_name="edited.mp4", mimetype="video/mp4")
    except Exception as e:
        current_app.logger.exception("Video edit failed")
        # try to include a short trace but avoid leaking secrets
        return jsonify({"error": "video_edit_failed", "detail": str(e)}), 500
    finally:
        # cleanup input file; do not aggressively remove out_tmp because send_file may still be streaming it
        try:
            if os.path.exists(input_tmp):
                os.remove(input_tmp)
        except Exception:
            pass


@edit_bp.route("/tts", methods=["POST"])
def tts_text():
    """
    POST /api/tts
    JSON body:
      { "text": "Hello", "voice_id": "optional-voice-id" }
    Response:
      { "audio_base64": "...", "mime": "audio/mpeg" }
    """
    if not ELEVEN_API_KEY:
        current_app.logger.error("ELEVENLABS_API_KEY is not configured")
        return jsonify({"error": "Server misconfiguration: ELEVENLABS_API_KEY not configured"}), 500

    try:
        payload = request.get_json(force=True)
    except Exception:
        return jsonify({"error": "Request must be application/json with 'text' field."}), 400

    text = (payload.get("text") or "").strip()
    if not text:
        return jsonify({"error": "Field 'text' is required."}), 400

    voice_id = payload.get("voice_id") or DEFAULT_VOICE_ID

    # Build ElevenLabs TTS request
    url = f"{ELEVEN_TTS_BASE}/{voice_id}"
    headers = {
        "xi-api-key": ELEVEN_API_KEY,
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
    }
    body = {"text": text}

    try:
        resp = requests.post(url, json=body, headers=headers, timeout=30)
        resp.raise_for_status()
        audio_bytes = resp.content

        # Optionally write response to tmp for debugging (best-effort)
        try:
            tmp_debug = make_tmp_file(suffix=".mp3")
            if tmp_debug:
                with open(tmp_debug, "wb") as fh:
                    fh.write(audio_bytes)
                current_app.logger.debug(f"ElevenLabs TTS wrote debug audio to {tmp_debug}")
        except Exception:
            pass

        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
        return jsonify({"audio_base64": audio_b64, "mime": "audio/mpeg"})
    except requests.HTTPError as http_err:
        current_app.logger.exception("ElevenLabs TTS HTTP error")
        try:
            return jsonify({"error": f"ElevenLabs HTTP error: {http_err}; body: {resp.text}"}), 502
        except Exception:
            return jsonify({"error": str(http_err)}), 502
    except Exception as e:
        current_app.logger.exception("ElevenLabs TTS failed")
        return jsonify({"error": str(e)}), 500
