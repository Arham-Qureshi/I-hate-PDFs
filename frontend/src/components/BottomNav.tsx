import { NavLink } from 'react-router-dom';
import { Layers, Scissors, ArrowLeftRight, Minimize2, MoreHorizontal } from 'lucide-react';
import { useState } from 'react';

const mainItems = [
  { to: '/merge', icon: Layers, label: 'Merge' },
  { to: '/split', icon: Scissors, label: 'Split' },
  { to: '/convert', icon: ArrowLeftRight, label: 'Convert' },
  { to: '/compress/pdf', icon: Minimize2, label: 'Compress' },
];

const moreItems = [
  { to: '/jpeg-to-pdf', label: 'JPEG → PDF' },
  { to: '/image-convert', label: 'Image Convert' },
  { to: '/compress/docx', label: 'Compress DOCX' },
];

export default function BottomNav() {
  const [moreOpen, setMoreOpen] = useState(false);

  return (
    <>
      {moreOpen && (
        <div
          className="fixed inset-0 bg-[#141413]/40 backdrop-blur-xs z-40"
          onClick={() => setMoreOpen(false)}
        />
      )}

      {moreOpen && (
        <div className="fixed bottom-[72px] left-4 right-4 bg-[#181715] border border-[#252320] rounded-[12px] p-2 z-50 shadow-lg text-[#faf9f5]">
          {moreItems.map(item => (
            <NavLink
              key={item.to}
              to={item.to}
              onClick={() => setMoreOpen(false)}
              className={({ isActive }) =>
                `block px-4 py-3 rounded-[8px] text-[14px] font-medium transition-colors ${
                  isActive
                    ? 'bg-[#252320] text-[#cc785c]'
                    : 'text-[#a09d96] hover:bg-[#252320] hover:text-[#faf9f5]'
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </div>
      )}

      <nav className="fixed bottom-0 left-0 right-0 h-[64px] bg-[#181715] border-t border-[#252320] flex items-center justify-around px-2 z-30 lg:hidden" style={{ paddingBottom: 'env(safe-area-inset-bottom)' }}>
        {mainItems.map(item => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `flex flex-col items-center gap-1 py-1.5 px-3 rounded-[8px] transition-colors ${
                isActive
                  ? 'text-[#cc785c] font-medium'
                  : 'text-[#a09d96] hover:text-[#faf9f5]'
              }`
            }
          >
            <item.icon className="w-5 h-5" />
            <span className="text-[11px]">{item.label}</span>
          </NavLink>
        ))}

        <button
          onClick={() => setMoreOpen(!moreOpen)}
          className={`flex flex-col items-center gap-1 py-1.5 px-3 rounded-[8px] transition-colors ${
            moreOpen ? 'text-[#cc785c]' : 'text-[#a09d96] hover:text-[#faf9f5]'
          }`}
        >
          <MoreHorizontal className="w-5 h-5" />
          <span className="text-[11px]">More</span>
        </button>
      </nav>
    </>
  );
}
