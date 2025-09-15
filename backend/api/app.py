from flask import Flask
from .routes.edit_routes import edit_bp
from .routes.converse_routes import conv_bp
from .routes.product_optimize_routes import product_bp
import os
from flask_cors import CORS
from api.video_edit import ffmpeg_utils

def create_app():
    app = Flask(__name__)
    
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    app.config.from_mapping({
        "MAX_CONTENT_LENGTH": 1024 * 1024 * 1024, # 1GB max upload
        "UPLOAD_FOLDER": os.path.join("/tmp", "uploads"), 
    })

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # Ensure ffmpeg/ffprobe binaries exist at startup
    ffmpeg_path = ffmpeg_utils._find_executable("ffmpeg")
    ffprobe_path = ffmpeg_utils._find_executable("ffprobe")
    print("ffmpeg path:", ffmpeg_path)
    print("ffprobe path:", ffprobe_path)

    # Register blueprints
    app.register_blueprint(edit_bp, url_prefix="/api")
    app.register_blueprint(conv_bp, url_prefix="/api")
    app.register_blueprint(product_bp, url_prefix="/api")

    @app.route("/", methods=["GET"])
    def idx():
        return "Flask Video Editor API. Use POST /api/edit to upload video and user_prompt."
    
    return app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
