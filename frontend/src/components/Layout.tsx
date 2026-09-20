import { Outlet } from 'react-router-dom';
import Navbar from './Navbar';
import BottomNav from './BottomNav';
import Toast from './Toast';

export default function Layout() {
  return (
    <div className="min-h-screen bg-[#181715] text-[#faf9f5] flex flex-col">
      <Toast />
      <Navbar />
      <main className="flex-1 pt-16 pb-24 lg:pb-12">
        <div className="max-w-[1100px] mx-auto px-4 py-8 md:px-8 md:py-10 lg:px-12 lg:py-12">
          <Outlet />
        </div>
      </main>
      <BottomNav />
    </div>
  );
}
