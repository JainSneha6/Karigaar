# routes/product_optimize_routes.py
import os
import json
import datetime
import uuid
import traceback
from flask import Blueprint, request, jsonify, current_app, send_from_directory
from werkzeug.utils import secure_filename

# Optional Gemini client helper (try import; code works if package present)
try:
    import google.generativeai as genai
except Exception:
    genai = None

product_bp = Blueprint("product_optimize", __name__)

# Environment / config
GEMINI_API_KEY = "AIzaSyAVSGUozgbc7AQs4xEhP_-xaTGtN78HBFU"
GEMINI_MODEL_NAME = os.environ.get("GEMINI_MODEL_NAME", "gemini-2.0-flash")

# Allowed image extensions
ALLOWED_EXT = {"png", "jpg", "jpeg", "webp", "gif"}


# ----------------- Helpers -----------------
def call_gemini_raw(prompt: str, api_key: str, model_name: str = "gemini-2.0-flash",
                    max_output_tokens: int = 512, temperature: float = 0.0) -> str:
    """
    Minimal wrapper for google.generativeai similar to your other code.
    Raises RuntimeError if genai is not available.
    """
    if genai is None:
        raise RuntimeError("google.generativeai package not installed. pip install google-generativeai")
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


def extract_json_from_text(text: str) -> dict:
    """
    Try to extract a JSON object from the model's text output.
    Returns dict on success, empty dict on failure.
    """
    if not text:
        return {}
    # Try to find the first top-level {...} block
    try:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            candidate = text[start:end + 1]
            return json.loads(candidate)
    except Exception:
        pass
    # Try parsing whole text as JSON
    try:
        return json.loads(text)
    except Exception:
        return {}


def allowed_file(filename: str) -> bool:
    ext = (filename.rsplit(".", 1)[-1] if "." in filename else "").lower()
    return ext in ALLOWED_EXT


def save_uploaded_images(files_list, product_images_dir):
    """
    Saves uploaded images. Returns list of saved filenames (secure) and any errors.
    """
    saved = []
    errors = []
    for f in files_list:
        if not f:
            continue
        filename = secure_filename(f.filename or "")
        if not filename:
            errors.append("empty_filename")
            continue
        if not allowed_file(filename):
            errors.append(f"unsupported_file_type:{filename}")
            continue
        # avoid collisions with uuid prefix
        unique_name = f"{uuid.uuid4().hex[:8]}-{filename}"
        out_path = os.path.join(product_images_dir, unique_name)
        try:
            f.save(out_path)
            saved.append(unique_name)
        except Exception as e:
            current_app.logger.exception("Failed saving uploaded image")
            errors.append(f"save_error:{filename}")
    return saved, errors


# ----------------- Routes -----------------

