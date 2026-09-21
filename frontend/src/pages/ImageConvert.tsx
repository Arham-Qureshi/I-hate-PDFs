import { useState } from 'react';
import FileUpload from '../components/FileUpload';
import Button from '../components/Button';
import { useFileUpload } from '../hooks/useFileUpload';
import { showToast } from '../components/Toast';
import api from '../api/client';

type Mode = 'jpeg-to-png' | 'png-to-jpeg';

export default function ImageConvert() {
  const [mode, setMode] = useState<Mode>('jpeg-to-png');
  const accept = mode === 'jpeg-to-png' ? '.jpg,.jpeg' : '.png';
  const { files, error, addFiles, clearFiles } = useFileUpload({ accept, multiple: false });
  const [loading, setLoading] = useState(false);

  const handleConvert = async () => {
    if (files.length === 0) {
      showToast('Please upload an image', 'error');
      return;
    }

    setLoading(true);
    const formData = new FormData();
    formData.append('file', files[0]);
    formData.append('mode', mode);

    try {
      const res = await api.post('/api/image-convert', formData, { responseType: 'blob' });
      const contentDisposition = res.headers['content-disposition'];
      const filename = contentDisposition?.match(/filename="?(.+?)"?$/)?.[1] || (mode === 'jpeg-to-png' ? 'converted.png' : 'converted.jpg');

      const url = URL.createObjectURL(res.data);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      a.click();
      URL.revokeObjectURL(url);
      showToast('Image converted successfully!', 'success');
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
        <h1 className="font-serif text-3xl md:text-4xl font-normal text-[#faf9f5] mb-2">Image Convert</h1>
        <p className="text-[#a09d96] text-base">
          Convert between JPEG and PNG image formats instantly.
        </p>
      </div>

      <div className="flex gap-2 mb-6 bg-[#252320] border border-[#373430] rounded-[8px] p-1">
        <button
          onClick={() => { setMode('jpeg-to-png'); clearFiles(); }}
          className={`flex-1 py-2 px-4 rounded-[6px] text-sm font-medium transition-all cursor-pointer ${
            mode === 'jpeg-to-png'
              ? 'bg-[#cc785c] text-white shadow-xs'
              : 'text-[#a09d96] hover:text-[#faf9f5]'
          }`}
        >
          JPEG → PNG
        </button>
        <button
          onClick={() => { setMode('png-to-jpeg'); clearFiles(); }}
          className={`flex-1 py-2 px-4 rounded-[6px] text-sm font-medium transition-all cursor-pointer ${
            mode === 'png-to-jpeg'
              ? 'bg-[#cc785c] text-white shadow-xs'
              : 'text-[#a09d96] hover:text-[#faf9f5]'
          }`}
        >
          PNG → JPEG
        </button>
      </div>

      <FileUpload
        accept={accept}
        multiple={false}
        onFilesSelected={addFiles}
        label={mode === 'jpeg-to-png' ? 'Drop a JPEG image here' : 'Drop a PNG image here'}
        className="mb-6"
      />

      {error && <p className="text-[#c64545] text-sm mb-4">{error}</p>}

      <Button onClick={handleConvert} disabled={files.length === 0 || loading} className="w-full">
        {loading ? 'Converting...' : 'Convert Image'}
      </Button>
    </div>
  );
}

