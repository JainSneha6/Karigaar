import os
import tempfile
from flask import Blueprint, request, send_file, current_app, jsonify
from werkzeug.utils import secure_filename
from video_edit.core import process_with_gemini
import requests
import base64
ELEVEN_API_KEY = 'sk_119a741c6b322f526f7e712be124a4007a04b3294734b78d'
DEFAULT_VOICE_ID = 'KaCAGkAghyX8sFEYByRC'  # replace with your preferred default

# ElevenLabs TTS base URL (adjust if ElevenLabs changes their API path)
ELEVEN_TTS_BASE = "https://api.elevenlabs.io/v1/text-to-speech"


edit_bp = Blueprint('edit', __name__)


@edit_bp.route('/edit', methods=['POST'])
def edit_video():
    """
    POST /api/edit
    Form fields (multipart/form-data):
      - video: file blob (required)
      - user_prompt: natural language instruction (required)

    Returns the edited video as an attachment (video/mp4) on success.
    """
    
    if 'video' not in request.files:
        return jsonify({"error": "No 'video' file part"}), 400

    vid_file = request.files['video']
    if vid_file.filename == '':
        return jsonify({"error": "Empty filename"}), 400

    # Save uploaded file to a temp path
    fd, input_tmp = tempfile.mkstemp(suffix='.' + secure_filename(vid_file.filename).rsplit('.', 1)[-1])
    os.close(fd)
    try:
        vid_file.save(input_tmp)
    except Exception as e:
        try:
            os.remove(input_tmp)
        except Exception:
            pass
        return jsonify({"error": f"Failed to save uploaded file: {e}"}), 500

    user_prompt = request.form.get('user_prompt', '').strip()

    if not user_prompt:
        os.remove(input_tmp)
        return jsonify({"error": "user_prompt must be provided."}), 400

    google_api_key = "AIzaSyAVSGUozgbc7AQs4xEhP_-xaTGtN78HBFU"
    if not google_api_key:
        raise RuntimeError("GOOGLE_API_KEY not configured in environment.")

    # Temporary output file
    out_fd, out_tmp = tempfile.mkstemp(suffix='.mp4')
    os.close(out_fd)

    try:
        process_with_gemini(input_tmp, user_prompt, out_tmp, api_key=google_api_key)

        # Stream the resulting file back
        return send_file(out_tmp, as_attachment=True, download_name='edited.mp4', mimetype='video/mp4')

    except Exception as e:
        current_app.logger.exception('Video edit failed')
        return jsonify({"error": str(e)}), 500

    finally:
        # cleanup input file and output file will be removed by the runtime or left for the sending to finish
        try:
            if os.path.exists(input_tmp):
                os.remove(input_tmp)
        except Exception:
            pass
        # Note: out_tmp is returned via send_file; if you want to remove it after send, use file streaming with generator.


@edit_bp.route('/tts', methods=['POST'])
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
    # Many ElevenLabs TTS endpoints accept POST /v1/text-to-speech/{voice_id} and return audio binary.
    url = f"{ELEVEN_TTS_BASE}/{voice_id}"
    headers = {
        "xi-api-key": ELEVEN_API_KEY,
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
    }
    body = {
        "text": text
        # Optionally add voice_settings, model, etc. depending on your ElevenLabs plan.
    }

    try:
        resp = requests.post(url, json=body, headers=headers, timeout=30)
        resp.raise_for_status()
        audio_bytes = resp.content
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
        return jsonify({"audio_base64": audio_b64, "mime": "audio/mpeg"})
    except requests.HTTPError as http_err:
        current_app.logger.exception("ElevenLabs TTS HTTP error")
        try:
            # attempt to include server-side error details if any
            return jsonify({"error": f"ElevenLabs HTTP error: {http_err}; body: {resp.text}"}), 502
        except Exception:
            return jsonify({"error": str(http_err)}), 502
    except Exception as e:
        current_app.logger.exception("ElevenLabs TTS failed")
        return jsonify({"error": str(e)}), 500