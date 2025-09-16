// src/components/SampleVideoDownloadPill.jsx
import React, { useState } from "react";

/**
 * SampleVideoDownloadPill
 *
 * Props:
 *  - driveDownloadUrl: string (direct-drive-download url, e.g. https://drive.google.com/uc?export=download&id=FILE_ID)
 *  - filename: optional desired filename for download (e.g. "sample.mp4")
 *  - hidden: boolean — hide the pill when true
 *
 * Behavior:
 *  - Collapsed: small pill (matches SamplePromptsPill collapsed styling)
 *  - Expanded: compact card with Download button (matches SamplePromptsPill open card styling)
 *  - Tries to fetch the URL and save as blob (better UX) — if fetch fails, opens the URL in new tab.
 */
export default function SampleVideoDownloadPill({
    driveDownloadUrl,
    filename = "sample_video.mp4",
    hidden = false,
}) {
    const [open, setOpen] = useState(false);
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState(null);

    if (hidden) return null;

    const toggle = () => {
        setError(null);
        setOpen((v) => !v);
    };

    async function tryDownload() {
        if (!driveDownloadUrl) {
            setError("No sample video URL configured.");
            return;
        }
        setBusy(true);
        setError(null);

        try {
            const res = await fetch(driveDownloadUrl, { method: "GET", mode: "cors" });
            if (!res.ok) {
                throw new Error(`HTTP ${res.status}`);
            }
            const blob = await res.blob();
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            a.remove();
            setTimeout(() => URL.revokeObjectURL(url), 5000);
            setBusy(false);
            setOpen(false);
        } catch (err) {
            setBusy(false);
            // Fallback: open in new tab for user to handle download (Drive CORS/redirects)
            window.open(driveDownloadUrl, "_blank", "noopener,noreferrer");
        }
    }

    return (
        <div
            aria-hidden={false}
            style={{
                zIndex: 55,
                width: open ? 340 : 182, // match SamplePromptsPill widths
                maxWidth: "92vw",
                transition: "width 220ms ease, opacity 180ms ease",
                opacity: 0.95,
                pointerEvents: "auto",
            }}
        >
            {!open ? (
                <button
                    onClick={toggle}
                    aria-expanded={open}
                    title="Sample video"
                    style={{
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "space-between", // match prompts pill collapsed layout
                        gap: 8,
                        padding: "8px 12px", // match prompts pill
                        borderRadius: 9999,
                        background: "rgba(255,255,255,0.85)",
                        border: "1px solid rgba(0,0,0,0.04)",
                        boxShadow: "0 6px 18px rgba(2,6,23,0.06)", // match prompts pill
                        color: "#222",
                        fontSize: 13,
                        cursor: "pointer",
                        backdropFilter: "blur(4px)",
                        width: "100%",
                    }}
                >
                    <span style={{ display: "inline-flex", alignItems: "center", gap: 8 }}>
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" aria-hidden>
                            {/* use a video-ish icon (three horizontal lines replaced with a play-like icon) */}
                            <path d="M5 3v18l14-9L5 3z" stroke="#6b7280" strokeWidth="0" fill="#6b7280" opacity="0.12" />
                            <path d="M5 3v18l14-9L5 3z" stroke="#6b7280" strokeWidth="0" fill="none" />
                            <path d="M9 7v10l8-5-8-5z" stroke="#6b7280" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" fill="none" />
                        </svg>
                        <span style={{ color: "#374151", fontWeight: 600 }}>Sample Video</span>
                    </span>

                    <span
                        style={{
                            display: "inline-flex",
                            alignItems: "center",
                            justifyContent: "center",
                            width: 30,
                            height: 30,
                            borderRadius: 8,
                            background: "#f3e8ff",
                            color: "#6d28d9",
                            fontWeight: 700,
                            fontSize: 13,
                        }}
                    >
                        ▶
                    </span>
                </button>
            ) : (
                <div
                    style={{
                        borderRadius: 14, // match prompts pill open card
                        padding: 12,
                        boxShadow: "0 10px 30px rgba(2,6,23,0.06)",
                        border: "1px solid rgba(0,0,0,0.04)",
                        backdropFilter: "blur(6px)",
                        background: "rgba(255,255,255,0.96)",
                        width: "100%",
                    }}
                >
                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 8 }}>
                        <div style={{ fontSize: 14, fontWeight: 700, color: "#111827" }}>Sample video</div>
                        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                            <div style={{ fontSize: 12, color: "#6b7280" }}>Use your own video or download a short clip to try editing</div>
                            <button
                                onClick={toggle}
                                aria-label="Close sample video"
                                style={{
                                    border: "none",
                                    background: "transparent",
                                    padding: 6,
                                    borderRadius: 8,
                                    cursor: "pointer",
                                }}
                            >
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                                    <path d="M6 6l12 12M18 6L6 18" stroke="#6b7280" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                                </svg>
                            </button>
                        </div>
                    </div>



                    {error && <div style={{ color: "#b91c1c", fontSize: 12, marginBottom: 8 }}>{error}</div>}

                    <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>
                        <button
                            onClick={tryDownload}
                            disabled={busy}
                            style={{
                                padding: "6px 10px",
                                borderRadius: 10,
                                border: "1px solid rgba(99,102,241,0.12)", // match prompts "Use" button border
                                background: busy
                                    ? "#e6e6e6"
                                    : "linear-gradient(180deg, rgba(99,102,241,0.08), rgba(167,139,250,0.06))", // match prompts subtle gradient
                                color: "#6d28d9",
                                fontWeight: 700,
                                fontSize: 13,
                                cursor: busy ? "not-allowed" : "pointer",
                                opacity: busy ? 0.7 : 1,
                            }}
                        >
                            {busy ? "Downloading..." : "Download"}
                        </button>

                    </div>
                </div>
            )}
        </div>
    );
}
