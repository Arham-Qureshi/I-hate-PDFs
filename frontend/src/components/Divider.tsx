interface DividerProps {
  className?: string;
}

export default function Divider({ className = '' }: DividerProps) {
  return <hr className={`border-0 border-t border-[var(--border-color)] my-16 ${className}`} />;
}
