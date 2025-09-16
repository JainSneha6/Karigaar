// File: src/pages/MobileVideoEditor.jsx
import React, { useState, useRef, useEffect, useMemo } from "react";
import axios from "axios";
import MenuDrawer from "../components/MenuDrawer";
import FloatingBackgroundBlobs from "../components/FloatingBackgroundBlobs";
import HamburgerMenu from "../components/Hamburger";
import VideoPlayer from "../components/VideoPlayer";
import FloatingFAB from "../components/FloatingFAB";
import BottomSheet from "../components/BottomSheet";
import SongsSheet from "../components/SongsSheet";
import SamplePromptsPill from "../components/SamplePromptsPill";
import SampleVideoDownloadPill from "../components/SampleVideoDownloadPill";


/**
 * MobileVideoEditor (with Trending Songs + Subtle Collapsible Sample Prompts)
 *
 * - Sample prompts are collapsed into a small, low-contrast pill in the top-right.
 * - Click the pill to expand. The card is hidden while assistant/songs sheets are open.
 * - 'Use' still fills the assistant input and opens the assistant sheet.
 */

export default function MobileVideoEditor() {
  // --- State ---
  const [messages, setMessages] = useState([]);
  const [conversationState, setConversationState] = useState("upload_video");
  const [history, setHistory] = useState([]); // { blob, url }
  const [promptHistory, setPromptHistory] = useState([]);
  const [listening, setListening] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [addingSong, setAddingSong] = useState(false);
  const [addingSongTitle, setAddingSongTitle] = useState(null);
  const [error, setError] = useState(null);
  const [inputText, setInputText] = useState("");
  const [sheetOpen, setSheetOpen] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);

  // trending songs modal
  const [trendingOpen, setTrendingOpen] = useState(false);
  const [availableTrending, setAvailableTrending] = useState([]); // displayed 5-6 songs

  // sample prompts collapsed state
  const [promptsOpen, setPromptsOpen] = useState(false);

  const recognitionRef = useRef(null);
  const audioRef = useRef(null);

  // --- Hardcoded trending songs (frontend copy)
  const HARDCODED_TRENDING = useMemo(
    () => [
      { id: "s1", title: "Sahiba", artist: "Aditya Rikhari", duration: 30, public_url: "https://drive.google.com/uc?export=download&id=1u5k0HPhka_ytUGLt6eyn3awVM3oYSS6b" },
      { id: "s2", title: "Saiyaara", artist: "Tanishk Bagchi", duration: 28, public_url: "https://drive.google.com/uc?export=download&id=1CaPk8_CvQdH1FUZiEGVkjpbAff3FMaEz" },
      { id: "s3", title: "Dard", artist: "Kushagra", duration: 32, public_url: "https://drive.google.com/uc?export=download&id=1fLXKnSdCmNYztsPTQf6S7Xxbnanw4M5E" },
      { id: "s4", title: "Kaanamale", artist: "Mugen Rao", duration: 25, public_url: "https://drive.google.com/uc?export=download&id=1MixJI_YU5S2ORKfrQamOs-TbrmpTZi4m" },
      { id: "s5", title: "Pardesiya", artist: "Sachin-Jigar", duration: 29, public_url: "https://drive.google.com/uc?export=download&id=1GC0zEcPp-TYMbCpr-p1u-zaHHsGB_Uuy" },
      { id: "s6", title: "Noormahal", artist: "Chani Nattan", duration: 27, public_url: "https://drive.google.com/uc?export=download&id=1XtSSZOeaH1Uu8oBmDKzbFQXxl0EiDe5V" },
      { id: "s7", title: "The Night We Met", artist: "Lord Huron", duration: 30, public_url: "https://drive.google.com/uc?export=download&id=1cz0o_si2oIaWKu5a3rgERbWoOCW5r9aS" },
      { id: "s8", title: "Yaarum Sollala", artist: "Shreyas Narasimhan", duration: 31, public_url: "https://drive.google.com/uc?export=download&id=1JyncQt2piEU-0VdVCywpYPeGn0fJpID2" },
      { id: "s9", title: "Sapphire", artist: "Ed Sheeran", duration: 26, public_url: "https://drive.google.com/uc?export=download&id=16jpFu95nzQy-vAky1U_h0UIsg0gGToPR" },
    ],
    []
  );

  // --- Sample prompts to display (the content the user requested) ---
  const SAMPLE_PROMPTS = [
    "Cut the first 10 seconds of the video",
    "Make the video into 2x",
    "Add a thumbs up emoji at 10s",
  ];

  // --- Speech Recognition ---
  useEffect(() => {
    if ("SpeechRecognition" in window || "webkitSpeechRecognition" in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = false;
      recognitionRef.current.onresult = (event) => {
        const transcript = event.results[0][0].transcript.trim();
        setListening(false);
        handleUserInput(transcript);
      };
      recognitionRef.current.onend = () => setListening(false);
      recognitionRef.current.onerror = (e) => {
        setError(`Speech recognition error: ${e.message}`);
        setListening(false);
      };
    }

    if (conversationState === "upload_video") {
      addAIMessage("Tap to upload a video to begin editing.");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [conversationState]);

  // --- TTS ---
  async function playBase64Audio(base64, mime = "audio/mpeg") {
    if (!base64) return;
    const byteString = atob(base64);
    const ab = new ArrayBuffer(byteString.length);
    const ia = new Uint8Array(ab);
    for (let i = 0; i < byteString.length; i += 1)
      ia[i] = byteString.charCodeAt(i);
    const blob = new Blob([ab], { type: mime });
    const url = URL.createObjectURL(blob);
    const audio = audioRef.current;
    if (!audio) return;
    audio.src = url;
    try {
      await audio.play();
    } catch (err) {
      console.warn("Playback blocked or failed:", err);
    }
  }

  async function requestServerTTS(text) {
    try {
      const res = await axios.post("https://karigaar-xhml.vercel.app/api/tts", { text });
      return res.data; // expects { audio_base64, mime }
    } catch (err) {
      console.error("TTS request failed", err);
      setError("TTS request failed: " + (err?.response?.data?.error || err.message));
      return null;
    }
  }

  async function addAIMessage(text) {
    if (!text) return;
    let shouldAdd = true;
    setMessages((prev) => {
      const last = prev[prev.length - 1];
      if (last && last.role === "ai" && last.content.trim() === text.trim()) {
        shouldAdd = false;
        return prev;
      }
      return [...prev, { role: "ai", content: text }];
    });

    if (!shouldAdd) return;

    try {
      const tts = await requestServerTTS(text);
      if (tts && tts.audio_base64) {
        await playBase64Audio(tts.audio_base64, tts.mime || "audio/mpeg");
      }
    } catch (e) {
      console.error("addAIMessage: TTS/playback failed", e);
    }
  }

  const addUserMessage = (text) => {
    if (!text) return;
    setMessages((prev) => [...prev, { role: "user", content: text }]);
  };

  const startListening = () => {
    if (recognitionRef.current && !listening) {
      setListening(true);
      recognitionRef.current.start();
    }
  };

  // --- File Upload ---
  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      const url = URL.createObjectURL(file);
      setHistory([{ blob: file, url }]);
      setPromptHistory([]);
      addUserMessage("Video uploaded");
      addAIMessage("Describe the edits you would like to make");
      setConversationState("get_prompt");
    }
  };

  // --- User Input Flow ---
  const handleUserInput = (transcript) => {
    addUserMessage(transcript);
    if (conversationState === "get_prompt") {
      submitEdit(transcript);
    } else if (conversationState === "review") {
      const lower = transcript.toLowerCase();
      if (lower.includes("restore")) {
        restorePrevious();
      } else if (
        lower.includes("edit") ||
        lower.includes("change") ||
        lower.includes("more") ||
        lower.includes("yes")
      ) {
        addAIMessage("What additional edits would you like?");
        setConversationState("get_prompt");
      } else if (lower.includes("done") || lower.includes("no")) {
        addAIMessage("Session complete. Upload a new video to continue.");
        setConversationState("upload_video");
        setHistory([]);
        setPromptHistory([]);
        setMessages([]);
      } else {
        addAIMessage("Please specify: more edits, restore previous version, or done?");
      }
    }
  };

  const submitEdit = async (prompt) => {
    const current = history[history.length - 1];
    if (!current) return;

    setUploading(true);
    setError(null);

    let fullPrompt = prompt;
    if (promptHistory.length > 0) {
      fullPrompt = `Previous edits: ${promptHistory.join(". ")}. Additional edit: ${prompt}`;
    }

    const formData = new FormData();
    formData.append("video", current.blob, current.blob.name || "video.mp4");
    formData.append("user_prompt", fullPrompt);

    try {
      const response = await fetch("https://karigaar-xhml.vercel.app/api/edit", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || "Processing failed");
      }

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      setHistory((prev) => [...prev, { blob, url }]);
      setPromptHistory((prev) => [...prev, prompt]);
      addAIMessage("Edit complete. Continue editing, restore previous version, or finish?");
      setConversationState("review");
      setSheetOpen(false);
    } catch (err) {
      console.error(err);
      setError(err.message);
    } finally {
      setUploading(false);
    }
  };

  const handleTextSubmit = () => {
    if (inputText.trim()) {
      handleUserInput(inputText.trim());
      setInputText("");
    }
  };

  const openSheetForPrompt = () => {
    if (!history[history.length - 1]) {
      document.getElementById("mobile-upload")?.click();
      return;
    }
    setSheetOpen(true);
  };

  const restorePrevious = () => {
    if (history.length > 1) {
      setHistory((prev) => {
        const removed = prev[prev.length - 1];
        try {
          URL.revokeObjectURL(removed.url);
        } catch (e) { }
        return prev.slice(0, -1);
      });
      setPromptHistory((prev) => prev.slice(0, -1));
      addAIMessage("Previous version restored. What would you like to edit next?");
      setConversationState("get_prompt");
    }
  };

  const current = history[history.length - 1] || null;

  // --- Trending songs logic (frontend randomize 5-6)
  const pickRandomSubset = (arr, count) => {
    const copy = arr.slice();
    for (let i = copy.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [copy[i], copy[j]] = [copy[j], copy[i]];
    }
    return copy.slice(0, count);
  };

  useEffect(() => {
    // On open trending modal, pick a subset
    if (trendingOpen) {
      const subset = pickRandomSubset(HARDCODED_TRENDING, Math.floor(5 + Math.random() * 2)); // 5-6
      setAvailableTrending(subset);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [trendingOpen]);

  // --- Add song to video (uploads current video blob + song_url to backend) ---
  const addSongToCurrentVideo = async (song) => {
    if (!current || !current.blob) {
      setError("No video loaded");
      return;
    }

    // mark adding song state so the overlay can show a helpful label
    setAddingSong(true);
    setAddingSongTitle(song?.title || null);
    setUploading(true);
    setError(null);
    try {
      const formData = new FormData();
      formData.append("video", current.blob, current.blob.name || "video.mp4");
      formData.append("song_url", song.public_url);
      const res = await fetch("https://karigaar-xhml.vercel.app/api/add_music", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.error || `Add music failed (${res.status})`);
      }

      const outBlob = await res.blob();
      const url = URL.createObjectURL(outBlob);
      setHistory((prev) => [...prev, { blob: outBlob, url }]);
      setPromptHistory((prev) => [...prev, `Added song: ${song.title} — ${song.artist}`]);
      addAIMessage(`Added "${song.title}" to the video. Continue editing or finish.`);
      setTrendingOpen(false);
      setConversationState("review");
    } catch (err) {
      console.error("addSongToCurrentVideo:", err);
      setError(err.message);
    } finally {
      setAddingSong(false);
      setAddingSongTitle(null);
      setUploading(false);
    }
  };

  // --- helper: use sample prompt (fills input & opens assistant sheet) ---
  const useSamplePrompt = (prompt) => {
    if (!current) {
      document.getElementById("mobile-upload")?.click();
      return;
    }
    setInputText(prompt);
    setSheetOpen(true);
  };

  // Toggle collapsed/expanded prompts pill
  const togglePrompts = () => setPromptsOpen((v) => !v);

  // close prompts when sheets open for clean UX
  useEffect(() => {
    if (sheetOpen || trendingOpen) setPromptsOpen(false);
  }, [sheetOpen, trendingOpen]);

  // --- UI ---
  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-100 via-blue-50 to-pink-100 overflow-hidden relative">
      <FloatingBackgroundBlobs />
      <HamburgerMenu onClick={() => setMenuOpen(true)} />

      {/* Wrap the VideoPlayer in a relative container so we can place an absolute overlay on top */}
      <div className="relative max-w-3xl mx-auto">
        <VideoPlayer current={current} handleFileChange={handleFileChange} />

        {/* Loading overlay: shows when either an edit is processing or a song is being added */}
        {uploading && current && (
          <div
            role="status"
            aria-live="polite"
            className="absolute top-80 inset-0 z-60 flex items-center justify-center bg-black/40 backdrop-blur-sm pointer-events-auto rounded-lg"
          >
            {/* Big animated spinner only (no text) */}
            <div className="flex items-center justify-center">
              <div className="w-28 h-28 rounded-full border-8 border-white/20 border-t-white animate-spin" aria-hidden="true" />
              <span className="sr-only">Processing</span>
            </div>
          </div>
        )}
      </div>

      {!sheetOpen && !trendingOpen && (
        <div style={{
          position: "fixed",
          top: 16,
          right: 16,
          zIndex: 55,
        }}>
          <div>
            <SamplePromptsPill
              prompts={[
                "Cut the first 10 seconds of the video",
                "Make the video into 2x",
                "Add a thumbs up emoji at 10s"
              ]}
              open={promptsOpen}
              setOpen={setPromptsOpen}
              onUse={(p) => {
                if (!current) {
                  document.getElementById("mobile-upload")?.click();
                  return;
                }
                setInputText(p);
                setSheetOpen(true);
              }}
              uploading={uploading}
              hidden={false}
            />
          </div>

          <div style={{ marginTop: 12 }}>
            <SampleVideoDownloadPill
              driveDownloadUrl={"https://drive.google.com/uc?export=download&id=1g3HGMPmRNKMCbPeV1xlo5XFUZDfyRIvs"}
              filename={"sample_video.mp4"}
            />
          </div>
        </div>
      )}


      {/* FABs: assistant (open prompt sheet) + songs (open songs sheet) placed side-by-side */}
      <FloatingFAB
        onAssistantClick={openSheetForPrompt}
        onSongsClick={() => {
          if (!current) {
            document.getElementById("mobile-upload")?.click();
            return;
          }
          setTrendingOpen(true);
        }}
      />

      <BottomSheet
        sheetOpen={sheetOpen}
        setSheetOpen={setSheetOpen}
        history={history}
        messages={messages}
        listening={listening}
        inputText={inputText}
        setInputText={setInputText}
        uploading={uploading}
        promptHistory={promptHistory}
        error={error}
        restorePrevious={restorePrevious}
        handleTextSubmit={handleTextSubmit}
        startListening={startListening}
        recognitionRef={recognitionRef}
        audioRef={audioRef}
      />

      <MenuDrawer open={menuOpen} onClose={() => setMenuOpen(false)} />

      <SongsSheet
        sheetOpen={trendingOpen}
        setSheetOpen={setTrendingOpen}
        availableTrending={availableTrending}
        onShuffle={() => {
          const subset = pickRandomSubset(HARDCODED_TRENDING, Math.floor(5 + Math.random() * 2));
          setAvailableTrending(subset);
        }}
        onLoadFromServer={() => {
          fetch("/api/trending_songs")
            .then((r) => r.json())
            .then((d) => {
              const subset = pickRandomSubset(d.songs || [], Math.floor(5 + Math.random() * 2));
              setAvailableTrending(subset);
            })
            .catch((e) => {
              console.warn("fetch trending songs failed", e);
            });
        }}
        addSongToCurrentVideo={addSongToCurrentVideo}
        uploading={uploading}
        error={error}
      />

      {/* audio element for TTS playback */}
      <audio ref={audioRef} hidden />
    </div>
  );
}


