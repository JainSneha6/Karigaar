export default function TranscriptOverlay({ show, onClose, history }) {
  if (!show) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50 conversation-overlay">
      <div className="bg-white rounded-3xl max-w-md w-full max-h-[80vh] overflow-y-auto">
        <div className="p-6">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-bold text-gray-900 headline">
              Conversation
            </h3>
            <button
              onClick={onClose}
              className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center hover:bg-gray-300 transition-colors"
            >
              <span className="text-gray-600 text-lg">×</span>
            </button>
          </div>

          <div className="space-y-3">
            {history.length === 0 ? (
              <div className="text-center text-gray-500 py-8">
                <div className="text-4xl mb-2">💬</div>
                <div>No conversation yet</div>
                <div className="text-sm">Start talking to see transcript</div>
              </div>
            ) : (
              history.map((m, i) => (
                <div
                  key={i}
                  className={`p-3 rounded-2xl ${
                    m.role === "user"
                      ? "bg-blue-100 text-blue-900 ml-8"
                      : "bg-gray-100 text-gray-900 mr-8"
                  }`}
                >
                  <div className="text-xs text-gray-600 mb-1">
                    {m.role === "user" ? "You" : "Assistant"}
                  </div>
                  <div className="text-sm">{m.text}</div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
