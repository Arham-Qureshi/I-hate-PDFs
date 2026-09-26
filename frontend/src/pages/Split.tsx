import { useState, useEffect, useCallback } from 'react';
import { Info } from 'lucide-react';
import FileUpload from '../components/FileUpload';
import Button from '../components/Button';
import { useFileUpload } from '../hooks/useFileUpload';
import { showToast } from '../components/Toast';
import api from '../api/client';

interface PageThumbnail {
  page: number;
  image: string;
}

interface ManualGroup {
  id: number;
  range: string;
}

type Mode = 'extract' | 'manual';

export default function Split() {
  const { files, error, addFiles, clearFiles } = useFileUpload({
    accept: '.pdf',
    multiple: false,
  });
  const [mode, setMode] = useState<Mode>('extract');
  const [thumbnails, setThumbnails] = useState<PageThumbnail[]>([]);
  const [selectedPages, setSelectedPages] = useState<Set<number>>(new Set());
  const [manualGroups, setManualGroups] = useState<ManualGroup[]>([{ id: 1, range: '' }]);
  const [mergeOutput, setMergeOutput] = useState(false);
  const [loading, setLoading] = useState(false);
  const [thumbLoading, setThumbLoading] = useState(false);
  const [nextGroupId, setNextGroupId] = useState(2);

  const loadThumbnails = useCallback(async (file: File) => {
    setThumbLoading(true);
    const formData = new FormData();
    formData.append('file', file);
    try {
      const res = await api.post('/api/split/thumbnails', formData);
      setThumbnails(res.data.pages);
    } catch {
      setThumbnails([]);
    } finally {
      setThumbLoading(false);
    }
  }, []);

  const handleFilesSelected = async (fileList: FileList) => {
    addFiles(fileList);
    setSelectedPages(new Set());
    setManualGroups([{ id: 1, range: '' }]);
    if (fileList.length > 0) {
      loadThumbnails(fileList[0]);
    }
  };

  useEffect(() => {
    if (files.length === 0) {
      setThumbnails([]);
      setSelectedPages(new Set());
    }
  }, [files]);

  function togglePage(page: number) {
    setSelectedPages(prev => {
      const next = new Set(prev);
      if (next.has(page)) next.delete(page);
      else next.add(page);
      return next;
    });
  }

  function addGroup() {
    setManualGroups(prev => [...prev, { id: nextGroupId, range: '' }]);
    setNextGroupId(prev => prev + 1);
  }

  function removeGroup(id: number) {
    setManualGroups(prev => prev.filter(g => g.id !== id));
  }

  function updateGroupRange(id: number, range: string) {
    setManualGroups(prev => prev.map(g => g.id === id ? { ...g, range } : g));
  }

  function buildRangeGroups(): string[] {
    if (mode === 'extract') {
      const sorted = Array.from(selectedPages).sort((a, b) => a - b);
      if (sorted.length === 0) return [];
      if (mergeOutput) return [sorted.join(',')];
      const groups: string[] = [];
      let start = sorted[0];
      let end = sorted[0];
      for (let i = 1; i < sorted.length; i++) {
        if (sorted[i] === end + 1) {
          end = sorted[i];
        } else {
          groups.push(start === end ? String(start) : `${start}-${end}`);
          start = sorted[i];
          end = sorted[i];
        }
      }
      groups.push(start === end ? String(start) : `${start}-${end}`);
      return groups;
    }
    const validRanges = manualGroups.map(g => g.range.trim()).filter(Boolean);
    if (validRanges.length === 0) return [];
    if (mergeOutput) return [validRanges.join(',')];
    return validRanges;
  }

  function parseRangePages(rangeStr: string): { first: number; last: number } | null {
    const parts = rangeStr.split(',').map(s => s.trim()).filter(Boolean);
    if (parts.length === 0) return null;
    let first = Infinity;
    let last = -Infinity;
    for (const part of parts) {
      const dashMatch = part.match(/^(\d+)\s*-\s*(\d+)$/);
      if (dashMatch) {
        const s = parseInt(dashMatch[1], 10);
        const e = parseInt(dashMatch[2], 10);
        if (s < first) first = s;
        if (e > last) last = e;
      } else if (/^\d+$/.test(part)) {
        const n = parseInt(part, 10);
        if (n < first) first = n;
        if (n > last) last = n;
      } else {
        return null;
      }
    }
    return first === Infinity ? null : { first, last };
  }

  function countOutputPDFs(): number {
    if (mode === 'extract') {
      if (selectedPages.size === 0) return 0;
      if (mergeOutput) return 1;
      const sorted = Array.from(selectedPages).sort((a, b) => a - b);
      let groups = 1;
      for (let i = 1; i < sorted.length; i++) {
        if (sorted[i] !== sorted[i - 1] + 1) groups++;
      }
      return groups;
    }
    const validCount = manualGroups.filter(g => g.range.trim()).length;
    if (validCount === 0) return 0;
    return mergeOutput ? 1 : validCount;
  }

  function canSplit(): boolean {
    return files.length > 0 && buildRangeGroups().length > 0;
  }

  const handleSplit = async () => {
    const groups = buildRangeGroups();
    if (groups.length === 0) {
      showToast('Please select pages or enter ranges', 'error');
      return;
    }

    setLoading(true);

    try {
      const formData = new FormData();
      formData.append('file', files[0]);
      formData.append('ranges', groups.join(','));
      formData.append('merge', String(mergeOutput));
      const res = await api.post('/api/split', formData, { responseType: 'blob' });
      const contentDisposition = res.headers['content-disposition'];
      const filename = contentDisposition?.match(/filename="?(.+?)"?$/)?.[1] || 'split.pdf';
      const url = URL.createObjectURL(res.data);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      a.click();
      URL.revokeObjectURL(url);
      showToast('PDF split successfully!', 'success');
    } catch (err) {
      showToast(err instanceof Error ? err.message : 'Split failed', 'error');
    } finally {
      setLoading(false);
    }
  };

  const pdfCount = countOutputPDFs();

  return (
    <div>
      <div className="mb-8 border-b border-[#252320] pb-6">
        <h1 className="font-serif text-3xl md:text-4xl font-normal text-[#faf9f5] mb-2">Split PDF</h1>
        <p className="text-[#a09d96] text-base">
          Extract specific pages into separate files.
        </p>
      </div>

      {thumbnails.length === 0 ? (
        <FileUpload
          accept=".pdf"
          multiple={false}
          onFilesSelected={handleFilesSelected}
          label="Drop a PDF here or tap to select"
          className="mb-6"
        />
      ) : (
        <div className="flex flex-col lg:flex-row gap-6">
          {/* Left panel — Thumbnails */}
          <div className="flex-[3] min-w-0">
            {thumbLoading ? (
              <div className="flex items-center justify-center py-20 bg-[#252320] border border-[#373430] rounded-[12px]">
                <p className="text-[#a09d96] text-sm">Loading page previews...</p>
              </div>
            ) : (
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4 max-h-[60vh] overflow-y-auto pr-2">
                {thumbnails.map(thumb => {
                  const isSelected = selectedPages.has(thumb.page);
                  return (
                    <button
                      key={thumb.page}
                      onClick={() => mode === 'extract' && togglePage(thumb.page)}
                      className={`relative rounded-[10px] border-2 overflow-hidden transition-all duration-150 cursor-pointer ${
                        isSelected
                          ? 'border-[#5db872] shadow-[0_0_0_1px_#5db872]'
                          : 'border-[#373430] hover:border-[#cc785c]'
                      }`}
                    >
                      {isSelected && (
                        <div className="absolute top-1.5 left-1.5 z-10 w-5 h-5 rounded-full bg-[#5db872] flex items-center justify-center">
                          <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                          </svg>
                        </div>
                      )}
                      <img
                        src={`data:image/jpeg;base64,${thumb.image}`}
                        alt={`Page ${thumb.page}`}
                        className="w-full aspect-[3/4] object-contain bg-[#1f1e1b]"
                      />
                      <div className="py-1.5 text-center text-xs text-[#a09d96] font-medium">
                        {thumb.page}
                      </div>
                    </button>
                  );
                })}
              </div>
            )}
          </div>

          {/* Right panel — Controls */}
          <div className="flex-1 min-w-[280px]">
            <h2 className="font-serif text-2xl font-normal text-[#faf9f5] mb-5">Split</h2>

            {/* Mode toggle */}
            <div className="flex gap-2 mb-5 bg-[#252320] border border-[#373430] rounded-[8px] p-1">
              <button
                onClick={() => setMode('extract')}
                className={`flex-1 py-2 px-4 rounded-[6px] text-sm font-medium transition-all cursor-pointer ${
                  mode === 'extract'
                    ? 'bg-[#cc785c] text-white shadow-xs'
                    : 'text-[#a09d96] hover:text-[#faf9f5]'
                }`}
              >
                Extract
              </button>
              <button
                onClick={() => setMode('manual')}
                className={`flex-1 py-2 px-4 rounded-[6px] text-sm font-medium transition-all cursor-pointer ${
                  mode === 'manual'
                    ? 'bg-[#cc785c] text-white shadow-xs'
                    : 'text-[#a09d96] hover:text-[#faf9f5]'
                }`}
              >
                Manual
              </button>
            </div>

            {/* Mode content */}
            {mode === 'extract' ? (
              <p className="text-sm text-[#8e8b82] mb-5">
                Click pages on the left to select them for extraction.
              </p>
            ) : (
              <div className="space-y-3 mb-5">
                {manualGroups.map(group => {
                  const rangePages = parseRangePages(group.range);
                  const firstThumb = rangePages ? thumbnails.find(t => t.page === rangePages.first) : null;
                  const lastThumb = rangePages ? thumbnails.find(t => t.page === rangePages.last) : null;
                  const showBoth = rangePages && rangePages.first !== rangePages.last;
                  return (
                    <div key={group.id}>
                      <div className="flex items-center gap-2">
                        <input
                          type="text"
                          value={group.range}
                          onChange={e => updateGroupRange(group.id, e.target.value)}
                          placeholder="e.g. 1-3, 5, 7-10"
                          className="flex-1 px-3 py-2.5 bg-[#181715] border border-[#373430] rounded-[8px] text-sm text-[#faf9f5] placeholder:text-[#6c6a64] focus:outline-none focus:border-[#cc785c] transition-all"
                        />
                        {manualGroups.length > 1 && (
                          <button
                            onClick={() => removeGroup(group.id)}
                            className="p-2 text-[#8e8b82] hover:text-[#c64545] transition-colors cursor-pointer"
                          >
                            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                            </svg>
                          </button>
                        )}
                      </div>
                      {rangePages && firstThumb && (
                        <div className="flex items-center gap-2 mt-2 pl-1">
                          <div className="w-10 h-13 rounded-[4px] overflow-hidden border border-[#373430] bg-[#1f1e1b] flex-shrink-0">
                            <img
                              src={`data:image/jpeg;base64,${firstThumb.image}`}
                              alt={`Page ${rangePages.first}`}
                              className="w-full h-full object-contain"
                            />
                          </div>
                          {showBoth && lastThumb && (
                            <>
                              <span className="text-[10px] text-[#6c6a64]">→</span>
                              <div className="w-10 h-13 rounded-[4px] overflow-hidden border border-[#373430] bg-[#1f1e1b] flex-shrink-0">
                                <img
                                  src={`data:image/jpeg;base64,${lastThumb.image}`}
                                  alt={`Page ${rangePages.last}`}
                                  className="w-full h-full object-contain"
                                />
                              </div>
                            </>
                          )}
                          <span className="text-[10px] text-[#6c6a64]">
                            {rangePages.first === rangePages.last
                              ? `Page ${rangePages.first}`
                              : `Pages ${rangePages.first}–${rangePages.last}`}
                          </span>
                        </div>
                      )}
                    </div>
                  );
                })}
                <button
                  onClick={addGroup}
                  className="text-sm text-[#cc785c] hover:underline cursor-pointer font-medium"
                >
                  + Add range
                </button>
              </div>
            )}

            {/* Merge checkbox */}
            <label className="flex items-center gap-3 mb-4 cursor-pointer">
              <input
                type="checkbox"
                checked={mergeOutput}
                onChange={e => setMergeOutput(e.target.checked)}
                className="w-4 h-4 rounded border-[#373430] bg-[#181715] accent-[#cc785c] cursor-pointer"
              />
              <span className="text-sm text-[#a09d96]">Merge extracted pages into one PDF file</span>
            </label>

            {/* Info box */}
            {pdfCount > 0 && (
              <div className="flex items-start gap-2.5 px-4 py-3 rounded-[8px] bg-[#1a2332] border border-[#2a3a50] mb-5">
                <Info className="w-4 h-4 text-[#5b9bd5] shrink-0 mt-0.5" />
                <p className="text-sm text-[#a09d96]">
                  {pdfCount === 1
                    ? 'Selected pages will be merged into 1 PDF file.'
                    : `Selected pages will be converted into separate PDF files. ${pdfCount} PDFs will be created.`}
                </p>
              </div>
            )}

            {/* Action button */}
            <Button
              onClick={handleSplit}
              disabled={!canSplit() || loading}
              className="w-full"
            >
              {loading ? 'Splitting...' : 'Split PDF'}
            </Button>

            {/* Re-upload */}
            <button
              onClick={() => { clearFiles(); setThumbnails([]); setSelectedPages(new Set()); setManualGroups([{ id: 1, range: '' }]); }}
              className="w-full mt-3 text-sm text-[#8e8b82] hover:text-[#cc785c] transition-colors cursor-pointer py-2"
            >
              Upload a different PDF
            </button>
          </div>
        </div>
      )}

      {error && <p className="text-[#c64545] text-sm mt-4">{error}</p>}
    </div>
  );
}
