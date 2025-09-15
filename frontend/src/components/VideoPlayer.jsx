import React from "react";
import { Upload } from "lucide-react";

export default function VideoPlayer({ current, handleFileChange }) {
  return (
    <div className="fixed inset-0 flex items-center justify-center">
      {current ? (
        <video
          controls
          playsInline
          src={current.url}
          className="w-full h-full object-contain"
        />
      ) : (
        <div className="w-full h-full flex flex-col items-center justify-center p-6 relative z-10">
          <div className="w-28 h-28 bg-gradient-to-br from-purple-400 to-pink-400 
            rounded-full flex items-center justify-center mb-6 shadow-lg">
            <Upload className="w-12 h-12 text-white" />
          </div>
          <p className="text-lg font-medium mb-2 text-gray-700">No video uploaded</p>
          <p className="text-sm opacity-80 mb-6 text-center text-gray-600">
            Tap the button below to upload a video and start editing
          </p>
          <label
            htmlFor="mobile-upload"
            className="px-6 py-3 rounded-full bg-gradient-to-r 
              from-purple-500 to-pink-500 text-white font-medium cursor-pointer 
              shadow-md hover:scale-105 transition-transform"
          >
            Choose video
          </label>
          <input
            id="mobile-upload"
            type="file"
            accept="video/*"
            onChange={handleFileChange}
            className="hidden"
          />
        </div>
      )}
    </div>
  );
}
