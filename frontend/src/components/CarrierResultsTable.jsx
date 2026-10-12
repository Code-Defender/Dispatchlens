import React from 'react';
import { formatMcNumber, formatPhoneNumber, formatLocation, escapeHtml } from '../utils/formatters';

export default function CarrierResultsTable({ results, startMc, endMc }) {
  if (!results || results.length === 0) {
    return (
      <div className="bg-white rounded-2xl shadow-xl border border-slate-100 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-100 border-b border-slate-200 text-slate-700 uppercase font-semibold">
              <tr>
                <th className="py-3.5 px-4">MC / DOT</th>
                <th className="py-3.5 px-4">Legal Business Name</th>
                <th className="py-3.5 px-4">Equipment & Fleet</th>
                <th className="py-3.5 px-4">Location</th>
                <th className="py-3.5 px-4">Phone / Contact</th>
                <th className="py-3.5 px-4">Authority Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 text-slate-800">
              <tr>
                <td colSpan="6" className="py-8 text-center text-slate-500">
                  No active MC authorized carriers found matching criteria in range {startMc} – {endMc}.
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-2xl shadow-xl border border-slate-100 overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead className="bg-slate-100 border-b border-slate-200 text-slate-700 uppercase font-semibold">
            <tr>
              <th className="py-3.5 px-4">MC / DOT</th>
              <th className="py-3.5 px-4">Legal Business Name</th>
              <th className="py-3.5 px-4">Equipment & Fleet</th>
              <th className="py-3.5 px-4">Location</th>
              <th className="py-3.5 px-4">Phone / Contact</th>
              <th className="py-3.5 px-4">Authority Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200 text-slate-800">
            {results.map((c, idx) => {
              const mcFormatted = formatMcNumber(c.mc_number || c.mc_numeric);
              const dotFormatted = c.dot_number ? `DOT ${c.dot_number}` : 'DOT N/A';
              const compName = c.company_name || 'N/A';
              const officerName = c.officer_name || 'N/A';
              const phoneFormatted = c.phone ? formatPhoneNumber(c.phone) : 'N/A';
              const locationFormatted = formatLocation(c.address);
              const equipType = c.equipment_type || 'General';
              const powerUnits = c.power_units ?? 0;
              const drivers = c.drivers ?? 0;

              return (
                <tr key={c.mc_numeric || c.mc_number || idx} className="hover:bg-slate-50 transition">
                  <td className="py-3.5 px-4 font-mono font-bold text-slate-900">
                    <div className="text-slate-900">{mcFormatted}</div>
                    <div className="text-[10px] text-slate-500 font-normal">{dotFormatted}</div>
                  </td>
                  <td className="py-3.5 px-4 font-semibold text-slate-900">
                    <div>{compName}</div>
                    <div className="text-[11px] text-slate-500 font-normal mt-0.5">
                      <i className="fa-solid fa-user-tie text-slate-400 mr-1"></i>
                      {officerName}
                    </div>
                  </td>
                  <td className="py-3.5 px-4">
                    <span className={`inline-block px-2 py-0.5 rounded font-semibold text-[11px] border ${
                      c.is_broker
                        ? 'bg-purple-50 text-purple-700 border-purple-200'
                        : 'bg-blue-50 text-blue-700 border-blue-200'
                    }`}>
                      {equipType}
                    </span>
                    <div className="text-[11px] text-slate-500 mt-1">
                      {powerUnits} Power Units / {drivers} Drivers
                    </div>
                  </td>
                  <td className="py-3.5 px-4 text-slate-600 font-medium">
                    <i className="fa-solid fa-location-dot text-slate-400 mr-1"></i>
                    {locationFormatted}
                  </td>
                  <td className="py-3.5 px-4 text-slate-600 font-mono text-[11px] space-y-1">
                    <div>
                      {c.phone ? (
                        <a href={`tel:${c.phone}`} className="text-slate-800 hover:text-orange-600 transition">
                          <i className="fa-solid fa-phone text-slate-400 mr-1.5"></i>
                          {phoneFormatted}
                        </a>
                      ) : (
                        <span className="text-slate-400">
                          <i className="fa-solid fa-phone mr-1.5"></i>No Phone
                        </span>
                      )}
                    </div>
                    <div>
                      {c.email ? (
                        <a href={`mailto:${c.email}`} className="text-orange-600 hover:underline block truncate max-w-[180px]" title={c.email}>
                          <i className="fa-solid fa-envelope text-slate-400 mr-1.5"></i>
                          {c.email}
                        </a>
                      ) : (
                        <span className="text-slate-400 block">
                          <i className="fa-solid fa-envelope mr-1.5"></i>No Email
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="py-3.5 px-4">
                    {c.is_active_authority ? (
                      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-bold bg-emerald-100 text-emerald-800">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 mr-1.5"></span> ACTIVE MC
                      </span>
                    ) : (c.docket_status === 'I' || c.authority_status === 'REVOKED') ? (
                      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-bold bg-rose-100 text-rose-800">
                        <span className="w-1.5 h-1.5 rounded-full bg-rose-500 mr-1.5"></span> REVOKED
                      </span>
                    ) : (
                      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-bold bg-amber-100 text-amber-800" title="Active USDOT; MC authority unconfirmed in census">
                        <span className="w-1.5 h-1.5 rounded-full bg-amber-500 mr-1.5"></span> UNVERIFIED
                      </span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
