// src/components/ImageGallery.jsx
import React from "react";

export default function ImageGallery({ images, selected, setSelected }) {
  if (images.length === 0)
    return (
      <div className="w-full max-h-80 rounded-2xl bg-white/40 backdrop-blur-sm border border-white/30 flex items-center justify-center">
        <span className="text-gray-700">No image</span>
      </div>
    );

  return (
    <div className="flex flex-col items-center">
      <img
        src={selected}
        alt="product"
        className="w-full max-h-80 object-cover rounded-2xl shadow-lg"
        draggable={false}
      />
      {images.length > 1 && (
        <div className="w-full mt-3">
          <div className="flex gap-3 overflow-x-auto py-1 px-1">
            {images.map((url, idx) => (
              <button
                key={idx}
                onClick={() => setSelected(url)}
                className={`flex-shrink-0 rounded-lg overflow-hidden border-2 ${
                  selected === url ? "border-purple-600" : "border-transparent"
                }`}
                aria-label={`Select image ${idx + 1}`}
              >
                <img
                  src={url}
                  alt={`thumb-${idx}`}
                  className="w-20 h-20 object-cover"
                  draggable={false}
                />
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
