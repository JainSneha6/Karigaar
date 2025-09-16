// src/components/SamplePromptsPill.jsx
import React from "react";

/**
 * SamplePromptsPill
 *
 * Props:
 * - prompts: string[] (list of sample prompt text)
 * - open: boolean (controlled expanded state)
 * - setOpen: fn(boolean) to toggle expanded state
 * - onUse(prompt: string) => void  (called when user clicks "Use")
 * - uploading: boolean (disable buttons while uploading)
 * - hidden: boolean (if true, component renders null)
 *
 * Renders a small, low-contrast pill in collapsed state and an expandable card when open.
 * Designed to be placed at the top-right (positioning left to the caller).
 */
export default function SamplePromptsPill({
    prompts = [],
    open = false,
    setOpen = () => { },
    onUse = () => { },
    uploading = false,
    hidden = false,
}) {
    if (hidden) return null;

    const toggle = () => setOpen(!open);

    return (
        <div
            aria-hidden={false}
            style={{
                zIndex: 55,
                width: open ? 340 : 182,
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
                    title="Sample prompts"
                    style={{
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "space-between",
                        gap: 8,
                        padding: "8px 12px",
                        borderRadius: 9999,
                        background: "rgba(255,255,255,0.85)",
                        border: "1px solid rgba(0,0,0,0.04)",
                        boxShadow: "0 6px 18px rgba(2,6,23,0.06)",
                        color: "#222",
                        fontSize: 13,
                        cursor: "pointer",
                        backdropFilter: "blur(4px)",
                        width: "100%",
                    }}
                >
                    <span style={{ display: "inline-flex", alignItems: "center", gap: 8 }}>
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" aria-hidden>
                            <path d="M3 6h18M3 12h18M3 18h18" stroke="#6b7280" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
                        </svg>
                        <span style={{ color: "#374151", fontWeight: 600 }}>Sample Prompts</span>
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
                        ?
                    </span>
                </button>
            ) : (
                <div
                    className="sample-prompts-card"
                    style={{
                        borderRadius: 14,
                        padding: 12,
                        boxShadow: "0 10px 30px rgba(2,6,23,0.06)",
                        border: "1px solid rgba(0,0,0,0.04)",
                        backdropFilter: "blur(6px)",
                        background: "rgba(255,255,255,0.96)",
                        width: "100%",
                    }}
                >
                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 8 }}>
                        <div style={{ fontSize: 14, fontWeight: 700, color: "#111827" }}>Sample prompts</div>
                        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                            <div style={{ fontSize: 12, color: "#6b7280" }}>Try these on your video</div>
                            <button
                                onClick={toggle}
                                aria-label="Close sample prompts"
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

                    <div style={{ display: "grid", gap: 8 }}>
                        {prompts.map((p, idx) => (
                            <div key={idx} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12 }}>
                                <div style={{ fontSize: 13, color: "#374151" }}>
                                    <span style={{ fontWeight: 600, marginRight: 8 }}>{idx + 1}.</span>
                                    <span style={{ opacity: 0.92 }}>{p}</span>
                                </div>
                                <div>
                                    <button
                                        onClick={() => onUse(p)}
                                        style={{
                                            padding: "6px 10px",
                                            borderRadius: 10,
                                            border: "1px solid rgba(99,102,241,0.12)",
                                            background: "linear-gradient(180deg, rgba(99,102,241,0.08), rgba(167,139,250,0.06))",
                                            color: "#6d28d9",
                                            fontWeight: 700,
                                            fontSize: 13,
                                            cursor: uploading ? "not-allowed" : "pointer",
                                            opacity: uploading ? 0.6 : 1,
                                        }}
                                        disabled={uploading}
                                    >
                                        Use
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}
