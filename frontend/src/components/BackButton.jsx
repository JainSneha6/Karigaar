// src/components/BackButton.jsx
import React from "react";
import { ArrowLeft } from "lucide-react";

export default function BackButton({ onClick }) {
  return (
    <button
      aria-label="Back"
      onClick={onClick}
      className="absolute top-4 left-4 p-2 rounded-lg bg-white/40 backdrop-blur-sm border border-white/30 shadow hover:scale-95 transition-transform"
    >
      <ArrowLeft className="w-5 h-5 text-gray-800" />
    </button>
  );
}
