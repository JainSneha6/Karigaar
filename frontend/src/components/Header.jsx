import React from "react";
import { Sparkles } from "lucide-react";

export default function Header() {
  return (
    <div className="text-center mb-8">
      {/* Icon badge */}
      <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-r from-purple-400 to-pink-400 rounded-2xl mb-4 shadow-lg">
        <Sparkles className="w-8 h-8 text-white" />
      </div>

      {/* Gradient headline */}
      <h1 className="text-3xl md:text-4xl font-bold bg-gradient-to-r from-purple-700 to-pink-600 bg-clip-text text-transparent leading-tight tracking-tight">
        I’m Chloe — Your Onboarding Guide
      </h1>

      {/* Subtext */}
      <p className="text-purple-700 mt-2 text-lg font-medium leading-relaxed">
        Talk to me naturally. I’ll understand and respond intelligently.
      </p>
    </div>
  );
}
