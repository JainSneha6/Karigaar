// src/components/AISuggestion.jsx
import React from "react";
import { Stars } from "lucide-react";

export default function AISuggestion({ detail }) {
  const optimized = detail.optimized || {};
  const suggestedPrice = optimized.suggested_price ?? detail.price ?? "—";

  return (
    <>
      {/* AI suggested name */}
      <div className="px-1">
        <h2 className="text-lg font-semibold text-purple-700 mb-2 flex items-center gap-2">
          <Stars className="w-5 h-5 text-purple-600" />
          AI suggested product name
        </h2>
        <p className="text-xl font-bold text-gray-900">
          {optimized.suggested_name ?? detail.name}
        </p>
      </div>

      {/* AI suggested price */}
      <div className="px-1">
        <h2 className="text-lg font-semibold text-purple-700 mb-2 flex items-center gap-2">
          <Stars className="w-5 h-5 text-purple-600" />
          AI suggested price
        </h2>
        <div className="text-2xl font-extrabold bg-clip-text text-transparent bg-gradient-to-r from-purple-700 to-pink-600">
          ₹{suggestedPrice}
        </div>
      </div>

      {/* AI suggested description */}
      <div className="px-1">
        <h2 className="text-lg font-semibold text-purple-700 mb-2 flex items-center gap-2">
          <Stars className="w-5 h-5 text-purple-600" />
          AI suggested description
        </h2>
        <p className="text-sm text-gray-800 leading-relaxed">
          {optimized.suggested_description ?? detail.short ?? "No description available."}
        </p>
      </div>

      {/* SEO tags */}
      {optimized.seo_tags && optimized.seo_tags.length > 0 && (
        <div className="px-1">
          <h2 className="text-lg font-semibold text-purple-700 mb-2 flex items-center gap-2">
            <Stars className="w-5 h-5 text-purple-600" />
            AI suggested SEO tags
          </h2>
          <div className="flex flex-wrap gap-2">
            {optimized.seo_tags.map((tag, i) => (
              <span
                key={i}
                className="px-3 py-1 rounded-full text-xs font-medium bg-gradient-to-br from-purple-400 to-blue-400 text-white select-none"
              >
                #{tag}
              </span>
            ))}
          </div>
        </div>
      )}
    </>
  );
}
