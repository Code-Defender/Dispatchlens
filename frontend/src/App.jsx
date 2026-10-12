import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Footer from './components/Footer';
import SearchPage from './components/SearchPage';
import GeneratorPage from './components/GeneratorPage';
import PrivacyPage from './pages/PrivacyPage';
import TermsPage from './pages/TermsPage';
import RefundPage from './pages/RefundPage';

export default function App() {
  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      <div className="flex-grow">
        <Routes>
          <Route path="/" element={<SearchPage />} />
          <Route path="/generator/" element={<GeneratorPage />} />
          <Route path="/generator" element={<GeneratorPage />} />
          <Route path="/privacy/" element={<PrivacyPage />} />
          <Route path="/privacy" element={<PrivacyPage />} />
          <Route path="/terms/" element={<TermsPage />} />
          <Route path="/terms" element={<TermsPage />} />
          <Route path="/refund-policy/" element={<RefundPage />} />
          <Route path="/refund-policy" element={<RefundPage />} />
        </Routes>
      </div>
      <Footer />
    </div>
  );
}
