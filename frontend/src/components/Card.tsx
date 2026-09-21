import type { ReactNode } from 'react';

interface CardProps {
  children: ReactNode;
  className?: string;
  hover?: boolean;
  variant?: 'card' | 'dark' | 'canvas';
}

export default function Card({ children, className = '', hover = false, variant = 'card' }: CardProps) {
  const variantStyles = {
    card: 'bg-[#252320] text-[#faf9f5] border border-[#373430]',
    dark: 'bg-[#181715] text-[#faf9f5] border border-[#252320]',
    canvas: 'bg-[#181715] text-[#faf9f5] border border-[#373430]',
  };

  const hoverStyles = hover
    ? 'hover:border-[#cc785c] hover:shadow-sm transition-all duration-200 cursor-pointer'
    : 'transition-colors duration-150';

  return (
    <div
      className={`rounded-[12px] p-6 md:p-8 ${variantStyles[variant]} ${hoverStyles} ${className}`}
    >
      {children}
    </div>
  );
}

