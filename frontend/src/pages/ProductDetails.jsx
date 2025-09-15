import React, { useContext, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { ProductContext } from "../context/ProductContext";

import FloatingBackgroundBlobs from "../components/FloatingBackgroundBlobs";
import BackButton from "../components/BackButton";
import ImageGallery from "../components/ImageGallery";
import AISuggestion from "../components/AISuggestion";
import VideoPlayer from "../components/VideoPlayer2";
import MarketplaceLinks from "../components/MarketPlacesLink";
import { ToastContainer } from "react-toastify";
import { Sparkle } from "lucide-react";

export default function ProductDetail() {
  const { id } = useParams();
  const { products } = useContext(ProductContext);
  const navigate = useNavigate();
  const [selectedImage, setSelectedImage] = useState(null);

  const detail = products.find((p) => p.id == id);

  if (!detail) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-100 via-blue-50 to-pink-100 flex items-center justify-center">
        <div className="text-center text-gray-800 text-lg font-medium">
          Product not found
        </div>
      </div>
    );
  }

  const images = detail.images || [];
  const selected = selectedImage || images[0] || "";

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-100 via-blue-50 to-pink-100 relative overflow-hidden flex flex-col">
      {/* Floating background blobs */}
      <FloatingBackgroundBlobs />

      {/* Header */}
      <header className="relative z-10 p-4 pt-16 text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-r from-purple-400 to-pink-400 rounded-2xl mb-4 shadow-lg">
          <Sparkle className="w-8 h-8 text-white" />
        </div>
        <h1 className="text-3xl md:text-4xl font-bold bg-gradient-to-r from-purple-700 to-pink-600 bg-clip-text text-transparent">
          Product Details
        </h1>
        <BackButton onClick={() => navigate("/product-listing")} />
      </header>

      {/* Main content */}
      <main className="relative z-10 px-4 pb-12 flex-1 overflow-y-auto">
        <section className="max-w-3xl mx-auto space-y-10">
          {/* Image gallery */}
          <ImageGallery
            images={images}
            selected={selected}
            setSelected={setSelectedImage}
          />

          {/* AI suggested info */}
          <AISuggestion detail={detail} />

          {/* Product demo video */}
          {detail.video && <VideoPlayer videoUrl={detail.video} />}

          {/* Marketplace links */}
          <MarketplaceLinks />
          <ToastContainer />
        </section>
      </main>
    </div>
  );
}
