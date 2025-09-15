import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import MenuDrawer from "../components/MenuDrawer";
import FloatingBackgroundBlobs from "../components/FloatingBackgroundBlobs";
import HamburgerButton from "../components/Hamburger";

export default function Profile() {
  const { slug } = useParams();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [menuOpen, setMenuOpen] = useState(false);

  const effectiveSlug = slug || "Siddhartha";

  useEffect(() => {
    const fetchProfile = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await fetch(
          `http://localhost:5000/api/converse/profile_json/${encodeURIComponent(
            effectiveSlug
          )}`
        );
        if (!res.ok) {
          const body = await res.json().catch(() => ({}));
          throw new Error(body?.error || `Server returned ${res.status}`);
        }
        const data = await res.json();
        setProfile(data);
      } catch (e) {
        console.error(e);
        setError(e.message || "Failed to load profile");
      } finally {
        setLoading(false);
      }
    };
    fetchProfile();
  }, [effectiveSlug]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-100 via-blue-50 to-pink-100 overflow-hidden relative font-sans">
      {/* Floating blobs */}
      <FloatingBackgroundBlobs />

      {/* Hamburger */}
      <HamburgerButton onClick={() => setMenuOpen(true)} />

      <main className="relative z-10 max-w-md mx-auto px-6 py-8">
        {/* Loader */}
        {loading && (
          <div className="mt-12 flex flex-col items-center gap-4">
            <div className="w-28 h-28 rounded-2xl bg-gradient-to-br from-purple-400 to-pink-400 animate-pulse shadow-md" />
            <div className="h-6 w-44 rounded bg-gray-200/30 animate-pulse" />
            <div className="h-4 w-64 rounded bg-gray-200/20 animate-pulse" />
          </div>
        )}

        {/* Error */}
        {!loading && error && (
          <div className="mt-8 text-center text-red-700">
            <strong>Error:</strong> {error}
            <div className="mt-3">
              <button
                onClick={() => window.location.reload()}
                className="px-3 py-2 rounded-lg bg-purple-600 text-white"
              >
                Retry
              </button>
            </div>
          </div>
        )}

        {/* Profile content */}
        {!loading && profile && (
          <article className="mt-6">
            <div className="relative flex flex-col items-center text-center">
              <div className="absolute -top-8 -left-8 w-32 h-32 bg-white/6 rounded-full blur-2xl pointer-events-none" />

              {/* Avatar */}
              <div className="relative">
                <div className="w-28 h-28 md:w-32 md:h-32 rounded-2xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-3xl md:text-4xl font-semibold text-white shadow-xl ring-2 ring-white/20">
                  {profile["Full Name"]
                    ? profile["Full Name"]
                        .split(" ")
                        .map((n) => n[0])
                        .slice(0, 2)
                        .join("")
                        .toUpperCase()
                    : "A"}
                </div>
              </div>

              {/* Name */}
              <h1 className="mt-4 text-3xl md:text-4xl font-heading font-bold leading-tight bg-clip-text text-transparent bg-gradient-to-r from-purple-700 to-pink-600 tracking-tight">
                {profile["Full Name"] || "Unknown Artisan"}
              </h1>

              {/* Tagline */}
              <p className="mt-2 text-sm md:text-base text-gray-600 max-w-xs">
                {profile["Tagline"] ||
                  (profile["Bio"] ? profile["Bio"].slice(0, 110) : "")}
              </p>

              <div className="mt-3 text-xs text-gray-500">Location</div>
              <div className="text-sm font-semibold text-gray-800">
                {profile["Location"] || "—"}
              </div>
            </div>

            {/* Details sections */}
            <div className="mt-8 px-1 space-y-6">
              <section>
                <h3 className="text-lg font-semibold text-purple-700 mb-2 flex items-center gap-2">
                  Bio
                </h3>
                <p className="text-gray-700 leading-relaxed text-sm md:text-base max-w-prose mx-auto">
                  {profile["Bio"] || "No bio available."}
                </p>
              </section>

              <section>
                <h3 className="text-lg font-semibold text-purple-700 mb-2 flex items-center gap-2">
                  Materials Used
                </h3>
                <p className="text-gray-700 leading-relaxed text-sm md:text-base max-w-prose mx-auto">
                  {profile["Materials Used"] || "Not specified."}
                </p>
              </section>

              <section>
                <h3 className="text-lg font-semibold text-purple-700 mb-2 flex items-center gap-2">
                  Aspiration
                </h3>
                <p className="text-gray-700 leading-relaxed text-sm md:text-base max-w-prose mx-auto">
                  {profile["Aspiration"] || "Not specified."}
                </p>
              </section>
            </div>
          </article>
        )}
      </main>

      <MenuDrawer open={menuOpen} onClose={() => setMenuOpen(false)} />

      <style>{`
        @layer utilities {
          .font-heading {
            font-family: Poppins, Inter, system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial;
          }
        }
      `}</style>
    </div>
  );
}
