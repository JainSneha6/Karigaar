import React, { useState, useRef, useEffect } from "react";
import axios from "axios";
import MenuDrawer from "../components/MenuDrawer";
import FloatingBackgroundBlobs from "../components/FloatingBackgroundBlobs";
import HamburgerMenu from "../components/Hamburger";
import VideoPlayer from "../components/VideoPlayer";
import FloatingFAB from "../components/FloatingFAB";
import BottomSheet from "../components/BottomSheet";

export default function MobileVideoEditor() {
  // --- State ---
  const [messages, setMessages] = useState([]);
  const [conversationState, setConversationState] = useState("upload_video");
  const [history, setHistory] = useState([]); // { blob, url }
  const [promptHistory, setPromptHistory] = useState([]);
  const [listening, setListening] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);
  const [inputText, setInputText] = useState("");
  const [sheetOpen, setSheetOpen] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);

  const recognitionRef = useRef(null);
  const audioRef = useRef(null);

  // --- Speech Recognition ---
  useEffect(() => {
    if ("SpeechRecognition" in window || "webkitSpeechRecognition" in window) {
      const SpeechRecognition =
        window.SpeechRecognition || window.webkitSpeechRecognition;
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
      const res = await axios.post("http://localhost:5000/api/tts", { text });
      return res.data; // expects { audio_base64, mime }
    } catch (err) {
      console.error("TTS request failed", err);
      setError(
        "TTS request failed: " + (err?.response?.data?.error || err.message)
      );
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
        addAIMessage(
          "Please specify: more edits, restore previous version, or done?"
        );
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
      fullPrompt = `Previous edits: ${promptHistory.join(
        ". "
      )}. Additional edit: ${prompt}`;
    }

    const formData = new FormData();
    formData.append("video", current.blob);
    formData.append("user_prompt", fullPrompt);

    try {
      const response = await fetch("http://localhost:5000/api/edit", {
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
      addAIMessage(
        "Edit complete. Continue editing, restore previous version, or finish?"
      );
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
      document.getElementById("mobile-upload").click();
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
        } catch (e) {}
        return prev.slice(0, -1);
      });
      setPromptHistory((prev) => prev.slice(0, -1));
      addAIMessage(
        "Previous version restored. What would you like to edit next?"
      );
      setConversationState("get_prompt");
    }
  };

  const current = history[history.length - 1] || null;

  // --- UI ---
  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-100 via-blue-50 to-pink-100 overflow-hidden relative">
      <FloatingBackgroundBlobs />
      <HamburgerMenu onClick={() => setMenuOpen(true)} />
      <VideoPlayer current={current} handleFileChange={handleFileChange} />
      <FloatingFAB onClick={openSheetForPrompt} />
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
    </div>
  );
}
