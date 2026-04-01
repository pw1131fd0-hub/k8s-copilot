import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { api } from '../utils/api';

export default function ExportModal({ isOpen, onClose }) {
  const { t } = useTranslation();
  const [format, setFormat] = useState('json');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleExport = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      // Build query parameters
      const params = new URLSearchParams();
      params.append('format', format);
      if (startDate) params.append('start_date', startDate);
      if (endDate) params.append('end_date', endDate);

      // Call API
      const response = await fetch(`${api.baseURL}/posts/export?${params}`, {
        method: 'GET',
        headers: {
          'Accept': format === 'json' ? 'application/json' : 'text/plain',
        },
      });

      if (!response.ok) {
        throw new Error(t('export.error'));
      }

      // Get the file content
      const blob = await response.blob();

      // Create download link
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = response.headers
        .get('content-disposition')
        ?.split('filename=')[1]
        ?.replace(/"/g, '') || `clawbook_export.${format === 'markdown' ? 'md' : format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      onClose();
    } catch (err) {
      setError(err.message || t('export.error'));
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-slate-900 rounded-lg shadow-xl p-6 max-w-md w-full mx-4 dark:bg-slate-800">
        <h2 className="text-2xl font-bold mb-4 text-slate-100">{t('export.title')}</h2>

        <form onSubmit={handleExport} className="space-y-4">
          {/* Format Selection */}
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              {t('export.format')}
            </label>
            <select
              value={format}
              onChange={(e) => setFormat(e.target.value)}
              className="w-full px-4 py-2 rounded-lg bg-slate-800 text-slate-100 border border-slate-700 focus:outline-none focus:border-red-500"
            >
              <option value="json">JSON (for data analysis)</option>
              <option value="csv">CSV (for spreadsheets)</option>
              <option value="markdown">Markdown (for reading)</option>
            </select>
          </div>

          {/* Start Date */}
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Start Date (optional)
            </label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="w-full px-4 py-2 rounded-lg bg-slate-800 text-slate-100 border border-slate-700 focus:outline-none focus:border-red-500"
            />
          </div>

          {/* End Date */}
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              End Date (optional)
            </label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="w-full px-4 py-2 rounded-lg bg-slate-800 text-slate-100 border border-slate-700 focus:outline-none focus:border-red-500"
            />
          </div>

          {/* Error Message */}
          {error && (
            <div className="p-3 bg-red-900 text-red-100 rounded-lg text-sm">
              {error}
            </div>
          )}

          {/* Buttons */}
          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 rounded-lg bg-slate-700 text-slate-100 font-medium hover:bg-slate-600 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="flex-1 px-4 py-2 rounded-lg bg-red-600 text-white font-medium hover:bg-red-700 disabled:bg-red-400 transition-colors"
            >
              {isLoading ? 'Exporting...' : 'Export'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
