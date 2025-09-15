from typing import List, Dict, Any, Optional


from .ffmpeg_utils import run_cmd
from .sticker_helpers import DEFAULT_STICKER_DIRS,ensure_dirs_exist,find_or_fetch_sticker_image_for_emoji,resolve_image_path

def escape_drawtext_text(t: str) -> str:
    t = t.replace("\\", "\\\\")
    t = t.replace("'", "\\'")
    return t


def build_drawtext_filter(emoji: str, start: float, end: float, position: str = "bottom-right",
                          x: Optional[int] = None, y: Optional[int] = None, fontsize: int = 72) -> str:
    txt = escape_drawtext_text(emoji)
    if x is not None and y is not None:
        x_expr = str(x)
        y_expr = str(y)
    else:
        if position == "top-left":
            x_expr = "10"
            y_expr = "10"
        elif position == "top-right":
            x_expr = "w-tw-10"
            y_expr = "10"
        elif position == "bottom-left":
            x_expr = "10"
            y_expr = "h-th-10"
        elif position == "center":
            x_expr = "(w-tw)/2"
            y_expr = "(h-th)/2"
        else:
            x_expr = "w-tw-10"
            y_expr = "h-th-10"
    enable_expr = f"between(t,{start:.3f},{end:.3f})"
    filter_str = f"drawtext=text='{txt}':fontsize={fontsize}:x={x_expr}:y={y_expr}:enable='{enable_expr}':box=1:boxborderw=10:boxcolor=black@0.3"
    return filter_str


def apply_stickers_to_video(input_video: str, stickers: List[Dict[str, Any]], out_video: str,
                            sticker_dirs: Optional[List[str]] = None):
    if not stickers:
        run_cmd(["ffmpeg", "-y", "-i", input_video, "-c", "copy", out_video])
        return
    if sticker_dirs is None:
        sticker_dirs = DEFAULT_STICKER_DIRS
    ensure_dirs_exist(sticker_dirs)

    # Resolve emoji -> image first
    resolved_image_stickers = []
    unresolved_drawtext_stickers = []

    for s in stickers:
        content = s.get("content", {}) or {}
        if isinstance(content, dict) and "emoji" in content and "image" not in content:
            img_path = find_or_fetch_sticker_image_for_emoji(content.get("emoji"), sticker_dirs)
            if img_path:
                s["content"] = {"image": img_path}

    for s in stickers:
        content = s.get("content", {}) or {}
        if isinstance(content, dict) and "image" in content:
            resolved = resolve_image_path(content["image"], sticker_dirs=sticker_dirs)
            if resolved:
                s["content"]["image"] = resolved
                resolved_image_stickers.append(s)
            else:
                unresolved_drawtext_stickers.append(s)
        else:
            unresolved_drawtext_stickers.append(s)

    if not resolved_image_stickers:
        vf_parts = []
        for s in unresolved_drawtext_stickers:
            content = s.get("content", {}) or {}
            text = ""
            if isinstance(content, dict):
                text = content.get("text") or content.get("emoji") or ""
            elif isinstance(content, str):
                text = content
            pos = s.get("position", "bottom-right")
            vf_parts.append(build_drawtext_filter(text, s["start"], s["end"], pos, s.get("x"), s.get("y"), s.get("fontsize", 72)))
        vf = ",".join(vf_parts) if vf_parts else None
        if vf:
            cmd = [
                "ffmpeg", "-y",
                "-i", input_video,
                "-vf", vf,
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
                "-c:a", "aac", "-b:a", "128k",
                out_video
            ]
        else:
            cmd = ["ffmpeg", "-y", "-i", input_video, "-c", "copy", out_video]
        run_cmd(cmd)
        return

    # Build ffmpeg with multiple -i inputs and overlay chain
    cmd = ["ffmpeg", "-y", "-i", input_video]
    image_inputs = []
    for s in resolved_image_stickers:
        img = s["content"]["image"]
        cmd += ["-i", img]
        image_inputs.append((s, img))

    filter_parts = []
    last_label = "[0:v]"
    input_idx = 1
    for (s, img) in image_inputs:
        start = s["start"]
        end = s["end"]
        pos = s.get("position", "bottom-right")
        x = s.get("x")
        y = s.get("y")
        if x is not None and y is not None:
            x_expr = str(x); y_expr = str(y)
        else:
            if pos == "top-left":
                x_expr = "10"; y_expr = "10"
            elif pos == "top-right":
                x_expr = "main_w-overlay_w-10"; y_expr = "10"
            elif pos == "bottom-left":
                x_expr = "10"; y_expr = "main_h-overlay_h-10"
            elif pos == "center":
                x_expr = "(main_w-overlay_w)/2"; y_expr = "(main_h-overlay_h)/2"
            else:
                x_expr = "main_w-overlay_w-10"; y_expr = "main_h-overlay_h-10"
        enable_expr = f"between(t,{start:.3f},{end:.3f})"
        in_label = f"[{input_idx}:v]"
        out_label = f"[v{input_idx}]"
        filter_parts.append(f"{last_label}{in_label}overlay={x_expr}:{y_expr}:enable='{enable_expr}'{out_label}")
        last_label = out_label
        input_idx += 1

    # drawtext for unresolved
    if unresolved_drawtext_stickers:
        draw_parts = []
        for s in unresolved_drawtext_stickers:
            content = s.get("content", {}) or {}
            text = ""
            if isinstance(content, dict):
                text = content.get("text") or content.get("emoji") or ""
            elif isinstance(content, str):
                text = content
            pos = s.get("position", "bottom-right")
            fontsize = s.get("fontsize", 72)
            if s.get("x") is not None and s.get("y") is not None:
                x_expr = str(s.get("x")); y_expr = str(s.get("y"))
            else:
                if pos == "top-left":
                    x_expr = "10"; y_expr = "10"
                elif pos == "top-right":
                    x_expr = "w-tw-10"; y_expr = "10"
                elif pos == "bottom-left":
                    x_expr = "10"; y_expr = "h-th-10"
                elif pos == "center":
                    x_expr = "(w-tw)/2"; y_expr = "(h-th)/2"
                else:
                    x_expr = "w-tw-10"; y_expr = "h-th-10"
            enable_expr = f"between(t,{s['start']:.3f},{s['end']:.3f})"
            txt = escape_drawtext_text(text)
            draw_parts.append(f"drawtext=text='{txt}':fontsize={fontsize}:x={x_expr}:y={y_expr}:enable='{enable_expr}':box=1:boxborderw=10:boxcolor=black@0.3")
        draw_chain = ",".join(draw_parts)
        if filter_parts:
            filter_complex = ";".join(filter_parts) + ";" + f"{last_label}{draw_chain}[vout]"
        else:
            filter_complex = f"{last_label}{draw_chain}[vout]"
        final_label = "[vout]"
    else:
        filter_complex = ";".join(filter_parts) if filter_parts else ""
        final_label = last_label

    full_cmd = cmd + ["-filter_complex", filter_complex, "-map", final_label, "-map", "0:a?", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-c:a", "aac", "-b:a", "128k", out_video]
    run_cmd(full_cmd)
