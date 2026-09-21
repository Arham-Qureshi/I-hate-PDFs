import { useState } from 'react';
import { Image, Trash2 } from 'lucide-react';
import FileUpload from '../components/FileUpload';
import Button from '../components/Button';
import ProgressBar from '../components/ProgressBar';
import { useFileUpload } from '../hooks/useFileUpload';
import { showToast } from '../components/Toast';
import api from '../api/client';

export default function JPEGToPDF() {
  const { files, error, addFiles, removeFile, clearFiles } = useFileUpload({
    accept: '.jpg,.jpeg',
    multiple: true,
    maxSize: 30 * 1024 * 1024,
  });
  const [loading, setLoading] = useState(false);

  const handleConvert = async () => {
    if (files.length === 0) {
      showToast('Please upload at least one JPEG image', 'error');
      return;
    }

    setLoading(true);
    const formData = new FormData();
    files.forEach((file) => formData.append('files', file));

    try {
      const res = await api.post('/api/jpeg-to-pdf', formData, { responseType: 'blob' });
      const contentDisposition = res.headers['content-disposition'];
      const filename = contentDisposition?.match(/filename="?(.+?)"?$/)?.[1] || 'images.pdf';

      const url = URL.createObjectURL(res.data);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      a.click();
      URL.revokeObjectURL(url);
      showToast('PDF created successfully!', 'success');
      clearFiles();
    } catch (err) {
      showToast(err instanceof Error ? err.message : 'Conversion failed', 'error');
    } finally {
      setLoading(false);
    }
  };

  const totalSize = files.reduce((sum, f) => sum + f.size, 0);

  return (
    <div>
      <div className="mb-8 border-b border-[#252320] pb-6">
        <h1 className="font-serif text-3xl md:text-4xl font-normal text-[#faf9f5] mb-2">JPEG → PDF</h1>
        <p className="text-[#a09d96] text-base">
          Convert JPEG images into a single clean PDF document.
        </p>
      </div>

      <FileUpload
        accept=".jpg,.jpeg"
        multiple
        onFilesSelected={addFiles}
        label="Drop JPEG images here or tap to select"
        className="mb-6"
      />

      {error && <p className="text-[#c64545] text-sm mb-4">{error}</p>}

      {files.length > 0 && (
        <div className="mb-6 bg-[#252320] border border-[#373430] rounded-[12px] p-4">
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm font-medium text-[#faf9f5]">{files.length} image{files.length > 1 ? 's' : ''}</p>
            <p className="text-xs text-[#8e8b82]">{(totalSize / 1024 / 1024).toFixed(1)}MB total</p>
          </div>
          <button onClick={clearFiles} className="text-xs text-[#cc785c] hover:underline cursor-pointer">
            Clear all
          </button>
        </div>
      )}

      {files.length > 0 && (
        <div className="mb-6 space-y-2">
          {files.map((file, i) => (
            <div key={i} className="flex items-center justify-between bg-[#252320] border border-[#373430] rounded-[12px] px-4 py-3">
              <div className="flex items-center gap-3 min-w-0">
                <Image className="w-4 h-4 shrink-0 text-[#cc785c]" />
                <span className="text-sm font-medium text-[#faf9f5] truncate">{file.name}</span>
              </div>
              <button onClick={() => removeFile(i)} className="p-1 hover:bg-[#181715] rounded-[6px] transition-colors cursor-pointer">
                <Trash2 className="w-4 h-4 text-[#8e8b82] hover:text-[#c64545]" />
              </button>
            </div>
          ))}
        </div>
      )}

      {loading && <ProgressBar progress={50} label="Creating PDF..." className="mb-6" />}

      <Button onClick={handleConvert} disabled={files.length === 0 || loading} className="w-full">
        {loading ? 'Creating PDF...' : 'Create PDF'}
      </Button>
    </div>
  );
}

