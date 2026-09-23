import React, { useState } from 'react';
import { downloadReportPdf, downloadReportCsv } from '../api/client';
import { FileText, Download, FileSpreadsheet, CheckCircle2, Shield, Filter } from 'lucide-react';

export default function ReportExport({ pathsData = [], onToast }) {
  const [target, setTarget] = useState('all');
  const [loadingPdf, setLoadingPdf] = useState(false);
  const [loadingCsv, setLoadingCsv] = useState(false);

  /** Download a Blob through a temporary object URL and release that URL afterward. */
  const triggerBlobDownload = (blob, filename) => {
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    link.parentNode.removeChild(link);
    window.URL.revokeObjectURL(url);
  };

  const handleDownloadPdf = async () => {
    setLoadingPdf(true);
    try {
      const blob = await downloadReportPdf(target);
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      const filename = `attackgraphx-report-${target}-${timestamp}.pdf`;
      triggerBlobDownload(blob, filename);
      if (onToast) onToast(`PDF Report downloaded: ${filename}`, 'success');
    } catch (err) {
      if (onToast) onToast('Failed to generate PDF report', 'error');
    } finally {
      setLoadingPdf(false);
    }
  };

  const handleDownloadCsv = async () => {
    setLoadingCsv(true);
    try {
      const blob = await downloadReportCsv();
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      const filename = `attackgraphx-telemetry-${timestamp}.csv`;
      triggerBlobDownload(blob, filename);
      if (onToast) onToast(`CSV Data downloaded: ${filename}`, 'success');
    } catch (err) {
      if (onToast) onToast('Failed to export CSV telemetry', 'error');
    } finally {
      setLoadingCsv(false);
    }
  };

  const targets = Array.from(new Set((pathsData || []).map((p) => p.target))).sort();

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Executive Report Card */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">
        <div className="flex items-center justify-between pb-4 border-b border-slate-200">
          <div>
            <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <FileText className="w-5 h-5 text-blue-600" />
              <span>Compliance & Executive Report Export</span>
            </h3>
            <p className="text-xs text-slate-500 mt-0.5 font-sans">
              Generate audit-ready security topology reports and raw telemetry for SOC compliance and executive debriefs.
            </p>
          </div>
          <span className="text-xs font-mono px-3 py-1 rounded bg-slate-100 text-slate-700 border border-slate-200 font-medium">
            Format: PDF & CSV
          </span>
        </div>

        {/* Target Selector */}
        <div className="mt-6">
          <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2 font-mono flex items-center gap-1.5">
            <Filter className="w-3.5 h-3.5 text-blue-600" />
            Select Asset Target Scope
          </label>
          <select
            value={target}
            onChange={(e) => setTarget(e.target.value)}
            className="w-full max-w-md bg-slate-50 border border-slate-300 rounded-xl px-4 py-3 text-xs text-slate-900 font-mono focus:outline-none focus:border-blue-600 focus:bg-white transition-colors"
          >
            <option value="all">Entire Infrastructure (All Targets)</option>
            {targets.map((t) => (
              <option key={t} value={t} className="bg-white text-slate-800">
                Target Host: {t}
              </option>
            ))}
          </select>
        </div>

        {/* Download Action Cards */}
        <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* PDF Card */}
          <div className="bg-slate-50/80 border border-slate-200 rounded-xl p-5 hover:border-slate-300 transition-colors flex flex-col justify-between">
            <div>
              <div className="flex items-center gap-3">
                <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-600">
                  <FileText className="w-6 h-6" />
                </div>
                <div>
                  <h4 className="text-sm font-bold text-slate-900">Executive PDF Report</h4>
                  <p className="text-xs text-slate-500 mt-0.5 font-mono">Formatted PDF Document</p>
                </div>
              </div>
              <p className="text-xs text-slate-600 mt-4 leading-relaxed font-sans">
                Includes full path topology diagrams, vulnerability summaries, risk distribution metrics, and prioritized patch recommendations.
              </p>
            </div>

            <button
              onClick={handleDownloadPdf}
              disabled={loadingPdf}
              className="mt-6 w-full py-2.5 px-4 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs shadow-sm flex items-center justify-center gap-2 transition-all disabled:opacity-50 active:scale-95"
            >
              {loadingPdf ? (
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <>
                  <Download className="w-4 h-4" />
                  <span>Download PDF Report</span>
                </>
              )}
            </button>
          </div>

          {/* CSV Card */}
          <div className="bg-slate-50/80 border border-slate-200 rounded-xl p-5 hover:border-slate-300 transition-colors flex flex-col justify-between">
            <div>
              <div className="flex items-center gap-3">
                <div className="p-3 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-600">
                  <FileSpreadsheet className="w-6 h-6" />
                </div>
                <div>
                  <h4 className="text-sm font-bold text-slate-900">Raw Telemetry CSV Export</h4>
                  <p className="text-xs text-slate-500 mt-0.5 font-mono">Structured CSV Dataset</p>
                </div>
              </div>
              <p className="text-xs text-slate-600 mt-4 leading-relaxed font-sans">
                Contains complete tabular attack path datasets, host IPs, CVE IDs, MITRE ATT&CK techniques, and severity scores for SIEM import.
              </p>
            </div>

            <button
              onClick={handleDownloadCsv}
              disabled={loadingCsv}
              className="mt-6 w-full py-2.5 px-4 rounded-xl bg-white hover:bg-slate-50 text-slate-800 font-semibold text-xs border border-slate-300 shadow-sm flex items-center justify-center gap-2 transition-all disabled:opacity-50 active:scale-95"
            >
              {loadingCsv ? (
                <div className="w-4 h-4 border-2 border-slate-400 border-t-slate-800 rounded-full animate-spin" />
              ) : (
                <>
                  <Download className="w-4 h-4 text-emerald-600" />
                  <span>Export CSV Dataset</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
