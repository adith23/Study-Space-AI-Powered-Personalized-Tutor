import React, { useRef } from "react";
import { Upload as UploadIcon, Link as LinkIcon, Clipboard as ClipboardIcon, FileUp } from "lucide-react";
import Modal from "@/components/ui/Modal";

interface UploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUpload: (file: File) => void;
}

const UploadModal: React.FC<UploadModalProps> = ({ isOpen, onClose, onUpload }) => {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      onUpload(e.target.files[0]);
      onClose(); // Close modal immediately after starting upload
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={
        <div className="flex w-full items-center justify-center gap-3">
          <FileUp size={28} />
          <span>Upload your documents</span>
        </div>
      }
      maxWidth="max-w-3xl"
    >
      <div className="flex gap-6 justify-center py-8">
        {/* Upload Card */}
        <button
          onClick={() => fileInputRef.current?.click()}
          className="flex flex-col items-start gap-4 rounded-2xl bg-zinc-800/80 p-6 w-48 hover:bg-zinc-700 transition-colors border border-zinc-700 text-left group"
        >
          <UploadIcon size={24} className="text-zinc-300 group-hover:text-white" />
          <div>
            <h3 className="text-lg font-bold text-white mb-1">Upload</h3>
            <p className="text-xs text-zinc-400 font-medium">Files, Audio, Video</p>
          </div>
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            className="hidden"
            accept=".pdf,.txt,.doc,.docx"
          />
        </button>

        {/* Link Card (Stub) */}
        <button
          onClick={() => alert("Link upload is coming soon!")}
          className="flex flex-col items-start gap-4 rounded-2xl bg-zinc-800/80 p-6 w-48 hover:bg-zinc-700 transition-colors border border-zinc-700 text-left group"
        >
          <LinkIcon size={24} className="text-zinc-300 group-hover:text-white" />
          <div>
            <h3 className="text-lg font-bold text-white mb-1">Link</h3>
            <p className="text-xs text-zinc-400 font-medium">YouTube, Website</p>
          </div>
        </button>

        {/* Paste Card (Stub) */}
        <button
          onClick={() => alert("Paste upload is coming soon!")}
          className="flex flex-col items-start gap-4 rounded-2xl bg-zinc-800/80 p-6 w-48 hover:bg-zinc-700 transition-colors border border-zinc-700 text-left group"
        >
          <ClipboardIcon size={24} className="text-zinc-300 group-hover:text-white" />
          <div>
            <h3 className="text-lg font-bold text-white mb-1">Paste</h3>
            <p className="text-xs text-zinc-400 font-medium">Copied Text</p>
          </div>
        </button>
      </div>
    </Modal>
  );
};

export default UploadModal;
