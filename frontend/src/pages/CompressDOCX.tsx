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

  const handleCompress = async () => {
    if (files.length === 0) {
      showToast('Please upload a DOCX', 'error');
      return;
    }

    setLoading(true);
    const formData = new FormData();
    formData.append('file', files[0]);

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
          Reduce DOCX file size by optimizing embedded images.
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

      {loading && <ProgressBar progress={50} label="Compressing DOCX..." className="mb-6" />}

      <Button onClick={handleCompress} disabled={files.length === 0 || loading} className="w-full">
        {loading ? 'Compressing...' : 'Compress DOCX'}
      </Button>
    </div>
  );
}

