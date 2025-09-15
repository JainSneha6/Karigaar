import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Conversational from "./pages/Conversational";
import VideoEditor from "./pages/VideoEditor";
import ProductListings from "./pages/ProductListing";
import ProductDetail from "./pages/ProductDetails";
import Profile from "./pages/Profile";
import { ProductProvider } from "./context/ProductContext";

export default function App() {
  return (
    <BrowserRouter>
      <ProductProvider>
        <div>
          <Routes>
            <Route path="/" element={<Conversational />} />
            <Route path="/video-editor" element={<VideoEditor />} />
            <Route path="/profile" element={<Profile />} />
            <Route path="/product-listing" element={<ProductListings />} />
            <Route path="/product/:id" element={<ProductDetail />} />
            <Route path="*" element={<div className="p-8 bg-white rounded-lg shadow">Page not found</div>} />
          </Routes>
        </div>
      </ProductProvider>
    </BrowserRouter>
  );
}