import { useCallback, useState } from 'react';

interface UseFileUploadOptions {
  accept: string;
  multiple?: boolean;
  maxSize?: number;
}

interface UseFileUploadReturn {
  files: File[];
  error: string | null;
  addFiles: (newFiles: FileList | File[]) => void;
  removeFile: (index: number) => void;
  clearFiles: () => void;
}

export function useFileUpload({
  multiple = false,
  maxSize = 50 * 1024 * 1024,
}: UseFileUploadOptions): UseFileUploadReturn {
  const [files, setFiles] = useState<File[]>([]);
  const [error, setError] = useState<string | null>(null);

  const addFiles = useCallback(
    (newFiles: FileList | File[]) => {
      setError(null);
      const fileArray = Array.from(newFiles);

      const validFiles = fileArray.filter((file) => {
        if (maxSize && file.size > maxSize) {
          setError(`File "${file.name}" exceeds maximum size of ${Math.round(maxSize / 1024 / 1024)}MB`);
          return false;
        }
        return true;
      });

      if (validFiles.length === 0) return;

      setFiles((prev) => (multiple ? [...prev, ...validFiles] : validFiles));
    },
    [multiple, maxSize]
  );

  const removeFile = useCallback((index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  }, []);

  const clearFiles = useCallback(() => {
    setFiles([]);
    setError(null);
  }, []);

  return { files, error, addFiles, removeFile, clearFiles };
}