@product_bp.route("/product/optimize", methods=["POST"])
def optimize_product():
    """
    Accepts:
      - form fields: description (string), price (string/number), currency (opt)
      - files: images[] (multipart)
    Returns:
      - suggested_name
      - suggested_description
      - suggested_price (number)
      - seo_tags (array)
      - product_id and product_json_url
    """
    try:
        # Basic validation
        description = request.form.get("description", "").strip()
        price_raw = request.form.get("price", "").strip()
        currency = request.form.get("currency", "INR").strip()

        # parse price to float if possible
        suggested_price_hint = None
        try:
            if price_raw:
                suggested_price_hint = float(price_raw.replace(",", "").strip())
        except Exception:
            suggested_price_hint = None

        # Files
        images = request.files.getlist("images")
        # create product id
        product_id = datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S") + "-" + uuid.uuid4().hex[:6]
        uploads_root = os.path.join(current_app.root_path, "uploads", "products")
        product_dir = os.path.join(uploads_root, product_id)
        images_dir = os.path.join(product_dir, "images")
        os.makedirs(images_dir, exist_ok=True)

        # Save images
        saved_filenames, save_errors = save_uploaded_images(images, images_dir)

        # Build a simple "image captions" list for the prompt: just filenames
        image_references = []
        for fn in saved_filenames:
            # include filename and a hint for Gemini to "imagine" them
            image_references.append(fn)

        # Build prompt for Gemini (English requested)
        # We include the product description, price hint and image filenames (no raw pixels).
        prompt_lines = [
            "You are an expert e-commerce SEO copywriter and pricing analyst.",
            "Given the product description, current price, and images (filenames only), suggest:",
            "1) An SEO-optimized product title (short, 6-9 words) — 'suggested_name'",
            "2) An SEO-optimized product description (50-120 words) — 'suggested_description'. Use persuasive, clear, keyword-rich language suitable for product pages.",
            "3) A suggested_price (a numeric value) in the same currency, with a short 'price_reasoning' field describing why that price is recommended.",
            "4) A short list of 4-6 SEO tags or keywords — 'seo_tags'.",
            "Output STRICT JSON and nothing else. Use English. Fields: suggested_name (string), suggested_description (string), suggested_price (number), price_reasoning (string), seo_tags (array of strings).",
            "If price guidance is not possible, set suggested_price to null.",
            "",
            "Input data below:",
            f"Original description: '''{description}'''",
        ]
        if suggested_price_hint is not None:
            prompt_lines.append(f"Current price (approx): {suggested_price_hint} {currency}")
        else:
            prompt_lines.append("Current price: not provided")
        if image_references:
            prompt_lines.append(f"Image filenames: {', '.join(image_references)}")
            prompt_lines.append("Note: images are listed by filename only; infer visual style/usage from the filenames if helpful.")
        else:
            prompt_lines.append("No images provided.")
        prompt_lines.append("\nReturn only a single JSON object. Example schema: {\"suggested_name\":\"...\",\"suggested_description\":\"...\",\"suggested_price\":1234.5,\"price_reasoning\":\"...\",\"seo_tags\":[\"tag1\",\"tag2\"]}")
        prompt = "\n".join(prompt_lines)

        # Call Gemini if available
        gemini_result_text = ""
        parsed = {}
        if not GEMINI_API_KEY:
            current_app.logger.warning("GEMINI_API_KEY not set; cannot call Gemini")
        else:
            try:
                gemini_result_text = call_gemini_raw(prompt=prompt, api_key=GEMINI_API_KEY, model_name=GEMINI_MODEL_NAME, max_output_tokens=512, temperature=0.0)
                parsed = extract_json_from_text(gemini_result_text or "")
            except Exception:
                current_app.logger.exception("Gemini call failed")
                parsed = {}

        # If parsed empty, fallback heuristics
        suggested_name = ""
        suggested_description = ""
        suggested_price = None
        price_reasoning = ""
        seo_tags = []

        if parsed:
            suggested_name = parsed.get("suggested_name") or parsed.get("name") or ""
            suggested_description = parsed.get("suggested_description") or parsed.get("description") or ""
            # suggested_price might be string or number
            sp = parsed.get("suggested_price")
            try:
                suggested_price = float(sp) if (sp is not None and sp != "") else None
            except Exception:
                suggested_price = None
            price_reasoning = parsed.get("price_reasoning") or ""
            # ensure tags array
            st = parsed.get("seo_tags") or parsed.get("tags") or []
            if isinstance(st, str):
                # split by commas if it's a single string
                seo_tags = [t.strip() for t in st.split(",") if t.strip()]
            elif isinstance(st, list):
                seo_tags = [str(x).strip() for x in st if x]
        else:
            # fallback suggestion
            # name: first 4-6 words of description + "Handmade" / "Artisan" heuristic
            desc_words = [w for w in description.split() if w]
            suggested_name = " ".join(desc_words[:6]) + (" — Handmade" if desc_words else "Product")
            # suggested description: truncated original description (50-100 words)
            suggested_description = (" ".join(desc_words[:80]) + ("..." if len(desc_words) > 80 else "")).strip()
            # suggested price: use provided price hint or leave null
            suggested_price = suggested_price_hint
            price_reasoning = "No AI suggestions available; using provided price or leaving null."
            seo_tags = list({w.strip().lower() for w in (description.split()[:8] or []) if len(w) > 3})[:6]

        # Build the final object that we save and return
        final_obj = {
            "product_id": product_id,
            "original": {
                "description": description,
                "price": suggested_price_hint,
                "currency": currency,
                "uploaded_images": saved_filenames,
            },
            "optimized": {
                "suggested_name": suggested_name,
                "suggested_description": suggested_description,
                "suggested_price": suggested_price,
                "price_reasoning": price_reasoning,
                "seo_tags": seo_tags,
                # optionally attach raw gemini output for debugging
                "raw_gemini_text": gemini_result_text if gemini_result_text else None,
            },
            "created_at": datetime.datetime.utcnow().isoformat() + "Z",
        }

        # Save JSON to disk
        os.makedirs(product_dir, exist_ok=True)
        out_json_path = os.path.join(product_dir, "optimized.json")
        try:
            with open(out_json_path, "w", encoding="utf-8") as f:
                json.dump(final_obj, f, ensure_ascii=False, indent=2)
        except Exception:
            current_app.logger.exception("Failed to write optimized JSON")

        # Build image-accessible URLs based on current request (so frontend can show uploaded images)
        base = request.url_root.rstrip("/")
        image_urls = []
        for fn in saved_filenames:
            image_urls.append(f"{base}/api/product/image/{product_id}/{fn}")

        product_json_url = f"{base}/api/product/optimized/{product_id}"

        # Return payload
        response = {
            "product_id": product_id,
            "product_json_url": product_json_url,   # route to fetch the saved optimized JSON
            "suggested_name": suggested_name,
            "suggested_description": suggested_description,
            "suggested_price": suggested_price,
            "price_reasoning": price_reasoning,
            "seo_tags": seo_tags,
            "image_urls": image_urls,
        }
        if save_errors:
            response["image_save_errors"] = save_errors

        return jsonify(response), 200

    except Exception as exc:
        current_app.logger.exception("Unhandled exception in optimize_product")
        return jsonify({"error": "internal_server_error", "detail": str(exc), "trace": traceback.format_exc()}), 500


@product_bp.route("/product/optimized/<product_id>", methods=["GET"])
def serve_optimized_json(product_id):
    """
    Returns the saved optimized JSON for a product_id.
    """
    try:
        product_dir = os.path.join(current_app.root_path, "uploads", "products", product_id)
        json_path = os.path.join(product_dir, "optimized.json")
        if not os.path.exists(json_path):
            return jsonify({"error": "not_found"}), 404
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return jsonify(data)
    except Exception:
        current_app.logger.exception("Failed to read optimized JSON")
        return jsonify({"error": "failed_to_read"}), 500


@product_bp.route("/product/image/<product_id>/<filename>", methods=["GET"])
def serve_product_image(product_id, filename):
    """
    Serve uploaded product images saved under uploads/products/<product_id>/images/<filename>
    """
    try:
        safe_fn = secure_filename(filename)
        images_dir = os.path.join(current_app.root_path, "uploads", "products", product_id, "images")
        full_path = os.path.join(images_dir, safe_fn)
        if not os.path.exists(full_path):
            return jsonify({"error": "image_not_found"}), 404
        return send_from_directory(images_dir, safe_fn)
    except Exception:
        current_app.logger.exception("Failed to serve product image")
        return jsonify({"error": "failed_to_serve"}), 500
