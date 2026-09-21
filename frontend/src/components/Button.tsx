import { type ButtonHTMLAttributes, forwardRef } from 'react';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'secondary-dark' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = 'primary', size = 'md', className = '', children, ...props }, ref) => {
    const baseStyles = 'inline-flex items-center justify-center font-semibold tracking-normal transition-all duration-150 rounded-[8px] cursor-pointer disabled:bg-[#252320] disabled:text-[#6c6a64] disabled:cursor-not-allowed disabled:border disabled:border-[#373430] disabled:shadow-none';

    const variantStyles = {
      primary: 'bg-[#cc785c] text-white hover:bg-[#a9583e] active:bg-[#a9583e] shadow-xs',
      secondary: 'bg-[#252320] text-[#faf9f5] border border-[#373430] hover:border-[#cc785c]',
      'secondary-dark': 'bg-[#181715] text-[#faf9f5] border border-[#252320] hover:bg-[#252320]',
      ghost: 'bg-transparent text-[#faf9f5] hover:underline',
    };

    const sizeStyles = {
      sm: 'px-3 py-1.5 text-xs h-8',
      md: 'px-5 py-2.5 text-sm h-11',
      lg: 'px-6 py-3.5 text-base h-12',
    };

    return (
      <button
        ref={ref}
        className={`${baseStyles} ${variantStyles[variant]} ${sizeStyles[size]} ${className}`}
        {...props}
      >
        {children}
      </button>
    );
  }
);


Button.displayName = 'Button';

export default Button;

