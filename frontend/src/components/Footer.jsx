import React from 'react';
import { Link } from 'react-router-dom';

export default function Footer() {
  return (
    <footer className="bg-white border-t border-slate-200 mt-auto text-slate-600">
      <div className="max-w-7xl mx-auto px-6 lg:px-12 pt-12 pb-8">
        <div className="grid grid-cols-1 md:grid-cols-12 gap-8 lg:gap-12 pb-12 border-b border-slate-100">
          {/* Brand Info */}
          <div className="md:col-span-5 space-y-4">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-[10px] bg-gradient-to-br from-amber-400 via-orange-500 to-amber-600 flex items-center justify-center p-1 shadow-sm">
                <img src="/static/images/logo.png" alt="DispatchLens Logo" className="w-full h-full object-contain" />
              </div>
              <span className="font-bold text-lg text-slate-900 tracking-tight">DispatchLens</span>
            </div>
            <p className="text-xs sm:text-sm text-slate-500 max-w-sm leading-relaxed">
              FMCSA carrier verification built for dispatch companies, dispatch houses and freight brokers to find MC-authorized motor carriers in seconds.
            </p>
          </div>
          {/* Product Links */}
          <div className="md:col-span-2 space-y-3">
            <h3 className="text-xs font-semibold text-slate-900 uppercase tracking-wider">Product</h3>
            <ul className="space-y-2 text-xs sm:text-sm">
              <li><Link className="hover:text-slate-900 transition-colors" to="/">Carrier search</Link></li>
              <li><Link className="hover:text-slate-900 transition-colors" to="/generator/">Generator</Link></li>
            </ul>
          </div>
          {/* Legal Links */}
          <div className="md:col-span-2 space-y-3">
            <h3 className="text-xs font-semibold text-slate-900 uppercase tracking-wider">Legal</h3>
            <ul className="space-y-2 text-xs sm:text-sm">
              <li><Link className="hover:text-slate-900 transition-colors" to="/privacy/">Privacy policy</Link></li>
              <li><Link className="hover:text-slate-900 transition-colors" to="/terms/">Terms of service</Link></li>
              <li><Link className="hover:text-slate-900 transition-colors" to="/refund-policy/">Refund policy</Link></li>
            </ul>
          </div>
          {/* Contact Links */}
          <div className="md:col-span-3 space-y-3">
            <h3 className="text-xs font-semibold text-slate-900 uppercase tracking-wider">Contact</h3>
            <p className="text-xs sm:text-sm text-slate-600">
              WhatsApp: <a className="hover:text-slate-900 transition-colors" href="https://wa.me/923221945605">+92 322 1945605</a>
            </p>
          </div>
        </div>
        <div className="pt-8 flex flex-col sm:flex-row justify-between items-center text-xs text-slate-500 gap-4">
          <div>© 2026 DispatchLens. All rights reserved.</div>
          <div>Developed by <span className="font-semibold text-slate-900">DevNest Labs</span></div>
        </div>
      </div>
    </footer>
  );
}
