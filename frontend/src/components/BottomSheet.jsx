import React from "react";
import { Mic, MicOff, Send, X } from "lucide-react";

export default function BottomSheet({
  sheetOpen,
  setSheetOpen,
  history,
  messages,
  listening,
  inputText,
  setInputText,
  uploading,
  promptHistory,
  error,
  restorePrevious,
  handleTextSubmit,
  startListening,
  recognitionRef,
  audioRef,
}) {
  return (
    <div
      className={`fixed left-0 right-0 bottom-0 z-50 transition-transform duration-300 ${
        sheetOpen ? "translate-y-0" : "translate-y-full"
      }`}
      aria-hidden={!sheetOpen}
    >
      <div className="max-w-xl mx-auto bg-white/80 backdrop-blur-xl rounded-t-3xl shadow-2xl p-4 text-black">
        <div className="flex items-center justify-between mb-3">
          <div className="text-lg font-semibold">Assistant</div>
          <div className="flex items-center gap-2">
            {history.length > 1 && (
              <button
                onClick={restorePrevious}
                className="px-3 py-2 rounded-lg bg-purple-100 text-purple-700 text-sm"
              >
                Restore
              </button>
            )}
            <button
              aria-label="Close"
              onClick={() => setSheetOpen(false)}
              className="p-2 rounded-lg"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Messages */}
        <div className="h-32 overflow-y-auto mb-3 p-2 bg-gray-50 rounded-lg">
          {messages.length === 0 ? (
            <div className="text-gray-500 text-sm">
              No messages yet — use voice or type to talk to the assistant.
            </div>
          ) : (
            messages.slice(-6).map((m, i) => (
              <div
                key={i}
                className={`mb-2 text-sm ${
                  m.role === "ai"
                    ? "text-purple-700"
                    : "text-gray-800 text-right"
                }`}
              >
                {m.content}
              </div>
            ))
          )}
        </div>

        {/* Input */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => {
              if (recognitionRef.current && !listening) {
                recognitionRef.current.start();
              } else {
                startListening();
              }
            }}
            className={`p-3 rounded-xl flex items-center justify-center border ${
              listening
                ? "bg-red-100 border-red-200"
                : "bg-white border-gray-200"
            }`}
            aria-label="Voice input"
          >
            {listening ? (
              <MicOff className="w-5 h-5" />
            ) : (
              <Mic className="w-5 h-5" />
            )}
          </button>

          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyPress={(e) => e.key === "Enter" && handleTextSubmit()}
            placeholder={uploading ? "Processing..." : "Describe the edit you want..."}
            className="flex-1 px-4 py-3 rounded-xl border border-gray-200 focus:outline-none"
            disabled={uploading}
          />

          <button
            onClick={handleTextSubmit}
            disabled={uploading || !inputText.trim()}
            className={`p-3 rounded-xl ${
              uploading || !inputText.trim()
                ? "bg-gray-200 text-gray-400"
                : "bg-purple-600 text-white"
            }`}
            aria-label="Send"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>

        {/* History */}
        {promptHistory.length > 0 && (
          <div className="mt-3 p-2 bg-gray-50 rounded-lg text-sm">
            <div className="font-medium mb-2">Edit History</div>
            <div className="space-y-2 max-h-32 overflow-y-auto">
              {promptHistory.map((p, idx) => (
                <div key={idx} className="flex items-start gap-3">
                  <div className="w-6 h-6 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 
                    flex items-center justify-center text-white text-xs">
                    {idx + 1}
                  </div>
                  <div className="text-sm text-gray-800">{p}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {error && (
          <div className="mt-3 p-3 rounded-lg bg-red-50 text-red-700 text-sm">
            {error}
          </div>
        )}

        <audio ref={audioRef} className="hidden" />
      </div>
    </div>
  );
}
