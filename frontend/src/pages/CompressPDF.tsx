import { useState } from 'react';

import FileUpload from '../components/FileUpload';
import Button from '../components/Button';
import ProgressBar from '../components/ProgressBar';
import { useFileUpload } from '../hooks/useFileUpload';
import { showToast } from '../components/Toast';
import api from '../api/client';

export default function CompressPDF() {
  const { files, error, addFiles, clearFiles } = useFileUpload({ accept: '.pdf', multiple: false });
  const [strength, setStrength] = useState('medium');
  const [loading, setLoading] = useState(false);

  const handleCompress = async () => {
    if (files.length === 0) {
      showToast('Please upload a PDF', 'error');
      return;
    }

    setLoading(true);
    const formData = new FormData();
    formData.append('file', files[0]);
    formData.append('strength', strength);

    try {
      const res = await api.post('/api/compress/pdf', formData, { responseType: 'blob' });
      const contentDisposition = res.headers['content-disposition'];
      const filename = contentDisposition?.match(/filename="?(.+?)"?$/)?.[1] || 'compressed.pdf';

      const url = URL.createObjectURL(res.data);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      a.click();
      URL.revokeObjectURL(url);
      showToast('PDF compressed successfully!', 'success');
      clearFiles();
    } catch (err) {
      showToast(err instanceof Error ? err.message : 'Compression failed', 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="mb-8 border-b border-[#252320] pb-6">
        <h1 className="font-serif text-3xl md:text-4xl font-normal text-[#faf9f5] mb-2">Compress PDF</h1>
        <p className="text-[#a09d96] text-base">
          Reduce PDF file size without sacrificing readability or image quality.
        </p>
      </div>

      <FileUpload
        accept=".pdf"
        multiple={false}
        onFilesSelected={addFiles}
        label="Drop a PDF here or tap to select"
        className="mb-6"
      />

      {error && <p className="text-[#c64545] text-sm mb-4">{error}</p>}

      <div className="mb-6">
        <label className="block text-sm font-medium text-[#faf9f5] mb-3">Compression Level</label>
        <div className="flex gap-2.5">
          {[
            { value: 'low', label: 'Slim (Light)' },
            { value: 'medium', label: 'Medium (Balanced)' },
            { value: 'high', label: 'Ultra (Maximum)' },
          ].map((opt) => (
            <button
              key={opt.value}
              type="button"
              onClick={() => setStrength(opt.value)}
              className={`flex-1 py-2.5 px-3 rounded-[8px] text-xs md:text-sm font-medium border transition-all cursor-pointer ${
                strength === opt.value
                  ? 'bg-[#cc785c] text-white border-[#cc785c] shadow-xs'
                  : 'bg-[#181715] border-[#373430] text-[#a09d96] hover:border-[#cc785c]'
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      {loading && <ProgressBar progress={50} label="Compressing PDF..." className="mb-6" />}

      <Button onClick={handleCompress} disabled={files.length === 0 || loading} className="w-full">
        {loading ? 'Compressing...' : 'Compress PDF'}
      </Button>
    </div>
  );
}

