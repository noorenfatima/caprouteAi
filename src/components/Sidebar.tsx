import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { LayoutGrid, Network, History, Radio, Lightbulb, Settings, LogOut, Landmark } from "lucide-react";

export default function Sidebar() {
  const navigate = useNavigate();

  const menu = [
    { name: "Overview", path: "/", icon: LayoutGrid },
    { name: "Routing Matrix", path: "/matrix", icon: Network },
    { name: "History", path: "/history", icon: History },
    { name: "Simulation", path: "/simulation", icon: Radio },
    { name: "Insights", path: "/insights", icon: Lightbulb },
  ];

  return (
    <div className="h-screen w-[260px] fixed left-0 top-0 bg-[#F8F6FC] flex flex-col justify-between py-8 px-4 border-r border-gray-100">
      
      {/* Top Section */}
      <div>
        {/* Logo */}
        <div className="flex items-center gap-3 px-2 mb-10">
          <div className="w-10 h-10 rounded-full bg-[#6D5DF5] flex items-center justify-center shrink-0 shadow-sm shadow-purple-500/20">
            <Landmark className="w-5 h-5 text-white" />
          </div>
          <div className="flex flex-col">
            <span className="text-xl font-bold text-gray-900 leading-none tracking-tight">CapRoute</span>
            <span className="text-[10px] font-bold text-[#6D5DF5] tracking-widest mt-1 uppercase">AI</span>
          </div>
        </div>

        {/* Menu */}
        <div className="flex flex-col gap-1">
          {menu.map((item, index) => {
            const Icon = item.icon;
            
            return (
              <NavLink
                key={index}
                to={item.path}
                className={({ isActive }) => `flex items-center gap-3 px-4 py-3 rounded-2xl cursor-pointer transition-colors ${
                  isActive
                    ? "bg-[#EBE4FF] text-[#6D5DF5] font-semibold"
                    : "text-gray-500 hover:bg-gray-100 hover:text-gray-900 font-medium"
                }`}
              >
                <Icon size={18} />
                <span className="text-sm">{item.name}</span>
              </NavLink>
            );
          })}
        </div>
      </div>

      {/* Bottom Section */}
      <div className="flex flex-col gap-1 border-t border-gray-200 pt-4 px-2">
        <button
          type="button"
          onClick={() => window.alert('Settings panel is not available yet.')}
          className="flex items-center gap-3 px-4 py-3 rounded-2xl text-gray-500 hover:bg-gray-100 hover:text-gray-900 transition-colors w-full text-left"
        >
          <Settings size={18} />
          <span className="text-sm font-medium">Settings</span>
        </button>
        <button
          type="button"
          onClick={() => {
            window.alert('You have been logged out of this demo session.');
            navigate('/');
          }}
          className="flex items-center gap-3 px-4 py-3 rounded-2xl text-[#E94E8B] hover:bg-red-50 transition-colors w-full text-left"
        >
          <LogOut size={18} />
          <span className="text-sm font-medium">Logout</span>
        </button>
      </div>
    </div>
  );
}
