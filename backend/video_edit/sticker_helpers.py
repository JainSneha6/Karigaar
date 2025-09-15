import os
import tempfile
import re
import unicodedata
import urllib.request
import urllib.parse
from typing import List, Optional


DEFAULT_STICKER_DIRS = ["./stickers"]
for dd in DEFAULT_STICKER_DIRS:
    try:
        os.makedirs(dd, exist_ok=True)
    except Exception:
        pass


def ensure_dirs_exist(dirs: List[str]):
    for d in dirs:
        try:
            os.makedirs(d, exist_ok=True)
        except Exception:
            pass


def emoji_to_codepoints(emoji: str) -> str:
    return "".join(f"{ord(ch):x}" for ch in emoji)


def safe_unicodedata_name(ch: str) -> Optional[str]:
    try:
        return unicodedata.name(ch)
    except Exception:
        return None


def find_local_sticker_for_emoji(emoji: str, search_dirs: Optional[List[str]] = None) -> Optional[str]:
    if search_dirs is None:
        search_dirs = DEFAULT_STICKER_DIRS
    code = emoji_to_codepoints(emoji)
    name = safe_unicodedata_name(emoji) or ""
    name_lower = name.lower().replace(" ", "_")
    ensure_dirs_exist(search_dirs)
    for d in search_dirs:
        if not os.path.isdir(d):
            continue
        for fname in os.listdir(d):
            lf = fname.lower()
            full = os.path.join(d, fname)
            if not os.path.isfile(full):
                continue
            if lf.endswith((".png", ".webp", ".jpg", ".jpeg")):
                base = lf.rsplit(".", 1)[0]
                if base == code:
                    return full
                if code in base:
                    return full
                if name_lower and name_lower in base:
                    return full
                if name_lower:
                    parts = name_lower.split("_")
                    for p in parts:
                        if p and p in base:
                            return full
                if emoji in fname:
                    return full
    return None


def download_twemoji_png_for_emoji(emoji: str, size: int = 72, out_dir: Optional[str] = None) -> Optional[str]:
    if out_dir is None:
        out_dir = os.path.join(tempfile.gettempdir(), "twemoji_cache")
    os.makedirs(out_dir, exist_ok=True)
    code = emoji_to_codepoints(emoji)
    url = f"https://github.com/twitter/twemoji/raw/master/assets/{size}x{size}/{code}.png"
    out_path = os.path.join(out_dir, f"{code}.png")
    if os.path.isfile(out_path):
        return out_path
    try:
        urllib.request.urlretrieve(url, out_path)
        if os.path.getsize(out_path) > 0:
            return out_path
    except Exception:
        try:
            if os.path.isfile(out_path):
                os.remove(out_path)
        except Exception:
            pass
    return None


def find_or_fetch_sticker_image_for_emoji(emoji: str, sticker_dirs: Optional[List[str]] = None) -> Optional[str]:
    path = find_local_sticker_for_emoji(emoji, search_dirs=sticker_dirs)
    if path:
        return path
    tw = download_twemoji_png_for_emoji(emoji, size=72)
    return tw


def resolve_image_path(image_ref: str, sticker_dirs: Optional[List[str]] = None) -> Optional[str]:
    if not image_ref:
        return None
    if os.path.isfile(image_ref):
        return os.path.abspath(image_ref)
    parsed = urllib.parse.urlparse(image_ref)
    if parsed.scheme in ("http", "https"):
        fd, tmp = tempfile.mkstemp(suffix=os.path.splitext(parsed.path)[1] or ".png")
        os.close(fd)
        try:
            urllib.request.urlretrieve(image_ref, tmp)
            if os.path.getsize(tmp) > 0:
                return tmp
            os.remove(tmp)
        except Exception:
            try:
                os.remove(tmp)
            except Exception:
                pass
        return None
    # token search
    basename = os.path.basename(image_ref)
    base_no_ext = os.path.splitext(basename)[0]
    found = find_local_sticker_by_name(base_no_ext, search_dirs=sticker_dirs) if 'find_local_sticker_by_name' in globals() else None
    if found:
        return found
    parts = re.findall(r"[a-z0-9]+", base_no_ext.lower())
    if parts:
        joined = "".join(parts)
        if sticker_dirs is None:
            sticker_dirs = DEFAULT_STICKER_DIRS
        ensure_dirs_exist(sticker_dirs)
        for d in sticker_dirs:
            if not os.path.isdir(d):
                continue
            for fname in os.listdir(d):
                lf = fname.lower()
                if not lf.endswith((".png", ".webp", ".jpg", ".jpeg")):
                    continue
                base = lf.rsplit('.', 1)[0]
                compact = re.sub(r"[^a-z0-9]", "", base)
                if joined in compact:
                    return os.path.join(d, fname)
    return None


def find_local_sticker_by_name(name: str, search_dirs: Optional[List[str]] = None) -> Optional[str]:
    if not name:
        return None
    if search_dirs is None:
        search_dirs = DEFAULT_STICKER_DIRS
    ensure_dirs_exist(search_dirs)
    tokens = re.findall(r"[a-z0-9]+", name.lower())
    if not tokens:
        return None
    joined = "".join(tokens)
    for d in search_dirs:
        if not os.path.isdir(d):
            continue
        for fname in os.listdir(d):
            full = os.path.join(d, fname)
            if not os.path.isfile(full):
                continue
            lf = fname.lower()
            if not lf.endswith((".png", ".webp", ".jpg", ".jpeg")):
                continue
            base = lf.rsplit('.', 1)[0]
            if all(token in base for token in tokens):
                return full
            compact = re.sub(r"[^a-z0-9]", "", base)
            if joined and joined in compact:
                return full
    return None