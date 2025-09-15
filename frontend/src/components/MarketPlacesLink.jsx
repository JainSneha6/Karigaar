// src/components/MarketplaceLinks.jsx
import { Package } from "lucide-react";
import React from "react";
import { FaAmazon, FaFacebook, FaShoppingCart } from "react-icons/fa";
import { toast } from "react-toastify";
import 'react-toastify/dist/ReactToastify.css';

const MarketplaceLinks = () => {
  const links = [
    { name: "Amazon", url: "https://www.amazon.com", icon: FaAmazon },
    { name: "Facebook", url: "https://www.facebook.com", icon: FaFacebook },
    { name: "Flipkart", url: "https://www.flipkart.com", icon: FaShoppingCart },
  ];

  const handleClick = (name) => {
    toast.success(`Added to ${name}!`, {
      position: "top-right",
      autoClose: 2000,
      hideProgressBar: false,
      closeOnClick: true,
      pauseOnHover: true,
      draggable: true,
      theme: "colored",
    });
  };

  return (
    <div className="mt-10 px-1 max-w-3xl mx-auto space-y-3">
    <h2 className="text-lg font-semibold text-purple-700 mb-2 flex items-center gap-2">
        <Package className="w-5 h-5 text-purple-600" />
        Add to Marketplace
    </h2>
      <div className="flex flex-col gap-3">
        {links.map((link) => {
          const Icon = link.icon;
          return (
            <button
              key={link.name}
              onClick={() => handleClick(link.name)}
              className="flex items-center gap-3 px-4 py-2 rounded-xl bg-purple-300 text-purple-900 font-semibold shadow-sm hover:scale-105 transition-transform"
            >
              <Icon className="w-5 h-5" />
              <span>{link.name}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
};

export default MarketplaceLinks;
