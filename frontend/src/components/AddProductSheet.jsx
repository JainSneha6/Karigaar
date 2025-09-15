import React, { useState, useRef } from "react";
import { Upload, X } from "lucide-react";

export default function AddProductSheet({ open, onClose, addProduct, API_BASE }) {
  const [pName, setPName] = useState("");
  const [pPrice, setPPrice] = useState("");
  const [pShort, setPShort] = useState("");
  const [pImages, setPImages] = useState([]);
  const [pVideo, setPVideo] = useState(null);
  const [optimizing, setOptimizing] = useState(false);
  const [optError, setOptError] = useState(null);

  const imageInputRef = useRef(null);
  const videoInputRef = useRef(null);

  const handleImagesChange = (e) => {
    const files = e.target.files;
    if (!files) return;
    const newPreviews = Array.from(files).map((file) => ({
      file,
      url: URL.createObjectURL(file),
    }));
    setPImages((prev) => [...prev, ...newPreviews]);
  };

  const handleVideoChange = (e) => {
    const file = e.target.files && e.target.files[0];
    if (!file) return;
    setPVideo({ file, url: URL.createObjectURL(file) });
  };

  const handleAddProductSubmit = async (e) => {
    e.preventDefault();
    setOptError(null);

    if (!pName.trim() || !pPrice || !pShort.trim()) {
      alert("Please enter name, price and description.");
      return;
    }

    try {
      setOptimizing(true);
      const fd = new FormData();
      fd.append("description", pShort.trim());
      fd.append("price", pPrice);
      fd.append("currency", "INR");
      fd.append("original_name", pName.trim());
      pImages.forEach((p) => p.file && fd.append("images", p.file));

      const res = await fetch(`${API_BASE}/product/optimize`, {
        method: "POST",
        body: fd,
      });
      if (!res.ok) throw new Error("Failed to optimize product");

      const data = await res.json();
      const prodId = data.product_id || Date.now();
      const newProd = {
        id: prodId,
        name: data.suggested_name || pName.trim(),
        price:
          data.suggested_price !== undefined
            ? data.suggested_price
            : Number(pPrice),
        short: data.suggested_description || pShort.trim(),
        images:
          data.image_urls?.length > 0
            ? data.image_urls
            : pImages.map((i) => i.url),
        video: pVideo ? pVideo.url : null,
        optimized: {
          product_json_url: data.product_json_url || null,
          seo_tags: data.seo_tags || [],
          price_reasoning: data.price_reasoning || "",
        },
      };

      addProduct(newProd);
      handleClose();
    } catch (err) {
      console.error(err);
      setOptError(err.message || "Failed to optimize product");
    } finally {
      setOptimizing(false);
    }
  };

  const handleClose = () => {
    pImages.forEach((img) => {
      try {
        URL.revokeObjectURL(img.url);
      } catch {}
    });
    if (pVideo) {
      try {
        URL.revokeObjectURL(pVideo.url);
      } catch {}
    }
    setPName("");
    setPPrice("");
    setPShort("");
    setPImages([]);
    setPVideo(null);
    onClose();
  };

  return (
    <div
      className={`fixed left-0 right-0 bottom-0 z-60 transition-transform duration-300 ${
        open ? "translate-y-0" : "translate-y-full"
      }`}
      aria-hidden={!open}
    >
      <div className="max-w-xl mx-auto bg-gradient-to-br from-purple-100 via-blue-50 to-pink-100 backdrop-blur-xl rounded-t-3xl shadow-2xl p-4 text-black">
        <div className="flex items-center justify-between mb-3">
          <div className="text-lg font-semibold">Add Product</div>
          <button onClick={handleClose} className="p-2 rounded-lg">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleAddProductSubmit} className="space-y-3">
          {/* Images */}
          <div>
            <label className="text-sm font-medium">Photos</label>
            <div className="mt-2 flex gap-3 flex-wrap">
              {pImages.map((img, idx) => (
                <div
                  key={idx}
                  className="w-20 h-20 bg-gray-100 rounded-xl overflow-hidden relative"
                >
                  <img
                    src={img.url}
                    alt={`preview-${idx}`}
                    className="w-full h-full object-cover"
                  />
                  <button
                    type="button"
                    onClick={() => {
                      try {
                        URL.revokeObjectURL(img.url);
                      } catch {}
                      setPImages((prev) => prev.filter((_, i) => i !== idx));
                    }}
                    className="absolute top-1 right-1 bg-white rounded-full p-1 shadow"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              ))}
              <label
                htmlFor="add-photos"
                className="w-20 h-20 flex items-center justify-center bg-gray-100 rounded-xl cursor-pointer"
              >
                <Upload className="w-7 h-7 text-gray-400" />
              </label>
              <input
                ref={imageInputRef}
                type="file"
                accept="image/*"
                multiple
                onChange={handleImagesChange}
                className="hidden"
                id="add-photos"
              />
            </div>
          </div>

          {/* Video */}
          <div>
            <label className="text-sm font-medium">Video (optional)</label>
            <div className="mt-2">
              {pVideo ? (
                <div className="relative w-40 h-28 bg-gray-100 rounded-lg overflow-hidden">
                  <video
                    src={pVideo.url}
                    className="w-full h-full object-cover"
                    controls
                  />
                  <button
                    type="button"
                    onClick={() => setPVideo(null)}
                    className="absolute top-1 right-1 bg-white rounded-full p-1 shadow"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              ) : (
                <>
                  <label
                    htmlFor="add-video"
                    className="px-3 py-2 rounded-lg bg-transparent border border-purple-200 cursor-pointer inline-block"
                  >
                    Choose video
                  </label>
                  <input
                    ref={videoInputRef}
                    type="file"
                    accept="video/*"
                    onChange={handleVideoChange}
                    className="hidden"
                    id="add-video"
                  />
                </>
              )}
            </div>
          </div>

          {/* Name */}
          <div>
            <label className="text-sm font-medium">Name</label>
            <input
              value={pName}
              onChange={(e) => setPName(e.target.value)}
              className="w-full mt-2 px-3 py-2 rounded-lg border border-purple-200 bg-transparent"
              placeholder="Product name"
            />
          </div>

          {/* Price */}
          <div>
            <label className="text-sm font-medium">Selling Price (₹)</label>
            <input
              value={pPrice}
              onChange={(e) => setPPrice(e.target.value)}
              type="number"
              className="w-full mt-2 px-3 py-2 rounded-lg border border-purple-200 bg-transparent"
              placeholder="e.g. 2499"
            />
          </div>

          {/* Short description */}
          <div>
            <label className="text-sm font-medium">Short description</label>
            <input
              value={pShort}
              onChange={(e) => setPShort(e.target.value)}
              className="w-full mt-2 px-3 py-2 rounded-lg border border-purple-200 bg-transparent"
              placeholder="One-liner for list view"
            />
          </div>

          {optError && <div className="text-sm text-red-600">{optError}</div>}

          <div className="flex items-center justify-between">
            <button
              type="button"
              onClick={handleClose}
              className="px-4 py-2 rounded-lg bg-gray-100"
            >
              Cancel
            </button>
            <button
              type="submit"
              className={`px-4 py-2 rounded-lg ${
                optimizing
                  ? "bg-gray-400 text-white cursor-wait"
                  : "bg-purple-600 text-white"
              }`}
              disabled={optimizing}
            >
              {optimizing ? "Optimizing..." : "Add product"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
