import { useState, useEffect, useRef } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { Layers, Scissors, ArrowLeftRight, Minimize2, Image, RefreshCw, ChevronDown, ShieldCheck } from 'lucide-react';

interface Tool {
  to: string;
  icon: React.ElementType;
  label: string;
}

interface Category {
  label: string;
  icon: React.ElementType;
  tools: Tool[];
}

const categories: Category[] = [
  {
    label: 'PDF',
    icon: Layers,
    tools: [
      { to: '/merge', icon: Layers, label: 'Merge PDFs' },
      { to: '/split', icon: Scissors, label: 'Split PDF' },
      { to: '/compress/pdf', icon: Minimize2, label: 'Compress PDF' },
      { to: '/jpeg-to-pdf', icon: Image, label: 'JPEG to PDF' },
    ],
  },
  {
    label: 'DOCX',
    icon: ArrowLeftRight,
    tools: [
      { to: '/convert', icon: ArrowLeftRight, label: 'Convert PDF/DOCX' },
      { to: '/compress/docx', icon: Minimize2, label: 'Compress DOCX' },
    ],
  },
  {
    label: 'Image',
    icon: RefreshCw,
    tools: [
      { to: '/image-convert', icon: RefreshCw, label: 'Image Convert' },
    ],
  },
];

export default function Navbar() {
  const [openDropdown, setOpenDropdown] = useState<string | null>(null);
  const location = useLocation();
  const navRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setOpenDropdown(null);
  }, [location.pathname]);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (navRef.current && !navRef.current.contains(e.target as Node)) {
        setOpenDropdown(null);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  useEffect(() => {
    function handleEscape(e: KeyboardEvent) {
      if (e.key === 'Escape') setOpenDropdown(null);
    }
    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, []);

  function isToolActive(tool: Tool) {
    return location.pathname === tool.to;
  }

  function isCategoryActive(cat: Category) {
    return cat.tools.some(t => location.pathname === t.to);
  }

  return (
    <nav ref={navRef} className="fixed top-0 left-0 right-0 z-30 h-16 bg-[#181715] border-b border-[#252320] px-6 flex items-center justify-between lg:flex hidden">
      <NavLink to="/" className="flex items-center gap-2.5 shrink-0">
        <span className="w-6 h-6 rounded-full bg-[#cc785c] flex items-center justify-center text-white text-xs font-bold">
          &#10045;
        </span>
        <span className="font-serif text-xl font-normal tracking-tight text-[#faf9f5]">
          I Hate PDFs
        </span>
      </NavLink>

      <div className="flex items-center gap-1">
        {categories.map(cat => {
          const isActive = isCategoryActive(cat);
          const isOpen = openDropdown === cat.label;
          return (
            <div key={cat.label} className="relative">
              <button
                onClick={() => setOpenDropdown(isOpen ? null : cat.label)}
                className={`flex items-center gap-1.5 px-3 py-2 rounded-[8px] text-[14px] font-medium transition-all duration-150 ${
                  isActive
                    ? 'text-[#cc785c] bg-[#252320]'
                    : 'text-[#a09d96] hover:text-[#faf9f5] hover:bg-[#1f1e1b]'
                }`}
              >
                <cat.icon className="w-4 h-4" />
                <span>{cat.label}</span>
                <ChevronDown className={`w-3.5 h-3.5 transition-transform duration-150 ${isOpen ? 'rotate-180' : ''}`} />
              </button>

              {isOpen && (
                <div className="absolute top-full left-0 mt-1 w-56 bg-[#252320] border border-[#373430] rounded-[10px] py-1.5 shadow-xl z-50">
                  {cat.tools.map(tool => (
                    <NavLink
                      key={tool.to}
                      to={tool.to}
                      className={`flex items-center gap-3 px-4 py-2.5 text-[14px] font-medium transition-colors ${
                        isToolActive(tool)
                          ? 'text-[#cc785c] bg-[#1f1e1b]'
                          : 'text-[#a09d96] hover:text-[#faf9f5] hover:bg-[#1f1e1b]'
                      }`}
                    >
                      <tool.icon className="w-4 h-4 shrink-0" />
                      <span>{tool.label}</span>
                    </NavLink>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>

      <div className="flex items-center gap-2 px-3 py-1.5 rounded-[8px] bg-[#252320] border border-[#373430] text-xs text-[#a09d96] shrink-0">
        <ShieldCheck className="w-3.5 h-3.5 text-[#5db872]" />
        <span>In-Memory</span>
      </div>
    </nav>
  );
}
