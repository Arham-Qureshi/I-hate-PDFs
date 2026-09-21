import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Merge from './pages/Merge';
import Split from './pages/Split';
import Convert from './pages/Convert';
import CompressPDF from './pages/CompressPDF';
import CompressDOCX from './pages/CompressDOCX';
import JPEGToPDF from './pages/JPEGToPDF';
import ImageConvert from './pages/ImageConvert';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/merge" element={<Merge />} />
          <Route path="/split" element={<Split />} />
          <Route path="/convert" element={<Convert />} />
          <Route path="/compress/pdf" element={<CompressPDF />} />
          <Route path="/compress/docx" element={<CompressDOCX />} />
          <Route path="/jpeg-to-pdf" element={<JPEGToPDF />} />
          <Route path="/image-convert" element={<ImageConvert />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
