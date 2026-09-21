import { useEffect, useState } from 'react';

interface ToastMessage {
  id: string;
  message: string;
  type: 'success' | 'error';
}

let toastId = 0;
let listeners: ((message: ToastMessage) => void)[] = [];

export function showToast(message: string, type: 'success' | 'error' = 'error') {
  const id = String(++toastId);
  listeners.forEach(listener => listener({ id, message, type }));
}

export default function Toast() {
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  useEffect(() => {
    const listener = (message: ToastMessage) => {
      setToasts(prev => [...prev, message]);
      setTimeout(() => {
        setToasts(prev => prev.filter(t => t.id !== message.id));
      }, 3000);
    };
    listeners.push(listener);
    return () => {
      listeners = listeners.filter(l => l !== listener);
    };
  }, []);

  if (toasts.length === 0) return null;

  return (
    <div className="fixed top-4 right-4 z-50 flex flex-col gap-2 md:top-4 md:right-4 top-4 left-1/2 -translate-x-1/2 md:translate-x-0 md:left-auto">
      {toasts.map(toast => (
        <div
          key={toast.id}
          className={`px-5 py-3.5 rounded-[12px] text-sm font-medium shadow-md border ${
            toast.type === 'error'
              ? 'bg-[#181715] text-[#faf9f5] border-[#c64545]'
              : 'bg-[#181715] text-[#faf9f5] border-[#252320]'
          }`}
        >
          <span className={`inline-block w-2 h-2 rounded-full mr-2 ${toast.type === 'error' ? 'bg-[#c64545]' : 'bg-[#5db872]'}`} />
          {toast.message}
        </div>
      ))}
    </div>
  );
}

