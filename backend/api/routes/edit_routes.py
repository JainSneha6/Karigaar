import os
import requests
import base64
from flask import Blueprint, request, send_file, current_app, jsonify
from werkzeug.utils import secure_filename
from ..video_edit.core import process_with_gemini
from ..video_edit.ffmpeg_utils import make_tmp_file, get_tmp_dir
# add these imports near the top of your blueprint file
from flask import Blueprint, request, jsonify, send_file, current_app
from werkzeug.utils import secure_filename
import os
from ..video_edit.music import mix_background_music, download_url_to_temp_audio

# prefer reading API keys from env; fallback to existing literal if present
ELEVEN_API_KEY = os.environ.get("ELEVEN_API_KEY", "sk_119a741c6b322f526f7e712be124a4007a04b3294734b78d")
DEFAULT_VOICE_ID = os.environ.get("DEFAULT_VOICE_ID", "KaCAGkAghyX8sFEYByRC")

# ElevenLabs TTS base URL
ELEVEN_TTS_BASE = "https://api.elevenlabs.io/v1/text-to-speech"

TRENDING_SONGS = [
      { "id": "s1", "title": "Sahiba", "artist": "Aditya Rikhari", "duration": 30, "public_url": "https://drive.google.com/uc?export=download&id=1u5k0HPhka_ytUGLt6eyn3awVM3oYSS6b" },
      { "id": "s2", "title": "Saiyaara", "artist": "Tanishk Bagchi", "duration": 28, "public_url": "https://drive.google.com/uc?export=download&id=1CaPk8_CvQdH1FUZiEGVkjpbAff3FMaEz" },
      { "id": "s3", "title": "Dard", "artist": "Kushagra", "duration": 32, "public_url": "https://drive.google.com/uc?export=download&id=1fLXKnSdCmNYztsPTQf6S7Xxbnanw4M5E" },
      { "id": "s4", "title": "Kaanamale", "artist": "Mugen Rao", "duration": 25, "public_url": "https://drive.google.com/uc?export=download&id=1MixJI_YU5S2ORKfrQamOs-TbrmpTZi4m" },
      { "id": "s5", "title": "Pardesiya", "artist": "Sachin-Jigar", "duration": 29, "public_url": "https://drive.google.com/uc?export=download&id=1GC0zEcPp-TYMbCpr-p1u-zaHHsGB_Uuy" },
      { "id": "s6", "title": "Noormahal", "artist": "Chani Nattan", "duration": 27, "public_url": "https://drive.google.com/uc?export=download&id=1XtSSZOeaH1Uu8oBmDKzbFQXxl0EiDe5V" },
      { "id": "s7", "title": "The Night We Met", "artist": "Lord Huron", "duration": 30, "public_url": "https://drive.google.com/uc?export=download&id=1cz0o_si2oIaWKu5a3rgERbWoOCW5r9aS" },
      { "id": "s8", "title": "Yaarum Sollala", "artist": "Shreyas Narasimhan", "duration": 31, "public_url": "https://drive.google.com/uc?export=download&id=1JyncQt2piEU-0VdVCywpYPeGn0fJpID2" },
      { "id": "s9", "title": "Sapphire", "artist": "Ed Sheeran", "duration": 26, "public_url": "https://drive.google.com/uc?export=download&id=16jpFu95nzQy-vAky1U_h0UIsg0gGToPR" },
    ],


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
    print("Received /api/edit request")
    if "video" not in request.files:
        return jsonify({"error": "No 'video' file part"}), 400

    print("Video file part found")
    vid_file = request.files["video"]
    if vid_file.filename == "":
        return jsonify({"error": "Empty filename"}), 400
    
    print(f"Uploaded filename: {vid_file.filename}")
    # Determine extension safely
    safe_name = secure_filename(vid_file.filename)
    ext = ".mp4"
    if "." in safe_name:
        ext = "." + safe_name.rsplit(".", 1)[-1]

    print(f"Using file extension: {ext}")
    # create temp input path inside writable tmp dir
    input_tmp = make_tmp_file(suffix=ext)
    if not input_tmp:
        return jsonify({"error": "Failed to create temporary file for upload"}), 500

    print(f"Saving uploaded file to temporary path: {input_tmp}")
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

    print("File saved successfully")
    user_prompt = request.form.get("user_prompt", "").strip()
    if not user_prompt:
        try:
            if os.path.exists(input_tmp):
                os.remove(input_tmp)
        except Exception:
            pass
        return jsonify({"error": "user_prompt must be provided."}), 400

    # Prefer GEMINI API key from env
    print("Retrieving Google API key from environment")
    google_api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or "AIzaSyAVSGUozgbc7AQs4xEhP_-xaTGtN78HBFU"
    if not google_api_key:
        try:
            if os.path.exists(input_tmp):
                os.remove(input_tmp)
        except Exception:
            pass
        return jsonify({"error": "GOOGLE_API_KEY not configured in environment."}), 500

    # Temporary output file inside tmp dir
    print("Creating temporary output file")
    out_tmp = make_tmp_file(suffix=".mp4")
    if not out_tmp:
        try:
            if os.path.exists(input_tmp):
                os.remove(input_tmp)
        except Exception:
            pass
        return jsonify({"error": "Failed to create temporary output file"}), 500

    print(f"Processing video with prompt: {user_prompt}")
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


