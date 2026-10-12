import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import Navbar from './Navbar';
import CarrierResultsTable from './CarrierResultsTable';
import { formatMcNumber, formatPhoneNumber, formatLocation } from '../utils/formatters';

export default function SearchPage() {
  // Form State
  const [startMc, setStartMc] = useState('');
  const [endMc, setEndMc] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [searchMode, setSearchMode] = useState('mc-range');
  const [authorityFilter, setAuthorityFilter] = useState('all');
  const [equipFilter, setEquipFilter] = useState('');
  const [cargoFilter, setCargoFilter] = useState('');
  const [minTrucks, setMinTrucks] = useState('');
  const [maxTrucks, setMaxTrucks] = useState('');

  // UI State
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [rawResults, setRawResults] = useState([]);
  const [displaySearchMode, setDisplaySearchMode] = useState('mc-range');
  const [displayStartMc, setDisplayStartMc] = useState('');
  const [displayEndMc, setDisplayEndMc] = useState('');
  const [displayStartDate, setDisplayStartDate] = useState('');
  const [displayEndDate, setDisplayEndDate] = useState('');

  // FAQ State
  const [openFaq, setOpenFaq] = useState(null);

  const toggleFaq = (index) => {
    setOpenFaq(openFaq === index ? null : index);
  };

  const handleSearch = async (e) => {
    e.preventDefault();

    if (searchMode === 'search-by-date') {
      if (!startDate || !endDate) {
        alert('Please enter both Starting Date and Ending Date.');
        return;
      }
      if (endDate < startDate) {
        alert('Ending Date cannot be earlier than Starting Date.');
        return;
      }

      setLoading(true);
      try {
        const res = await fetch(`/api/carriers/search-by-date/?start_date=${startDate}&end_date=${endDate}`);
        const data = await res.json();
        if (res.ok && data.results) {
          setRawResults(data.results);
          setDisplayStartDate(startDate);
          setDisplayEndDate(endDate);
          setDisplaySearchMode('search-by-date');
          const hasConfirmed = data.results.some((c) => c.is_active_authority);
          setAuthorityFilter(hasConfirmed ? 'active-mc' : 'all');
          setSearched(true);
        } else {
          alert(data.error || 'Failed to fetch carrier data by date.');
        }
      } catch (err) {
        alert('Error connecting to FMCSA Census service.');
      } finally {
        setLoading(false);
      }
    } else {
      if (!startMc || !endMc) {
        alert('Please enter both Start MC and End MC.');
        return;
      }

      setLoading(true);
      try {
        const res = await fetch(`/api/carriers/search/?start_mc=${startMc}&end_mc=${endMc}`);
        const data = await res.json();
        if (res.ok && data.results) {
          setRawResults(data.results);
          setDisplayStartMc(startMc);
          setDisplayEndMc(endMc);
          setDisplaySearchMode('mc-range');
          setAuthorityFilter('all');
          setSearched(true);
        } else {
          alert(data.error || 'Failed to fetch carrier data.');
        }
      } catch (err) {
        alert('Error connecting to FMCSA Census service.');
      } finally {
        setLoading(false);
      }
    }
  };

  // Client-side filtering logic
  const filteredResults = rawResults.filter((c) => {
    if (authorityFilter === 'active-mc' && !c.is_active_authority) return false;
    if (authorityFilter === 'usdot-only' && c.is_active_authority) return false;
    if (equipFilter && c.equipment_type !== equipFilter) return false;
    const powerUnits = c.power_units || 0;
    const min = parseInt(minTrucks) || 0;
    const max = maxTrucks !== '' ? parseInt(maxTrucks) || Infinity : Infinity;
    if (powerUnits < min) return false;
    if (powerUnits > max) return false;
    return true;
  });

  const activeMcCount = rawResults.filter((c) => c.is_active_authority).length;
  const usdotOnlyCount = rawResults.filter((c) => !c.is_active_authority).length;

  // CSV Export Handler
  const handleExportCsv = () => {
    if (!filteredResults || filteredResults.length === 0) return;
    const headers = ['MC Number', 'DOT Number', 'Company Name', 'Officer Name', 'Phone', 'Email', 'Location', 'Equipment Type', 'Power Units', 'Drivers', 'Authority Status'];
    const rows = filteredResults.map((c) => [
      formatMcNumber(c.mc_number || c.mc_numeric),
      c.dot_number || 'N/A',
      `"${(c.company_name || 'N/A').replace(/"/g, '""')}"`,
      `"${(c.officer_name || 'N/A').replace(/"/g, '""')}"`,
      c.phone ? formatPhoneNumber(c.phone) : 'N/A',
      c.email || 'N/A',
      `"${formatLocation(c.address).replace(/"/g, '""')}"`,
      `"${(c.equipment_type || 'N/A').replace(/"/g, '""')}"`,
      c.power_units ?? 0,
      c.drivers ?? 0,
      c.is_active_authority ? 'ACTIVE MC' : (c.docket_status === 'I' ? 'REVOKED' : (c.is_active_carrier ? 'USDOT ONLY' : 'INACTIVE'))
    ]);
    const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map((r) => r.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    const fileName = displaySearchMode === 'search-by-date'
      ? `carriers_date_${displayStartDate}_to_${displayEndDate}.csv`
      : `carriers_${displayStartMc}_${displayEndMc}.csv`;
    link.setAttribute('download', fileName);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <>
      {/* Top Dark Container Header with Hero Content */}
      <div className="bg-gradient-to-b from-[#0e2544] via-[#0d223e] to-[#0c1f38] text-white pb-36 pt-4">
        {/* Navigation Bar */}
        <Navbar maxWidth="max-w-6xl" />

        {/* Hero Content */}
        <section className="max-w-6xl mx-auto px-6 pt-12 pb-6">
          <div className="max-w-3xl">
            <h1 className="text-3xl sm:text-4xl lg:text-[42px] font-extrabold text-white tracking-tight leading-[1.18]">
              FMCSA & MC scraper — find verified new MC carriers instantly.
            </h1>
            <p className="mt-4 text-[14px] leading-relaxed text-slate-300 max-w-2xl font-normal">
              Search and verify USA carrier authority, safety data, insurance eligibility and equipment type directly from the official FMCSA census — only carriers with confirmed active MC authority are returned.
            </p>
            {/* Feature Pill Badges */}
            <div className="mt-6 flex flex-wrap items-center gap-2.5 text-xs text-slate-200">
              <div className="inline-flex items-center px-3 py-1.5 rounded-full bg-[#1b3b64] border border-[#2b4c77]">
                <svg className="w-3.5 h-3.5 mr-1.5 text-slate-300" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                  <path d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" strokeLinecap="round" strokeLinejoin="round"></path>
                </svg>
                FMCSA verified only
              </div>
              <div className="inline-flex items-center px-3 py-1.5 rounded-full bg-[#1b3b64] border border-[#2b4c77]">
                <span className="mr-1.5 text-slate-300 font-bold">#</span>
                Active MC authority
              </div>
              <div className="inline-flex items-center px-3 py-1.5 rounded-full bg-[#1b3b64] border border-[#2b4c77]">
                <svg className="w-3.5 h-3.5 mr-1.5 text-slate-300" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                  <path d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" strokeLinecap="round" strokeLinejoin="round"></path>
                  <path d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" strokeLinecap="round" strokeLinejoin="round"></path>
                </svg>
                Equipment & fleet data
              </div>
            </div>
          </div>
        </section>
      </div>

      {/* Main Content */}
      <main className="max-w-6xl mx-auto px-6 -mt-24 w-full flex-grow pb-20 space-y-7">
        {/* Verification Filter Card */}
        <div className="bg-white rounded-2xl shadow-xl border border-slate-100 p-7">
          <div className="flex items-center space-x-2 text-slate-700 font-semibold text-xs tracking-wide uppercase mb-4">
            <svg className="w-4 h-4 text-orange-500" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" strokeLinecap="round" strokeLinejoin="round"></path>
            </svg>
            <span>Verification filters</span>
          </div>

          <form id="carrier-search-form" onSubmit={handleSearch}>
            {/* Search Mode Selector */}
            <div className="mb-5">
              <label className="block text-xs font-medium text-slate-600 mb-1.5 flex items-center">
                <svg className="w-3.5 h-3.5 mr-1 text-slate-400" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                  <path d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" strokeLinecap="round" strokeLinejoin="round"></path>
                </svg>
                Search mode
              </label>
              <div className="relative">
                <select
                  value={searchMode}
                  onChange={(e) => setSearchMode(e.target.value)}
                  className="w-full text-xs font-medium text-slate-800 bg-white border border-slate-200 rounded-lg py-2.5 px-3.5 appearance-none focus:outline-none focus:ring-1 focus:ring-orange-500 focus:border-orange-500 cursor-pointer"
                >
                  <option value="mc-range">MC Range Search</option>
                  <option value="search-by-date">Search by Date</option>
                </select>
                <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-3 text-slate-400">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                    <path d="M19 9l-7 7-7-7" strokeLinecap="round" strokeLinejoin="round"></path>
                  </svg>
                </div>
              </div>
            </div>

            {/* Inputs Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-5 mb-6">
              {searchMode === 'search-by-date' ? (
                <>
                  {/* Starting Date */}
                  <div>
                    <label htmlFor="start_date" className="block text-xs font-medium text-slate-700 mb-1.5 flex items-center">
                      <svg className="w-3.5 h-3.5 mr-1 text-slate-400" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                        <path d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" strokeLinecap="round" strokeLinejoin="round"></path>
                      </svg>
                      Starting Date
                    </label>
                    <input
                      id="start_date"
                      name="start_date"
                      required
                      value={startDate}
                      onChange={(e) => setStartDate(e.target.value)}
                      className="w-full text-xs text-slate-800 placeholder-slate-400 border border-slate-200 rounded-lg py-2.5 px-3.5 focus:outline-none focus:ring-1 focus:ring-orange-500 focus:border-orange-500"
                      type="date"
                    />
                  </div>

                  {/* Ending Date */}
                  <div>
                    <label htmlFor="end_date" className="block text-xs font-medium text-slate-700 mb-1.5 flex items-center">
                      <svg className="w-3.5 h-3.5 mr-1 text-slate-400" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                        <path d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" strokeLinecap="round" strokeLinejoin="round"></path>
                      </svg>
                      Ending Date
                    </label>
                    <input
                      id="end_date"
                      name="end_date"
                      required
                      value={endDate}
                      onChange={(e) => setEndDate(e.target.value)}
                      className="w-full text-xs text-slate-800 placeholder-slate-400 border border-slate-200 rounded-lg py-2.5 px-3.5 focus:outline-none focus:ring-1 focus:ring-orange-500 focus:border-orange-500"
                      type="date"
                    />
                  </div>
                </>
              ) : (
                <>
                  {/* Start MC */}
                  <div>
                    <label htmlFor="start_mc" className="block text-xs font-medium text-slate-700 mb-1.5 flex items-center">
                      <span className="mr-1 text-slate-400">#</span> Start MC
                    </label>
                    <input
                      id="start_mc"
                      name="start_mc"
                      required
                      min="1"
                      step="1"
                      value={startMc}
                      onChange={(e) => setStartMc(e.target.value)}
                      className="w-full text-xs text-slate-800 placeholder-slate-400 border border-slate-200 rounded-lg py-2.5 px-3.5 focus:outline-none focus:ring-1 focus:ring-orange-500 focus:border-orange-500"
                      placeholder="e.g. 100000"
                      type="number"
                    />
                  </div>

                  {/* End MC */}
                  <div>
                    <label htmlFor="end_mc" className="block text-xs font-medium text-slate-700 mb-1.5 flex items-center">
                      <span className="mr-1 text-slate-400">#</span> End MC
                    </label>
                    <input
                      id="end_mc"
                      name="end_mc"
                      required
                      min="1"
                      step="1"
                      value={endMc}
                      onChange={(e) => setEndMc(e.target.value)}
                      className="w-full text-xs text-slate-800 placeholder-slate-400 border border-slate-200 rounded-lg py-2.5 px-3.5 focus:outline-none focus:ring-1 focus:ring-orange-500 focus:border-orange-500"
                      placeholder="e.g. 100500"
                      type="number"
                    />
                  </div>
                </>
              )}

              {/* Equipment Type */}
              <div>
                <label htmlFor="filter_equipment" className="block text-xs font-medium text-slate-700 mb-1.5 flex items-center">
                  <svg className="w-3.5 h-3.5 mr-1 text-slate-400" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                    <path d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" strokeLinecap="round" strokeLinejoin="round"></path>
                  </svg>
                  Equipment type <span className="text-slate-400 text-[11px] ml-1">(select any number)</span>
                </label>
                <div className="relative">
                  <select
                    id="filter_equipment"
                    value={equipFilter}
                    onChange={(e) => setEquipFilter(e.target.value)}
                    className="w-full text-xs font-medium text-slate-700 bg-white border border-slate-200 rounded-lg py-2.5 px-3.5 appearance-none focus:outline-none focus:ring-1 focus:ring-orange-500 focus:border-orange-500 cursor-pointer"
                  >
                    <option value="">All equipment types</option>
                    <option value="Tractor-Trailer">Dry Van</option>
                    <option value="Reefer">Reefer</option>
                    <option value="Flatbed">Flatbed</option>
                    <option value="Power Only">Power Only</option>
                    <option value="Box Truck">Box Truck</option>
                  </select>
                  <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-3 text-slate-400">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                      <path d="M19 9l-7 7-7-7" strokeLinecap="round" strokeLinejoin="round"></path>
                    </svg>
                  </div>
                </div>
              </div>

              {/* Cargo Classification */}
              <div>
                <label htmlFor="filter_cargo" className="block text-xs font-medium text-slate-700 mb-1.5 flex items-center">
                  <svg className="w-3.5 h-3.5 mr-1 text-slate-400" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                    <path d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" strokeLinecap="round" strokeLinejoin="round"></path>
                  </svg>
                  Cargo classification <span className="text-slate-400 text-[11px] ml-1">(select any number)</span>
                </label>
                <div className="relative">
                  <select
                    id="filter_cargo"
                    value={cargoFilter}
                    onChange={(e) => setCargoFilter(e.target.value)}
                    className="w-full text-xs font-medium text-slate-700 bg-white border border-slate-200 rounded-lg py-2.5 px-3.5 appearance-none focus:outline-none focus:ring-1 focus:ring-orange-500 focus:border-orange-500 cursor-pointer"
                  >
                    <option value="">All cargo classifications</option>
                    <option value="General Freight">General Freight</option>
                    <option value="Household Goods">Household Goods</option>
                    <option value="Metal">Metal: sheets, coils, rolls</option>
                  </select>
                  <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-3 text-slate-400">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                      <path d="M19 9l-7 7-7-7" strokeLinecap="round" strokeLinejoin="round"></path>
                    </svg>
                  </div>
                </div>
              </div>

              {/* Minimum Trucks */}
              <div>
                <label htmlFor="filter_min_trucks" className="block text-xs font-medium text-slate-700 mb-1.5 flex items-center">
                  <svg className="w-3.5 h-3.5 mr-1 text-slate-400" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                    <path d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" strokeLinecap="round" strokeLinejoin="round"></path>
                  </svg>
                  Minimum trucks
                </label>
                <input
                  id="filter_min_trucks"
                  value={minTrucks}
                  onChange={(e) => setMinTrucks(e.target.value)}
                  className="w-full text-xs text-slate-800 placeholder-slate-400 border border-slate-200 rounded-lg py-2.5 px-3.5 focus:outline-none focus:ring-1 focus:ring-orange-500 focus:border-orange-500"
                  placeholder="e.g. 1"
                  type="number"
                  min="0"
                />
              </div>

              {/* Maximum Trucks */}
              <div>
                <label htmlFor="filter_max_trucks" className="block text-xs font-medium text-slate-700 mb-1.5 flex items-center">
                  <svg className="w-3.5 h-3.5 mr-1 text-slate-400" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                    <path d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" strokeLinecap="round" strokeLinejoin="round"></path>
                  </svg>
                  Maximum trucks
                </label>
                <input
                  id="filter_max_trucks"
                  value={maxTrucks}
                  onChange={(e) => setMaxTrucks(e.target.value)}
                  className="w-full text-xs text-slate-800 placeholder-slate-400 border border-slate-200 rounded-lg py-2.5 px-3.5 focus:outline-none focus:ring-1 focus:ring-orange-500 focus:border-orange-500"
                  placeholder="e.g. 10"
                  type="number"
                  min="0"
                />
              </div>
            </div>

            {/* Action Footer with Notice & Submit Button */}
            <div className="pt-2 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
              <p className="text-[11px] leading-relaxed text-slate-500 max-w-xl">
                Only FMCSA-verified, active MC-authorized USA carriers are returned. Carriers with pending authority, out-of-service, or revocation-pending status are excluded.
              </p>
              <button
                id="btn-search"
                disabled={loading}
                className="inline-flex items-center px-5 py-2.5 rounded-lg bg-orange-500 hover:bg-orange-600 text-white text-xs font-medium shadow-sm transition-colors whitespace-nowrap cursor-pointer disabled:opacity-50"
                type="submit"
              >
                <svg className="w-3.5 h-3.5 mr-1.5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                  <path d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" strokeLinecap="round" strokeLinejoin="round"></path>
                </svg>
                <span className="btn-text">{loading ? 'Querying FMCSA...' : 'Verify carriers'}</span>
              </button>
            </div>
          </form>
        </div>

        {/* Results Table Container */}
        {searched && (
          <div id="results-wrapper" className="space-y-4">
            <div className="bg-slate-900 text-white rounded-xl p-5 flex flex-wrap items-center justify-between gap-4 shadow-lg">
              <div>
                <div className="flex items-baseline gap-2">
                  <span id="results-count" className="text-2xl font-bold text-amber-400">
                    {filteredResults.length}
                  </span>
                  <span className="text-sm text-slate-300 font-medium">
                    {authorityFilter === 'active-mc'
                      ? 'Confirmed Active MC Carriers Found'
                      : (displaySearchMode === 'search-by-date' ? 'FMCSA Carriers Found' : 'Active FMCSA Carriers Found')}
                  </span>
                </div>
                {displaySearchMode === 'search-by-date' && (
                  <p className="text-xs text-slate-400 mt-1">
                    <span className="text-emerald-400 font-semibold">{activeMcCount} Confirmed Active MC</span>
                    <span className="mx-1.5">•</span>
                    <span className="text-slate-300">{usdotOnlyCount} USDOT-Only / Unverified</span>
                  </p>
                )}
                <p className="text-xs text-slate-400 mt-1">
                  {displaySearchMode === 'search-by-date' ? (
                    <>
                      Date Range: <span id="display-date-range" className="font-mono text-slate-200">{displayStartDate} – {displayEndDate}</span>
                    </>
                  ) : (
                    <>
                      Range: <span id="display-mc-range" className="font-mono text-slate-200">MC {displayStartMc} – MC {displayEndMc}</span>
                    </>
                  )}
                </p>
              </div>
              <div className="flex items-center gap-3">
                {displaySearchMode === 'search-by-date' && usdotOnlyCount > 0 && (
                  <div className="flex items-center rounded-lg bg-slate-800 p-1 border border-slate-700 text-xs">
                    <button
                      type="button"
                      onClick={() => setAuthorityFilter('active-mc')}
                      className={`px-3 py-1.5 rounded-md font-medium transition cursor-pointer ${
                        authorityFilter === 'active-mc' ? 'bg-orange-500 text-white shadow-xs' : 'text-slate-300 hover:text-white'
                      }`}
                    >
                      Active MC ({activeMcCount})
                    </button>
                    <button
                      type="button"
                      onClick={() => setAuthorityFilter('all')}
                      className={`px-3 py-1.5 rounded-md font-medium transition cursor-pointer ${
                        authorityFilter === 'all' ? 'bg-orange-500 text-white shadow-xs' : 'text-slate-300 hover:text-white'
                      }`}
                    >
                      All Records ({rawResults.length})
                    </button>
                  </div>
                )}
                <button
                  id="btn-export-csv"
                  type="button"
                  onClick={handleExportCsv}
                  className="inline-flex items-center px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold shadow-sm transition cursor-pointer"
                >
                  <i className="fa-solid fa-file-csv mr-2"></i> Export CSV
                </button>
              </div>
            </div>

            <CarrierResultsTable
              results={filteredResults}
              startMc={displaySearchMode === 'search-by-date' ? displayStartDate : displayStartMc}
              endMc={displaySearchMode === 'search-by-date' ? displayEndDate : displayEndMc}
            />
          </div>
        )}

        {/* Empty State Lookup Card */}
        {!searched && (
          <div id="empty-state-card" className="bg-white rounded-2xl border border-slate-200/90 py-16 px-6 text-center shadow-xs">
            <div className="mx-auto w-10 h-10 rounded-full bg-amber-50 border border-amber-200 flex items-center justify-center text-amber-500 mb-4">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="1.75" viewBox="0 0 24 24">
                <path d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" strokeLinecap="round" strokeLinejoin="round"></path>
              </svg>
            </div>
            <h3 className="text-sm font-semibold text-slate-800">Start a carrier safety lookup</h3>
            <p className="mt-1.5 text-xs text-slate-500 max-w-md mx-auto leading-normal">
              Search by MC range, city or location, or by the date MC authority was newly issued or reinstated — straight from the FMCSA census.
            </p>
          </div>
        )}

        {/* Secondary Generator Callout Card */}
        <div className="bg-white rounded-2xl border border-slate-200/90 py-10 px-6 text-center shadow-xs">
          <h3 className="text-sm font-semibold text-slate-800">Need an MC Authority Letter or W-9?</h3>
          <p className="mt-1 text-xs text-slate-500">The document generator now lives on its own page.</p>
          <div className="mt-4">
            <Link to="/generator/" className="inline-flex items-center px-4 py-2 rounded-lg bg-orange-500 hover:bg-orange-600 text-white text-xs font-medium shadow-sm transition-colors">
              Open the generator
            </Link>
          </div>
        </div>

        {/* Frequently Asked Questions Section */}
        <div className="pt-8 pb-4">
          <h2 className="text-2xl font-bold text-slate-900 text-center mb-8">Frequently asked questions</h2>
          <div className="max-w-3xl mx-auto space-y-3">
            {[
              {
                q: 'What is an MC scraper?',
                a: 'An MC scraper queries official FMCSA census database records for newly issued, active motor carrier records based on MC or DOT numbers, extracting essential contact, safety, and equipment details.'
              },
              {
                q: 'Is DispatchLens a Motus scraper?',
                a: 'DispatchLens queries official FMCSA Census records directly in real time, providing accurate authority, safety fitness, and equipment information.'
              },
              {
                q: 'Can I scrape new MC and 8 digit MC numbers?',
                a: 'Yes! DispatchLens supports searching any valid 6-digit, 7-digit, or 8-digit MC number range directly from official census data.'
              },
              {
                q: 'Which MC scraper filters are available?',
                a: 'You can filter results by equipment type (Tractor-Trailer, Power Only, Box Truck, Hotshot), power unit fleet size (minimum/maximum trucks), cargo classification, and company contact details.'
              }
            ].map((faq, index) => {
              const isOpen = openFaq === index;
              return (
                <div key={index} className="faq-item border border-slate-200/80 rounded-xl bg-white overflow-hidden shadow-xs">
                  <button
                    type="button"
                    onClick={() => toggleFaq(index)}
                    className="faq-toggle w-full text-left p-4 sm:px-6 flex justify-between items-center text-sm font-semibold text-slate-800 hover:bg-slate-50 transition cursor-pointer"
                  >
                    <span>{faq.q}</span>
                    <svg className={`w-4 h-4 text-slate-400 transition-transform duration-200 transform ${isOpen ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path d="M19 9l-7 7-7-7" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2"></path>
                    </svg>
                  </button>
                  {isOpen && (
                    <div className="faq-content px-4 sm:px-6 pb-4 text-xs text-slate-600 leading-relaxed border-t border-slate-100 pt-3">
                      {faq.a}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </main>
    </>
  );
}
