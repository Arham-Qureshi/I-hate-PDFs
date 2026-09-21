import { useState } from 'react';

import FileUpload from '../components/FileUpload';
import Button from '../components/Button';
import { useFileUpload } from '../hooks/useFileUpload';
import { showToast } from '../components/Toast';
import api from '../api/client';

type Mode = 'pdf-to-docx' | 'docx-to-pdf';

export default function Convert() {
  const [mode, setMode] = useState<Mode>('pdf-to-docx');
  const accept = mode === 'pdf-to-docx' ? '.pdf' : '.docx';
  const { files, error, addFiles, clearFiles } = useFileUpload({ accept, multiple: false });
  const [loading, setLoading] = useState(false);

  const handleConvert = async () => {
    if (files.length === 0) {
      showToast('Please upload a file', 'error');
      return;
    }

    setLoading(true);
    const formData = new FormData();
    formData.append('file', files[0]);

    const endpoint = mode === 'pdf-to-docx' ? '/api/convert/pdf-to-docx' : '/api/convert/docx-to-pdf';

    try {
      const res = await api.post(endpoint, formData, { responseType: 'blob' });
      const contentDisposition = res.headers['content-disposition'];
      const filename = contentDisposition?.match(/filename="?(.+?)"?$/)?.[1] || (mode === 'pdf-to-docx' ? 'converted.docx' : 'converted.pdf');

      const url = URL.createObjectURL(res.data);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      a.click();
      URL.revokeObjectURL(url);
      showToast('Conversion successful!', 'success');
      clearFiles();
    } catch (err) {
      showToast(err instanceof Error ? err.message : 'Conversion failed', 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="mb-8 border-b border-[#252320] pb-6">
        <h1 className="font-serif text-3xl md:text-4xl font-normal text-[#faf9f5] mb-2">Convert Documents</h1>
        <p className="text-[#a09d96] text-base">
          Convert between PDF and editable Word files seamlessly.
        </p>
      </div>

      <div className="flex gap-2 mb-6 bg-[#252320] border border-[#373430] rounded-[8px] p-1">
        <button
          onClick={() => { setMode('pdf-to-docx'); clearFiles(); }}
          className={`flex-1 py-2 px-4 rounded-[6px] text-sm font-medium transition-all ${
            mode === 'pdf-to-docx'
              ? 'bg-[#cc785c] text-white shadow-xs'
              : 'text-[#a09d96] hover:text-[#faf9f5]'
          }`}
        >
          PDF → DOCX
        </button>
        <button
          onClick={() => { setMode('docx-to-pdf'); clearFiles(); }}
          className={`flex-1 py-2 px-4 rounded-[6px] text-sm font-medium transition-all ${
            mode === 'docx-to-pdf'
              ? 'bg-[#cc785c] text-white shadow-xs'
              : 'text-[#a09d96] hover:text-[#faf9f5]'
          }`}
        >
          DOCX → PDF
        </button>
      </div>

      <FileUpload
        accept={accept}
        multiple={false}
        onFilesSelected={addFiles}
        label={mode === 'pdf-to-docx' ? 'Drop a PDF here' : 'Drop a DOCX here'}
        className="mb-6"
      />

      {error && <p className="text-[#c64545] text-sm mb-4">{error}</p>}

      <Button onClick={handleConvert} disabled={files.length === 0 || loading} className="w-full">
        {loading ? 'Converting...' : 'Convert File'}
      </Button>
    </div>
  );
}

