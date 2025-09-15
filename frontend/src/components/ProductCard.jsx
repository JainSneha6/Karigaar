import React from "react";

export default function ProductCard({ product, onClick }) {
  return (
    <article className="bg-gradient-to-br from-purple-50 via-blue-50 to-pink-50 rounded-2xl shadow-sm overflow-hidden">
      <button className="w-full block text-left" onClick={onClick}>
        <div className="w-full h-44 bg-gray-100 overflow-hidden">
          {product.images?.length > 0 ? (
            <img
              src={product.images[0]}
              alt={product.name}
              className="w-full h-full object-cover"
            />
          ) : (
            <div className="flex items-center justify-center w-full h-full text-gray-400">
              No image
            </div>
          )}
        </div>
        <div className="p-3">
          <div className="flex items-center justify-between mb-1">
            <h3 className="text-sm font-semibold text-gray-800">{product.name}</h3>
            <div className="text-sm font-semibold">₹{product.price}</div>
          </div>
          <p className="text-xs text-gray-500 mb-2 truncate">{product.short}</p>
          {product.optimized?.seo_tags?.length > 0 && (
            <div className="flex gap-2 flex-wrap">
              {product.optimized.seo_tags.slice(0, 3).map((t, i) => (
                <span
                  key={i}
                  className="text-xs bg-gray-100 px-2 py-1 rounded-md text-gray-600"
                >
                  {t}
                </span>
              ))}
            </div>
          )}
        </div>
      </button>
    </article>
  );
}
