import React, { useState, useEffect, useContext } from "react";
import { Package, Plus } from "lucide-react";
import { useNavigate } from "react-router-dom";
import MenuDrawer from "../components/MenuDrawer";
import { ProductContext } from "../context/ProductContext";

import SearchBar from "../components/SearchBar";
import ProductCard from "../components/ProductCard";
import AddProductSheet from "../components/AddProductSheet";
import FloatingBackgroundBlobs from "../components/FloatingBackgroundBlobs";
import HamburgerMenu from "../components/Hamburger";

const API_BASE = "http://localhost:5000/api"; // adjust if backend hosted elsewhere

export default function ProductListings() {
  const { products, addProduct } = useContext(ProductContext);
  const [query, setQuery] = useState("");
  const [menuOpen, setMenuOpen] = useState(false);
  const [addSheetOpen, setAddSheetOpen] = useState(false);

  const navigate = useNavigate();

  const filtered = products.filter(
    (p) =>
      p.name.toLowerCase().includes(query.toLowerCase()) ||
      p.short.toLowerCase().includes(query.toLowerCase())
  );

  // Cleanup blob URLs when unmounting
  useEffect(() => {
    return () => {
      products.forEach((product) => {
        (product.images || []).forEach((url) => {
          if (url && url.startsWith("blob:")) {
            try {
              URL.revokeObjectURL(url);
            } catch {}
          }
        });
        if (product.video && product.video.startsWith("blob:")) {
          try {
            URL.revokeObjectURL(product.video);
          } catch {}
        }
      });
    };
  }, [products]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-100 via-blue-50 to-pink-100 overflow-hidden relative p-4">
      {/* Floating background blobs */}
      <FloatingBackgroundBlobs />

      {/* Hamburger menu button */}
      <HamburgerMenu onClick={() => setMenuOpen(true)} />

      {/* Header */}
      <header className="relative z-10 p-4">
        <div className="text-center mb-6">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-r from-purple-400 to-pink-400 rounded-2xl mb-4 shadow-lg">
            <Package className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-3xl md:text-4xl font-bold bg-gradient-to-r from-purple-700 to-pink-600 bg-clip-text text-transparent">
            Product Listings
          </h1>
        </div>
      </header>

      {/* Search + Add */}
      <div className="flex items-center gap-3 mb-6 relative z-10">
        <SearchBar query={query} setQuery={setQuery} />
        <button
          onClick={() => setAddSheetOpen(true)}
          className="ml-2 inline-flex items-center justify-center h-12 w-12 rounded-xl bg-gradient-to-r from-purple-500 to-pink-500 text-white shadow-md"
          aria-label="Add product"
        >
          <Plus className="w-5 h-5" />
        </button>
      </div>

      {/* Product grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 relative z-10">
        {filtered.length === 0 ? (
          <div className="col-span-full text-center text-gray-500 py-12">
            No products — tap + to add one.
          </div>
        ) : (
          filtered.map((p) => (
            <ProductCard
              key={p.id}
              product={p}
              onClick={() => navigate(`/product/${p.id}`)}
            />
          ))
        )}
      </div>

      {/* Add Product sheet */}
      <AddProductSheet
        open={addSheetOpen}
        onClose={() => setAddSheetOpen(false)}
        addProduct={addProduct}
        API_BASE={API_BASE}
      />

      {/* Menu drawer */}
      <MenuDrawer open={menuOpen} onClose={() => setMenuOpen(false)} />
    </div>
  );
}
