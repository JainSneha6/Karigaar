export default function MicButton({ status, onClick }) {
  return (
    <div className="flex justify-center items-center">
      <div className="relative">
        <div
          className={`w-48 h-48 rounded-full flex items-center justify-center shadow-2xl transition-all duration-500 cursor-pointer ${
            status === "recording"
              ? "bg-gradient-to-br from-red-400 to-pink-500 animate-pulse scale-110"
              : status === "uploading"
              ? "bg-gradient-to-br from-blue-400 to-purple-500"
              : "bg-gradient-to-br from-purple-500 to-blue-500 hover:scale-105"
          }`}
          onClick={onClick}
        >
          {status === "uploading" ? (
            <div className="w-12 h-12 border-4 border-white border-t-transparent rounded-full animate-spin"></div>
          ) : (
            <svg
              className="w-16 h-16 text-white"
              fill="currentColor"
              viewBox="0 0 24 24"
            >
              <path d="M12 14c1.66 0 2.99-1.34 2.99-3L15 5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3zm5.3-3c0 3-2.54 5.1-5.3 5.1S6.7 14 6.7 11H5c0 3.41 2.72 6.23 6 6.72V21h2v-3.28c3.28-.48 6-3.3 6-6.72h-1.7z" />
            </svg>
          )}
        </div>

        {status === "recording" && (
          <>
            <div className="absolute inset-0 rounded-full border-4 border-red-300 animate-ping"></div>
            <div
              className="absolute inset-0 rounded-full border-2 border-red-200 animate-ping"
              style={{ animationDelay: "0.5s" }}
            ></div>
          </>
        )}
      </div>
    </div>
  );
}
