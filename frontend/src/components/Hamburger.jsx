import React from "react";

export default function HamburgerMenu({ onClick }) {
  return (
    <button
      onClick={onClick}
      className="absolute top-4 left-4 z-20 cursor-pointer"
      aria-label="Open menu"
    >
      <svg
        className="w-8 h-8 text-gray-800"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M4 6h16M4 12h16M4 18h16"
        />
      </svg>
    </button>
  );
}
