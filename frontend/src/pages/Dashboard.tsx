import { Link } from 'react-router-dom';
import { Layers, Scissors, ArrowLeftRight, Minimize2, Image, RefreshCw, Shield, Zap, Globe, ArrowRight, Lock } from 'lucide-react';
import Card from '../components/Card';


const tools = [
  { to: '/merge', icon: Layers, title: 'Merge PDFs', description: 'Combine multiple PDF files into a single structured document.' },
  { to: '/split', icon: Scissors, title: 'Split PDF', description: 'Extract specific page ranges into separate downloadable files.' },
  { to: '/convert', icon: ArrowLeftRight, title: 'PDF ↔ DOCX', description: 'Convert between PDF and editable Word files seamlessly.' },
  { to: '/compress/pdf', icon: Minimize2, title: 'Compress PDF', description: 'Reduce PDF file size drastically without quality loss.' },
  { to: '/jpeg-to-pdf', icon: Image, title: 'JPEG → PDF', description: 'Convert image files into clean standard PDF documents.' },
  { to: '/image-convert', icon: RefreshCw, label: 'Image Convert', title: 'Image Convert', description: 'Transform between JPEG and PNG formats instantly.' },
];

const features = [
  { icon: Shield, title: 'Privacy First', description: 'All file manipulation runs purely in-memory. Zero server storage.' },
  { icon: Zap, title: 'Fast Engine', description: 'PyMuPDF powered engine built for ultra-fast processing speeds.' },
  { icon: Globe, title: 'Open Source', description: '100% transparent architecture. Host on your own infrastructure.' },
];

export default function Dashboard() {
  return (
    <div className="space-y-16 md:space-y-24">
      {/* Editorial Hero Section */}
      <section className="pt-4 pb-6 border-b border-[#252320]">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#252320] border border-[#373430] text-[#cc785c] text-xs font-semibold uppercase tracking-wider mb-6">
          <Lock className="w-3.5 h-3.5" />
          In-Memory Processing
        </div>
        <h1 className="font-serif text-4xl md:text-6xl lg:text-7xl font-normal leading-[1.05] tracking-[-1.5px] text-[#faf9f5] mb-6 max-w-3xl">
          Meet your simple, private document workspace.
        </h1>
        <p className="text-lg md:text-xl text-[#a09d96] max-w-2xl font-normal leading-relaxed">
          Manipulate, convert, compress, and edit your PDFs without signing up or uploading files to permanent cloud storage.
        </p>
      </section>

      {/* Grid of Tools */}
      <section>
        <div className="flex items-center justify-between mb-8">
          <h2 className="font-serif text-2xl md:text-3xl font-normal text-[#faf9f5]">
            Essential Tools
          </h2>
          <span className="text-sm text-[#8e8b82]">6 utilities available</span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5 md:gap-6">
          {tools.map((tool) => (
            <Link key={tool.to} to={tool.to} className="group">
              <Card hover variant="card" className="h-full flex flex-col justify-between group-hover:-translate-y-0.5 transition-transform duration-200">
                <div>
                  <div className="w-10 h-10 rounded-[8px] bg-[#181715] border border-[#373430] flex items-center justify-center mb-5 text-[#cc785c]">
                    <tool.icon className="w-5 h-5" />
                  </div>
                  <h3 className="text-lg font-medium text-[#faf9f5] mb-2 flex items-center justify-between">
                    {tool.title}
                    <ArrowRight className="w-4 h-4 text-[#8e8b82] group-hover:text-[#cc785c] group-hover:translate-x-1 transition-all" />
                  </h3>
                  <p className="text-sm text-[#a09d96] leading-relaxed">{tool.description}</p>
                </div>
              </Card>
            </Link>
          ))}
        </div>
      </section>

      {/* Dark Product Showcase / Feature Band */}
      <section className="bg-[#181715] text-[#faf9f5] rounded-[16px] p-8 md:p-12 border border-[#252320]">
        <div className="max-w-3xl mb-10">
          <span className="text-[#cc785c] text-xs font-semibold uppercase tracking-widest">Architectural Guarantees</span>
          <h2 className="font-serif text-3xl md:text-4xl font-normal tracking-tight mt-2 mb-4">
            Built for security and compliance.
          </h2>
          <p className="text-[#a09d96] text-base leading-relaxed">
            Every document processing step occurs strictly in memory inside ephemeral BytesIO buffers. No temporary files persist across requests.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-6 border-t border-[#252320]">
          {features.map((feature) => (
            <div key={feature.title} className="bg-[#252320] rounded-[12px] p-6 border border-[#373430]">
              <feature.icon className="w-6 h-6 mb-3 text-[#cc785c]" />
              <h3 className="text-base font-medium text-[#faf9f5] mb-2">{feature.title}</h3>
              <p className="text-sm text-[#a09d96] leading-relaxed">{feature.description}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

