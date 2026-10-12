import React from 'react';
import { Link, useLocation } from 'react-router-dom';

export default function Navbar({ maxWidth = "max-w-6xl" }) {
  const location = useLocation();
  const currentPath = location.pathname;

  return (
    <header className={`${maxWidth} mx-auto px-6 h-16 flex items-center justify-between`}>
      {/* Brand Logo */}
      <Link className="flex items-center space-x-2.5 group" to="/">
        <div className="w-9 h-9 rounded-[12px] bg-gradient-to-br from-amber-400 via-orange-500 to-amber-600 flex items-center justify-center p-1.5 shadow-sm group-hover:scale-105 transition-transform">
          <img src="/static/images/logo.png" alt="DispatchLens Logo" className="w-full h-full object-contain" />
        </div>
        <span className="text-xl font-bold tracking-tight text-white">DispatchLens</span>
      </Link>

      {/* Right Navigation Items */}
      <nav className="flex items-center space-x-5 text-xs font-medium">
        <Link
          className={currentPath === '/' ? "text-white font-semibold transition-colors" : "text-slate-200 hover:text-white transition-colors"}
          to="/"
        >
          Scraper
        </Link>
        <Link
          className={currentPath === '/generator/' || currentPath === '/generator' ? "text-white font-semibold transition-colors" : "text-slate-200 hover:text-white transition-colors"}
          to="/generator/"
        >
          Generator
        </Link>
        {/* Premium Badge */}
        <Link
          className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-500 hover:bg-amber-600 text-slate-900 shadow-sm transition-colors"
          to="/refund-policy/"
        >
          <svg className="w-3.5 h-3.5 mr-1" fill="currentColor" viewBox="0 0 20 20">
            <path clipRule="evenodd" d="M10 2l2.5 4.5L18 7.5l-4 4 1 5.5-5-2.5-5 2.5 1-5.5-4-4 5.5-1L10 2z" fillRule="evenodd"></path>
          </svg>
          Premium
        </Link>
        {/* User ID Tag */}
        <div className="inline-flex items-center px-2.5 py-1 rounded-md bg-[#163155] border border-slate-700/60 text-slate-300 text-xs">
          <svg className="w-3.5 h-3.5 mr-1.5 text-slate-400 cursor-pointer hover:text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <rect height="14" rx="2" ry="2" strokeWidth="2" width="14" x="8" y="8"></rect>
            <path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2" strokeWidth="2"></path>
          </svg>
          <span>ID: 2afcd8ad...</span>
        </div>
        {/* Sign Out Action */}
        <a className="inline-flex items-center px-2.5 py-1 rounded-md bg-[#163155] border border-slate-700/60 text-slate-200 hover:text-white hover:bg-slate-700/50 transition-colors" href="#">
          <svg className="w-3.5 h-3.5 mr-1.5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
            <path d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" strokeLinecap="round" strokeLinejoin="round"></path>
          </svg>
          Sign out
        </a>
      </nav>
    </header>
  );
}
