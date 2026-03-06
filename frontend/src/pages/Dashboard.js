import React, { useState } from 'react';
import PodList from '../components/PodList';
import DiagnosePanel from '../components/DiagnosePanel';
import YAMLCodeEditor from '../components/YAMLCodeEditor';
import { useK8sData } from '../hooks/useK8sData';

const TABS = ['Cluster Overview', 'YAML Editor'];

export default function Dashboard() {
  const { pods, clusterStatus, loading, error, refresh } = useK8sData();
  const [activeTab, setActiveTab] = useState(0);
  const [diagnoseResult, setDiagnoseResult] = useState(null);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Top nav */}
      <header className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-2xl">🦞</span>
          <span className="font-semibold text-gray-800 text-lg">Lobster K8s Copilot</span>
        </div>
        <div className="flex items-center gap-3">
          {clusterStatus && (
            <span className={`flex items-center gap-1.5 text-xs font-medium ${clusterStatus.status === 'connected' ? 'text-green-600' : 'text-red-500'}`}>
              <span className={`w-2 h-2 rounded-full ${clusterStatus.status === 'connected' ? 'bg-green-500' : 'bg-red-500'}`} />
              {clusterStatus.status === 'connected' ? 'Cluster Connected' : 'Cluster Disconnected'}
            </span>
          )}
          <button
            onClick={refresh}
            className="text-xs text-gray-500 hover:text-gray-700 px-2 py-1 rounded border border-gray-200 hover:border-gray-300 transition-colors"
          >
            ↻ Refresh
          </button>
        </div>
      </header>

      {/* Tabs */}
      <div className="border-b border-gray-200 bg-white px-6">
        <nav className="flex gap-4">
          {TABS.map((tab, i) => (
            <button
              key={tab}
              onClick={() => setActiveTab(i)}
              className={`py-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === i
                  ? 'border-indigo-600 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              {tab}
            </button>
          ))}
        </nav>
      </div>

      {/* Main content */}
      <main className="p-6">
        {activeTab === 0 && (
          <PodList
            pods={pods}
            loading={loading}
            error={error}
            onDiagnoseResult={setDiagnoseResult}
          />
        )}
        {activeTab === 1 && <YAMLCodeEditor />}
      </main>

      {/* Diagnose slide-in panel */}
      {diagnoseResult && (
        <DiagnosePanel
          result={diagnoseResult}
          onClose={() => setDiagnoseResult(null)}
        />
      )}
    </div>
  );
}
