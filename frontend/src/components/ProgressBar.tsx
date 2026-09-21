interface ProgressBarProps {
  progress: number;
  label?: string;
  className?: string;
}

export default function ProgressBar({ progress, label, className = '' }: ProgressBarProps) {
  return (
    <div className={`w-full ${className}`}>
      {label && (
        <p className="text-sm font-medium text-[#a09d96] mb-2">{label}</p>
      )}
      <div className="w-full h-1.5 bg-[#e6dfd8] bg-[#252320] rounded-full overflow-hidden">
        <div
          className="h-full bg-[#cc785c] transition-all duration-300 ease-out"
          style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
        />
      </div>
    </div>
  );
}

