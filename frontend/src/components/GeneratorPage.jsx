import React, { useState } from 'react';
import Navbar from './Navbar';

export default function GeneratorPage() {
  const [docType, setDocType] = useState('both');
  const [numberType, setNumberType] = useState('dot');
  const [inputVal, setInputVal] = useState('2354988');
  const [loading, setLoading] = useState(false);
  const [carrier, setCarrier] = useState(null);
  const [alertVisible, setAlertVisible] = useState(true);

  const handleLoadCarrier = async (e) => {
    e.preventDefault();
    if (!inputVal.trim()) return;

    setLoading(true);
    try {
      const res = await fetch(`/api/carriers/${inputVal.trim()}/`);
      const data = await res.json();
      if (data.success && data.carrier) {
        setCarrier(data.carrier);
      } else {
        alert(data.error || 'Carrier not found in FMCSA database.');
      }
    } catch (err) {
      alert('Failed to connect to FMCSA carrier service.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      {/* Top Dark Blue Container including Navigation and Hero Content */}
      <div className="bg-gradient-to-b from-[#0e2544] via-[#0d223e] to-[#0c1f38] text-white pb-36 pt-4">
        {/* Navigation Bar */}
        <Navbar maxWidth="max-w-7xl" />

        {/* Hero Section */}
        <section className="max-w-5xl mx-auto px-6 lg:px-12 pt-12 pb-6">
          <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight text-white mb-4">
            MC Authority Letter & W-9<br className="hidden sm:inline" /> Generator
          </h1>
          <p className="text-slate-300 text-base sm:text-lg max-w-2xl font-normal leading-relaxed">
            Enter a DOT or MC number to pull the carrier's official record, review every field on screen, then download a flattened, non-editable PDF.
          </p>
        </section>
      </div>

      {/* Generator Card Section */}
      <main className="flex-grow -mt-24 sm:-mt-28 px-4 sm:px-6 lg:px-8 mb-24 relative z-10">
        <div className="max-w-5xl mx-auto">
          {/* Main Paperwork Card */}
          <div className="bg-white rounded-2xl shadow-xl shadow-slate-900/10 border border-slate-200/80 p-6 sm:p-10">
            {/* Badge Header */}
            <div className="flex items-center gap-2 text-amber-600 text-xs font-medium mb-3">
              <svg className="w-4 h-4 text-amber-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2"></path>
              </svg>
              <span className="tracking-wide">MC Authority Letter & W-9 Generator</span>
            </div>

            <h2 className="text-xl sm:text-2xl font-bold text-slate-900 mb-2">
              Generate carrier paperwork from a DOT or MC number
            </h2>
            <p className="text-sm text-slate-500 mb-6 leading-relaxed max-w-4xl">
              MC numbers are resolved to their DOT number before the FMCSA carrier service is called. Documents are generated on the official IRS W-9 and FMCSA certificate layouts.
            </p>

            {/* Warning Alert Callout */}
            {alertVisible && (
              <div id="alert-warning" className="bg-amber-50/70 border border-amber-200/90 rounded-xl p-4 flex items-start justify-between gap-3 mb-8 text-amber-900" role="alert">
                <div className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2"></path>
                  </svg>
                  <p className="text-xs sm:text-sm font-normal text-amber-800 leading-snug">
                    Authority status is <strong className="font-bold text-amber-950">not</strong> checked here. Before relying on any generated document, independently verify that the MC/DOT's operating authority is currently Active.
                  </p>
                </div>
                <button
                  aria-label="Dismiss alert"
                  onClick={() => setAlertVisible(false)}
                  className="text-amber-700/60 hover:text-amber-900 transition-colors p-0.5 cursor-pointer"
                  type="button"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path d="M6 18L18 6M6 6l12 12" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2"></path>
                  </svg>
                </button>
              </div>
            )}

            {/* Form Elements */}
            <form id="doc-generator-form" onSubmit={handleLoadCarrier} className="space-y-6">
              {/* Document Type Dropdown */}
              <div className="max-w-xs">
                <label className="block text-xs font-medium text-slate-700 mb-1.5" htmlFor="document-type">
                  Document type
                </label>
                <div className="relative">
                  <select
                    id="document-type"
                    name="document-type"
                    value={docType}
                    onChange={(e) => setDocType(e.target.value)}
                    className="w-full appearance-none bg-white border border-slate-300 rounded-lg px-3.5 py-2.5 text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-600 focus:border-blue-600 transition shadow-sm cursor-pointer"
                  >
                    <option value="both">Both</option>
                    <option value="mc-authority">MC Authority Letter</option>
                    <option value="w9">IRS W-9 Form</option>
                  </select>
                  <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-3 text-slate-400">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path d="M19 9l-7 7-7-7" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2"></path>
                    </svg>
                  </div>
                </div>
              </div>

              {/* Input Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-12 gap-3 sm:gap-4 items-end">
                <div className="sm:col-span-3">
                  <label className="block text-xs font-medium text-slate-700 mb-1.5" htmlFor="number-type">
                    Number type
                  </label>
                  <div className="relative">
                    <select
                      id="number-type"
                      name="number-type"
                      value={numberType}
                      onChange={(e) => setNumberType(e.target.value)}
                      className="w-full appearance-none bg-white border border-slate-300 rounded-lg px-3.5 py-2.5 text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-600 focus:border-blue-600 transition shadow-sm cursor-pointer"
                    >
                      <option value="dot">DOT number</option>
                      <option value="mc">MC number</option>
                    </select>
                    <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-3 text-slate-400">
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path d="M19 9l-7 7-7-7" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2"></path>
                      </svg>
                    </div>
                  </div>
                </div>

                <div className="sm:col-span-6">
                  <label className="block text-xs font-medium text-slate-700 mb-1.5" htmlFor="dot-number-input">
                    {numberType === 'mc' ? 'MC number' : 'DOT number'}
                  </label>
                  <input
                    id="dot-number-input"
                    name="dot_number"
                    required
                    type="text"
                    value={inputVal}
                    onChange={(e) => setInputVal(e.target.value)}
                    placeholder="e.g. 2354988"
                    className="w-full border border-slate-300 rounded-lg px-3.5 py-2.5 text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-600 focus:border-blue-600 transition shadow-sm"
                  />
                </div>

                <div className="sm:col-span-3">
                  <button
                    type="submit"
                    id="btn-load-carrier"
                    disabled={loading}
                    className="w-full inline-flex items-center justify-center gap-2 bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-600 hover:to-amber-700 text-white font-medium px-5 py-2.5 rounded-lg text-sm transition shadow-sm active:scale-[0.99] cursor-pointer disabled:opacity-50"
                  >
                    <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.2"></path>
                    </svg>
                    <span>{loading ? 'Loading...' : 'Load carrier'}</span>
                  </button>
                </div>
              </div>

              {/* Bottom Warning Reminder */}
              <div className="pt-1 flex items-center gap-2 text-xs text-amber-700">
                <svg className="w-3.5 h-3.5 text-amber-600 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2"></path>
                </svg>
                <span>Reminder: always confirm the MC/DOT's authority status is Active before using these documents.</span>
              </div>
            </form>

            {/* Document Output Preview Box */}
            {carrier && (
              <div id="carrier-doc-preview" className="mt-8 pt-8 border-t border-slate-200 space-y-4">
                <div className="bg-slate-900 text-white rounded-xl p-4 flex justify-between items-center">
                  <span className="font-bold text-sm text-amber-400">Carrier Document Loaded</span>
                  <button
                    type="button"
                    onClick={() => window.print()}
                    className="px-4 py-2 bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold rounded-lg text-xs cursor-pointer"
                  >
                    Print / Save PDF
                  </button>
                </div>
                <div className="bg-slate-50 border border-slate-300 rounded-xl p-6 font-mono text-xs text-slate-800 space-y-2">
                  <p><strong>Legal Name:</strong> <span id="doc-legal-name">{carrier.legal_name || 'N/A'}</span></p>
                  <p><strong>DOT Number:</strong> <span id="doc-dot-num">{carrier.dot_number || 'N/A'}</span></p>
                  <p><strong>MC Number:</strong> <span id="doc-mc-num">{carrier.mc_number || 'N/A'}</span></p>
                  <p><strong>Address:</strong> <span id="doc-address">{`${carrier.phy_street || ''}, ${carrier.phy_city || ''}, ${carrier.phy_state || ''} ${carrier.phy_zipcode || ''}`}</span></p>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </>
  );
}