@edit_bp.route("/trending_songs", methods=["GET"])
def trending_songs_list():
    """
    Returns the hardcoded list of trending songs metadata.
    Example response:
      { "songs": [ { id, title, artist, duration, public_url }, ... ] }
    """
    return jsonify({"songs": TRENDING_SONGS}), 200


@edit_bp.route("/add_music", methods=["POST"])
def add_music_to_video():
    """
    POST /api/add_music
    Form fields (multipart/form-data):
      - video: file blob (required)
      - song_id: optional; if provided, must match TRENDING_SONGS id
      - song_url: optional; direct publicly-accessible mp3 URL
      - music_start: optional float (seconds)
      - music_end: optional float (seconds)
      - music_volume: optional float (0.0-1.0)
      - loop: optional bool (string 'true'/'false')
    Returns edited video mp4 as attachment.
    """
    if "video" not in request.files:
        return jsonify({"error": "No 'video' file part"}), 400

    vid_file = request.files["video"]
    if vid_file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    safe_name = secure_filename(vid_file.filename)
    ext = ".mp4"
    if "." in safe_name:
        ext = "." + safe_name.rsplit(".", 1)[-1]

    input_tmp = make_tmp_file(suffix=ext)
    if not input_tmp:
        return jsonify({"error": "Failed to create temporary file for upload"}), 500

    try:
        vid_file.save(input_tmp)
    except Exception as e:
        try:
            if os.path.exists(input_tmp):
                os.remove(input_tmp)
        except Exception:
            pass
        return jsonify({"error": f"Failed to save uploaded file: {e}"}), 500

    # resolve song url
    song_id = request.form.get("song_id")
    song_url = request.form.get("song_url")
    if not song_url and song_id:
        match = next((s for s in TRENDING_SONGS if s["id"] == song_id), None)
        if match:
            song_url = match.get("public_url")

    if not song_url:
        # cleanup
        try:
            if os.path.exists(input_tmp):
                os.remove(input_tmp)
        except Exception:
            pass
        return jsonify({"error": "song_url or valid song_id must be provided"}), 400

    # optional params
    try:
        music_start = float(request.form.get("music_start")) if request.form.get("music_start") else 0.0
    except Exception:
        music_start = 0.0
    try:
        music_end = float(request.form.get("music_end")) if request.form.get("music_end") else None
    except Exception:
        music_end = None
    try:
        music_volume = float(request.form.get("music_volume")) if request.form.get("music_volume") else 0.4
    except Exception:
        music_volume = 0.4
    loop_str = request.form.get("loop", "true").lower()
    music_loop = loop_str in ("1", "true", "yes")

    # output tmp
    out_tmp = make_tmp_file(suffix=".mp4")
    if not out_tmp:
        try:
            if os.path.exists(input_tmp):
                os.remove(input_tmp)
        except Exception:
            pass
        return jsonify({"error": "Failed to create temporary output file"}), 500

    try:
        # mix_background_music accepts a music source path or URL. It will download if URL.
        mix_background_music(
            input_video=input_tmp,
            music_source_path=song_url,
            out_video=out_tmp,
            music_duration=None,
            music_volume=music_volume,
            loop=music_loop,
            music_start=music_start,
            music_end=music_end,
            reduce_original_volume=1.0,
            music_loop=music_loop,
            fade=1.0
        )
        # stream file back
        return send_file(out_tmp, as_attachment=True, download_name="edited_with_music.mp4", mimetype="video/mp4")
    except Exception as e:
        current_app.logger.exception("add_music failed")
        try:
            # try to provide a short error message
            return jsonify({"error": "add_music_failed", "detail": str(e)}), 500
        finally:
            try:
                if os.path.exists(input_tmp):
                    os.remove(input_tmp)
            except Exception:
                pass
    finally:
        # cleanup input file
        try:
            if os.path.exists(input_tmp):
                os.remove(input_tmp)
        except Exception:
            pass