from flask import Flask
from .routes.edit_routes import edit_bp
from .routes.converse_routes import conv_bp
from .routes.product_optimize_routes import product_bp
import os
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    # config: optional
    app.config.from_mapping({
    "MAX_CONTENT_LENGTH": 1024 * 1024 * 1024, # 1GB max upload by default
    "UPLOAD_FOLDER": os.path.join("/tmp", "uploads"), 
    })

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    
    ffmpeg_bin_dir = "/tmp/bin"
    os.makedirs(ffmpeg_bin_dir, exist_ok=True)
    os.environ["PATH"] = ffmpeg_bin_dir + ":" + os.environ.get("PATH", "")

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