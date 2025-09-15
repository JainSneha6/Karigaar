import React from "react";

export default function FloatingBackgroundBlobs() {
  return (
    <>
      <div className="absolute top-10 left-10 transform -translate-x-1/2 w-72 h-72 
        bg-gradient-to-br from-purple-300 to-pink-300 rounded-full mix-blend-multiply 
        filter blur-xl opacity-50 animate-pulse md:transform-none" />
      <div className="absolute top-20 right-10 w-64 h-64 
        bg-gradient-to-br from-blue-300 to-purple-300 rounded-full mix-blend-multiply 
        filter blur-xl opacity-50 animate-pulse delay-1000 hidden md:block" />
      <div className="absolute bottom-10 left-1/2 w-80 h-80 
        bg-gradient-to-br from-pink-300 to-blue-300 rounded-full mix-blend-multiply 
        filter blur-xl opacity-50 animate-pulse delay-2000" />
    </>
  );
}
