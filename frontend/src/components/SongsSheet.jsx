// File: src/components/SongsSheet.jsx
import React from "react";
import { X } from "lucide-react";
import { useState } from "react";


export default function SongsSheet({ sheetOpen, setSheetOpen, availableTrending = [], onShuffle, onLoadFromServer, addSongToCurrentVideo, uploading, error }) {
    // track which song (id) is currently being added so only its button shows the loading state
    const [addingId, setAddingId] = useState(null);


    const handleAddClick = async (song) => {
        try {
            setAddingId(song.id);
            // expect addSongToCurrentVideo to be an async function returning a promise
            await addSongToCurrentVideo(song);
        } catch (e) {
            // parent handles error display; swallow here
        } finally {
            setAddingId(null);
        }
    };
    return (
        <div
            className={`fixed left-0 right-0 bottom-0 z-50 transition-transform duration-300 ${sheetOpen ? "translate-y-0" : "translate-y-full"
                }`}
            aria-hidden={!sheetOpen}
        >
            {/* Constrain the sheet panel to max 50vh and make its inner area scrollable */}
            <div className="max-w-xl mx-auto bg-white/80 backdrop-blur-xl rounded-t-3xl shadow-2xl p-4 text-black" style={{ maxHeight: '50vh', overflow: 'hidden' }}>
                <div className="flex items-center justify-between mb-3">
                    <div className="text-lg font-semibold">Trending songs</div>
                    <div className="flex items-center gap-2">
                        <button
                            aria-label="Close"
                            onClick={() => setSheetOpen(false)}
                            className="p-2 rounded-lg"
                        >
                            <X className="w-5 h-5" />
                        </button>
                    </div>
                </div>


                <p className="text-sm text-gray-600">Showing top {availableTrending.length} trending songs. Click "Add" to mix into your current video.</p>


                {/* Scrollable list container - fills remaining space inside the 50vh panel */}
                <div className=" mt-3 " style={{ maxHeight: 'calc(50vh - 160px)', overflowY: 'auto', paddingRight: 8 }}>
                    <div className="space-y-3">
                        {availableTrending.map((s) => (
                            <div key={s.id} className="bg-white flex items-center justify-between p-3 rounded-lg border border-gray-100">
                                <div className="flex-1 pr-3">
                                    <div className="font-medium text-gray-900">{s.title}</div>
                                    <div className="text-sm text-gray-500">{s.artist}</div>
                                </div>
                                <div>
                                    <button
                                        disabled={addingId !== null}
                                        onClick={() => handleAddClick(s)}
                                        className={`px-3 py-2 rounded-lg text-sm font-semibold ${addingId === s.id ? 'bg-gray-200 text-gray-400' : 'bg-purple-100 text-purple-700'}`}
                                    >
                                        {addingId === s.id ? 'Adding...' : 'Add'}
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>


                {error && (
                    <div className="mt-3 p-3 rounded-lg bg-red-50 text-red-700 text-sm">{error}</div>
                )}


                <div className="mt-4 flex items-center justify-between">
                    <button
                        onClick={() => onShuffle && onShuffle()}
                        className="px-3 py-2 border border-gray-200 rounded-lg bg-gray-100 text-sm"
                    >
                        Shuffle
                    </button>


                    <button
                        onClick={() => onLoadFromServer && onLoadFromServer()}
                        className="px-3 py-2 rounded-lg border border-gray-200 bg-white text-sm"
                    >
                        Load from server
                    </button>
                </div>


            </div>
        </div>
    );
}
