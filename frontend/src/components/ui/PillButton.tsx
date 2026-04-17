import React from "react";

interface PillButtonProps {
  label: string;
  isActive: boolean;
  onClick: () => void;
}

const PillButton: React.FC<PillButtonProps> = ({ label, isActive, onClick }) => {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded-full px-6 py-2 text-sm font-medium transition-colors border ${
        isActive
          ? "border-white bg-zinc-800 text-white"
          : "border-zinc-700 bg-transparent text-zinc-400 hover:text-white hover:border-zinc-500"
      }`}
    >
      {label}
    </button>
  );
};

export default PillButton;
