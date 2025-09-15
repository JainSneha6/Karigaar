import React from "react";
import { Stars } from "lucide-react";

export default function FloatingFAB({ onClick }) {
  return (
    <div className="fixed left-0 right-0 bottom-6 flex items-center justify-center pointer-events-none z-20">
      <button
        onClick={onClick}
        className="pointer-events-auto inline-flex items-center justify-center 
          w-20 h-20 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 
          shadow-xl text-white font-bold transform hover:scale-105 active:scale-95"
        aria-label="Open prompt"
      >
        <Stars className="w-10 h-10" />
      </button>
    </div>
  );
}
