import { Link } from "react-router-dom";

export default function MenuDrawer({ open, onClose }) {
  if (!open) return null;

  return (
    <>
      {/* overlay */}
      <div
        className="fixed inset-0 bg-black/50 z-40"
        onClick={onClose}
      ></div>

      {/* drawer */}
      <div className="fixed inset-y-0 left-0 z-50 w-80 bg-gradient-to-br from-purple-100 via-pink-50 to-pink-100 shadow-xl transform translate-x-0 transition-transform duration-300 ease-in-out overflow-y-auto rounded-r-3xl">
        <div className="p-6">
          {/* header */}
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-bold text-gray-900 headline">Menu</h3>
            <button
              onClick={onClose}
              className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center hover:bg-gray-300 transition-colors"
            >
              <span className="text-gray-600 text-lg">×</span>
            </button>
          </div>

          {/* links */}
          <ul className="space-y-3">
            <li>
              <Link
                to="/profile"
                onClick={onClose}
                className="block p-3 bg-white/80 backdrop-blur-sm rounded-2xl text-gray-900 text-sm border border-white/30 hover:bg-white"
              >
                User Profile
              </Link>
            </li>
            <li>
              <Link
                to="/video-generation"
                onClick={onClose}
                className="block p-3 bg-white/80 backdrop-blur-sm rounded-2xl text-gray-900 text-sm border border-white/30 hover:bg-white"
              >
                Video Generation
              </Link>
            </li>
            <li>
              <Link
                to="/video-editor"
                onClick={onClose}
                className="block p-3 bg-white/80 backdrop-blur-sm rounded-2xl text-gray-900 text-sm border border-white/30 hover:bg-white"
              >
                Video Editor
              </Link>
            </li>
            <li>
              <Link
                to="/image-generation"
                onClick={onClose}
                className="block p-3 bg-white/80 backdrop-blur-sm rounded-2xl text-gray-900 text-sm border border-white/30 hover:bg-white"
              >
                Image Generation
              </Link>
            </li>
            <li>
              <Link
                to="/image-editor"
                onClick={onClose}
                className="block p-3 bg-white/80 backdrop-blur-sm rounded-2xl text-gray-900 text-sm border border-white/30 hover:bg-white"
              >
                Image Editor
              </Link>
            </li>
            <li>
              <Link
                to="/product-listing"
                onClick={onClose}
                className="block p-3 bg-white/80 backdrop-blur-sm rounded-2xl text-gray-900 text-sm border border-white/30 hover:bg-white"
              >
                Product Listing
              </Link>
            </li>
          </ul>
        </div>
      </div>
    </>
  );
}
