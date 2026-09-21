import { useRef } from 'react';
import { Upload } from 'lucide-react';

interface FileUploadProps {
  accept: string;
  multiple?: boolean;
  onFilesSelected: (files: FileList) => void;
  label?: string;
  className?: string;
}

export default function FileUpload({
  accept,
  multiple = false,
  onFilesSelected,
  label = 'Drop files here or tap to select',
  className = '',
}: FileUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      onFilesSelected(e.dataTransfer.files);
    }
  };

  const handleClick = () => {
    inputRef.current?.click();
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      onFilesSelected(e.target.files);
      e.target.value = '';
    }
  };

  return (
    <div
      onDragOver={handleDragOver}
      onDrop={handleDrop}
      onClick={handleClick}
      className={`border-2 border-dashed border-[#373430] bg-[#252320]/70 rounded-[16px] p-10 md:p-14 flex flex-col items-center justify-center gap-3.5 cursor-pointer transition-all duration-200 hover:border-[#cc785c] hover:border-[#cc785c] hover:bg-[#252320] group ${className}`}
    >
      <div className="w-12 h-12 rounded-full bg-[#181715] border border-[#373430] flex items-center justify-center shadow-xs group-hover:scale-105 group-hover:border-[#cc785c] transition-all">
        <Upload className="w-5 h-5 text-[#cc785c]" />
      </div>
      <p className="text-[15px] font-semibold text-[#faf9f5] text-center">{label}</p>
      <p className="text-[13px] text-[#a09d96]">Supports PDF, DOCX, JPEG, PNG</p>
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        multiple={multiple}
        onChange={handleChange}
        className="hidden"
      />
    </div>
  );
}


