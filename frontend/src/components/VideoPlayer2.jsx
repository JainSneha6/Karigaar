// src/components/VideoPlayer.jsx
import React from "react";

export default function VideoPlayer({ videoUrl }) {
  return (
    <div className="px-1">
      <h2 className="text-lg font-semibold text-purple-700 mb-2">Product demo video</h2>
      <video src={videoUrl} controls className="w-full rounded-lg" />
    </div>
  );
}
