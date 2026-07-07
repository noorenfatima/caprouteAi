import React from 'react';
import { Bell, Search, HelpCircle } from 'lucide-react';
import { useLocation } from 'react-router-dom';

export default function TopBar() {
  const location = useLocation();
  
  // Determine breadcrumb based on route
  let breadcrumb = "";
  if (location.pathname === '/matrix') {
    breadcrumb = "Asset Flow > Routing Matrix";
  } else if (location.pathname === '/history') {
    breadcrumb = "History";
  } else if (location.pathname === '/simulation') {
    breadcrumb = "Simulation";
  } else if (location.pathname === '/insights') {
    breadcrumb = "Insights";
  }

  return (
    <div className="h-20 bg-white flex items-center justify-between px-8 sticky top-0 z-10">
      {/* Left: Breadcrumbs or Empty (for Overview) */}
      <div className="flex-1">
        {breadcrumb && (
          <div className="text-sm font-medium text-gray-400">
            {breadcrumb.split(' > ').map((part, index, array) => (
              <span key={index}>
                {index > 0 && <span className="mx-2 text-gray-300">{'>'}</span>}
                <span className={index === array.length - 1 ? "text-[#6D5DF5] font-semibold" : ""}>
                  {part}
                </span>
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Middle: Search */}
      <div className="flex-1 flex justify-center">
        <div className="relative w-full max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input 
            type="text" 
            placeholder="Search asset routes..." 
            className="w-full bg-[#F8F9FA] border-none rounded-full pl-10 pr-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#6D5DF5]/20 transition-shadow"
          />
        </div>
      </div>

      {/* Right: Actions & Profile */}
      <div className="flex-1 flex items-center justify-end gap-5">
        <div className="flex items-center gap-2">
          <button className="p-2 text-[#6D5DF5] hover:bg-[#F8F9FA] rounded-full transition-colors relative">
            <Bell className="w-5 h-5 fill-current" />
            <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-[#E94E8B] rounded-full border-2 border-white"></span>
          </button>
          <button className="p-2 text-gray-400 hover:text-gray-600 hover:bg-[#F8F9FA] rounded-full transition-colors">
            <HelpCircle className="w-5 h-5 fill-current" />
          </button>
        </div>
        
        <div className="h-8 w-px bg-gray-200"></div>

        <div className="flex items-center gap-3">
          <div className="text-right hidden md:block">
            <p className="text-sm font-bold text-gray-900 leading-tight">Alexander Pierce</p>
            <p className="text-[10px] font-bold text-gray-400 tracking-wider uppercase">Chief Treasury</p>
          </div>
          <div className="w-10 h-10 rounded-full bg-gray-200 overflow-hidden shrink-0 border-2 border-white shadow-sm">
            <img src="https://picsum.photos/seed/alexander/100/100" alt="Alexander Pierce" referrerPolicy="no-referrer" className="w-full h-full object-cover" />
          </div>
        </div>
      </div>
    </div>
  );
}
