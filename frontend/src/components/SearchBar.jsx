import React from "react";
import { Search } from "lucide-react";

export default function SearchBar({ query, setQuery }) {
  return (
    <div className="flex-1 relative">
      <input
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search products"
        className="w-full h-12 px-4 rounded-xl border border-purple-200 bg-white shadow-sm focus:outline-none"
      />
      <Search className="absolute right-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
    </div>
  );
}
