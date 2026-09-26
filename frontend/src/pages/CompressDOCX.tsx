import { useState } from 'react';

import FileUpload from '../components/FileUpload';
import Button from '../components/Button';
import ProgressBar from '../components/ProgressBar';
import { useFileUpload } from '../hooks/useFileUpload';
import { showToast } from '../components/Toast';
import api from '../api/client';

export default function CompressDOCX() {
  const { files, error, addFiles, clearFiles } = useFileUpload({ accept: '.docx', multiple: false });
  const [loading, setLoading] = useState(false);
  const [level, setLevel] = useState<'quality' | 'size'>('quality');

  const handleCompress = async () => {
    if (files.length === 0) {
      showToast('Please upload a DOCX', 'error');
      return;
    }

    setLoading(true);
    const formData = new FormData();
    formData.append('file', files[0]);
    formData.append('level', level);

    try {
      const res = await api.post('/api/compress/docx', formData, { responseType: 'blob' });
      const contentDisposition = res.headers['content-disposition'];
      const filename = contentDisposition?.match(/filename="?(.+?)"?$/)?.[1] || 'compressed.docx';

      const url = URL.createObjectURL(res.data);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      a.click();
      URL.revokeObjectURL(url);
      showToast('DOCX compressed successfully!', 'success');
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
        <h1 className="font-serif text-3xl md:text-4xl font-normal text-[#faf9f5] mb-2">Compress Word</h1>
        <p className="text-[#a09d96] text-base">
          Reduce DOCX file size by subsetting embedded fonts and optimizing images.
        </p>
      </div>

      <FileUpload
        accept=".docx"
        multiple={false}
        onFilesSelected={addFiles}
        label="Drop a DOCX file here or tap to select"
        className="mb-6"
      />

      {error && <p className="text-[#c64545] text-sm mb-4">{error}</p>}

      <div className="mb-6">
        <label className="block text-sm font-medium text-[#faf9f5] mb-3">Compression Level</label>
        <div className="flex gap-2.5">
          {[
            { value: 'quality' as const, label: 'Best Quality', desc: 'Subsets fonts, keeps images sharp' },
            { value: 'size' as const, label: 'Smallest File', desc: 'Maximum compression, images may look softer' },
          ].map((opt) => (
            <button
              key={opt.value}
              type="button"
              onClick={() => setLevel(opt.value)}
              className={`flex-1 py-2.5 px-3 rounded-[8px] text-xs md:text-sm font-medium border transition-all cursor-pointer ${
                level === opt.value
                  ? 'bg-[#cc785c] text-white border-[#cc785c] shadow-xs'
                  : 'bg-[#181715] border-[#373430] text-[#a09d96] hover:border-[#cc785c]'
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
        <p className="text-[#a09d96] text-xs mt-2">
          {level === 'quality' ? 'Subsets fonts, keeps images sharp' : 'Maximum compression, images may look softer'}
        </p>
      </div>

      {loading && <ProgressBar progress={50} label="Compressing DOCX..." className="mb-6" />}

      <Button onClick={handleCompress} disabled={files.length === 0 || loading} className="w-full">
        {loading ? 'Compressing...' : 'Compress DOCX'}
      </Button>
    </div>
  );
}

