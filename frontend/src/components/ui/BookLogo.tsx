import React from "react";

interface BookLogoProps {
  className?: string;
  bookClassName?: string;
}

export function BookLogo({ className = "w-6 h-6", bookClassName = "w-6 h-6" }: BookLogoProps) {
  return (
    <div className={`relative inline-flex items-center justify-center ${className}`}>
      {/* Sparkle on top-left of the book icon */}
      <svg
        className="absolute -top-1.5 -left-1.5 w-3.5 h-3.5 text-white fill-current animate-pulse"
        viewBox="0 0 24 24"
        fill="currentColor"
      >
        <path d="M12 0L14.8 9.2L24 12L14.8 14.8L12 24L9.2 14.8L0 12L9.2 9.2Z" />
      </svg>
      
      {/* Open Book SVG matching the exact style */}
      <svg
        className={`${bookClassName} text-white`}
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z" />
        <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z" />
      </svg>
    </div>
  );
}
