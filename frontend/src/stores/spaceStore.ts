import { create } from "zustand";
import type { UploadedFileState } from "@/types/dashboard";

interface SpaceStoreState {
  files: UploadedFileState[];
  viewingFileId: number | null;
  selectedFileIds: Set<number>;
  
  // Actions
  setFiles: (files: UploadedFileState[]) => void;
  addFile: (file: UploadedFileState) => void;
  updateFile: (fileId: number, updates: Partial<UploadedFileState>) => void;
  removeFile: (fileId: number) => void;
  setViewingFileId: (id: number | null) => void;
  toggleFileSelection: (id: number) => void;
  setSelectedFileIds: (ids: Set<number>) => void;
  clearSelections: () => void;
}

export const useSpaceStore = create<SpaceStoreState>((set) => ({
  files: [],
  viewingFileId: null,
  selectedFileIds: new Set<number>(),

  setFiles: (files) => set({ files }),
  
  addFile: (file) =>
    set((state) => ({
      files: [file, ...state.files],
    })),

  updateFile: (fileId, updates) =>
    set((state) => ({
      files: state.files.map((f) =>
        f.id === fileId ? { ...f, ...updates } : f
      ),
    })),

  removeFile: (fileId) =>
    set((state) => {
      const nextSelected = new Set(state.selectedFileIds);
      nextSelected.delete(fileId);
      return {
        files: state.files.filter((f) => f.id !== fileId),
        selectedFileIds: nextSelected,
        viewingFileId: state.viewingFileId === fileId ? null : state.viewingFileId,
      };
    }),

  setViewingFileId: (viewingFileId) => set({ viewingFileId }),

  toggleFileSelection: (id) =>
    set((state) => {
      const next = new Set(state.selectedFileIds);
      if (next.has(id)) {
        next.delete(id);
      } else {
        const file = state.files.find((f) => f.id === id);
        if (file && file.status === "success") {
          next.add(id);
        }
      }
      return { selectedFileIds: next };
    }),

  setSelectedFileIds: (selectedFileIds) => set({ selectedFileIds }),

  clearSelections: () => set({ selectedFileIds: new Set<number>() }),
}));
