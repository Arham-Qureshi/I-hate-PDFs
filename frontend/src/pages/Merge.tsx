import { useState } from 'react';
import { Layers, Trash2 } from 'lucide-react';
import FileUpload from '../components/FileUpload';
import Button from '../components/Button';
import ProgressBar from '../components/ProgressBar';
import { useFileUpload } from '../hooks/useFileUpload';
import { showToast } from '../components/Toast';
import api from '../api/client';

export default function Merge() {
  const { files, error, addFiles, removeFile, clearFiles } = useFileUpload({
    accept: '.pdf',
    multiple: true,
  });
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);

  const handleMerge = async () => {
    if (files.length < 2) {
      showToast('Please upload at least 2 PDF files', 'error');
      return;
    }

    setLoading(true);
    setProgress(0);

    const formData = new FormData();
    files.forEach((file) => formData.append('files', file));

    try {
      const res = await api.post('/api/merge', formData, {
        responseType: 'blob',
        onUploadProgress: (e) => {
          if (e.total) setProgress((e.loaded / e.total) * 100);
        },
      });

      const url = URL.createObjectURL(res.data);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'merged.pdf';
      a.click();
      URL.revokeObjectURL(url);
      showToast('PDFs merged successfully!', 'success');
      clearFiles();
    } catch (err) {
      showToast(err instanceof Error ? err.message : 'Merge failed', 'error');
    } finally {
      setLoading(false);
      setProgress(0);
    }
  };

  return (
    <div>
      <div className="mb-8 border-b border-[#252320] pb-6">
        <h1 className="font-serif text-3xl md:text-4xl font-normal text-[#faf9f5] mb-2">Merge PDFs</h1>
        <p className="text-[#a09d96] text-base">
          Combine multiple PDF files into a single document.
        </p>
      </div>

      <FileUpload
        accept=".pdf"
        multiple
        onFilesSelected={addFiles}
        label="Drop PDFs here or tap to select"
        className="mb-6"
      />

      {error && (
        <p className="text-[#c64545] text-sm mb-4">{error}</p>
      )}

      {files.length > 0 && (
        <div className="mb-6">
          <div className="flex items-center justify-between mb-3">
            <p className="text-sm font-medium text-[#faf9f5]">{files.length} file{files.length > 1 ? 's' : ''} selected</p>
            <button onClick={clearFiles} className="text-sm text-[#cc785c] hover:underline cursor-pointer">
              Clear all
            </button>
          </div>
          <div className="space-y-2">
            {files.map((file, i) => (
              <div key={i} className="flex items-center justify-between bg-[#252320] border border-[#373430] rounded-[12px] px-4 py-3">
                <div className="flex items-center gap-3 min-w-0">
                  <Layers className="w-4 h-4 shrink-0 text-[#cc785c]" />
                  <span className="text-sm font-medium text-[#faf9f5] truncate">{file.name}</span>
                  <span className="text-xs text-[#8e8b82] shrink-0">
                    {(file.size / 1024 / 1024).toFixed(1)}MB
                  </span>
                </div>
                <button onClick={() => removeFile(i)} className="p-1 hover:bg-[#181715] rounded-[6px] transition-colors cursor-pointer">
                  <Trash2 className="w-4 h-4 text-[#8e8b82] hover:text-[#c64545]" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {loading && <ProgressBar progress={progress} label="Merging..." className="mb-6" />}

      <Button onClick={handleMerge} disabled={files.length < 2 || loading} className="w-full">
        {loading ? 'Merging...' : 'Merge PDFs'}
      </Button>
    </div>
  );
}

