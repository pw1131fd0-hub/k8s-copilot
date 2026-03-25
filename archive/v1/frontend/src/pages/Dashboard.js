import React, { useState } from 'react';
import PodList from '../components/PodList';
import DiagnosePanel from '../components/DiagnosePanel';
import YAMLCodeEditor from '../components/YAMLCodeEditor';
import { useK8sData } from '../hooks/useK8sData';

const TABS = [
  { label: 'Cluster Overview', icon: '🖥️' },
  { label: 'YAML Editor', icon: '📝' },
];

function StatCard({ label, value, colorClass, subtext }) {
  return (
    <div className={`bg-white rounded-xl border shadow-sm px-5 py-4 flex flex-col gap-1 ${colorClass}`}>
      <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">{label}</span>
      <span className="text-2xl font-bold text-gray-800">{value}</span>
      {subtext && <span className="text-xs text-gray-400">{subtext}</span>}
    </div>
  );
}

export default function Dashboard() {
  const { pods, clusterStatus, loading, error, refresh } = useK8sData();
  const [activeTab, setActiveTab] = useState(0);
  const [diagnoseResult, setDiagnoseResult] = useState(null);
  const [refreshing, setRefreshing] = useState(false);

  const handleRefresh = async () => {
    setRefreshing(true);
    await refresh();
    setTimeout(() => setRefreshing(false), 600);
  };

  const runningPods = pods.filter((p) => p.status === 'Running' || p.status === 'Succeeded').length;
  const unhealthyPods = pods.filter((p) => p.status !== 'Running' && p.status !== 'Succeeded').length;
  const isConnected = clusterStatus?.status === 'connected';

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Top nav */}
      <header className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between shadow-sm">
        <div className="flex items-center gap-3">
          <span className="text-2xl select-none">🦞</span>
          <div>
            <span className="font-bold text-gray-800 text-lg leading-none">Lobster K8s Copilot</span>
            <p className="text-xs text-gray-400 leading-none mt-0.5">Kubernetes AI Diagnostics</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {clusterStatus ? (
            <span className={`flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-full ${
              isConnected ? 'bg-green-50 text-green-700 ring-1 ring-green-200' : 'bg-red-50 text-red-700 ring-1 ring-red-200'
            }`}>
              <span className={`w-1.5 h-1.5 rounded-full ${isConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`} />
              {isConnected ? 'Connected' : 'Disconnected'}
            </span>
          ) : !loading && (
            <span className="text-xs text-gray-400">No cluster status</span>
          )}
          <button
            onClick={handleRefresh}
            disabled={loading || refreshing}
            className="flex items-center gap-1.5 text-xs text-gray-500 hover:text-indigo-600 px-3 py-1.5 rounded-lg border border-gray-200 hover:border-indigo-300 hover:bg-indigo-50 transition-all disabled:opacity-40"
          >
            <svg className={`w-3 h-3 ${refreshing ? 'animate-spin' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Refresh
          </button>
        </div>
      </header>

      {/* Stats bar – only on Cluster Overview when data is available */}
      {activeTab === 0 && !loading && !error && pods.length > 0 && (
        <div className="bg-white border-b border-gray-100 px-6 py-4">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 max-w-3xl">
            <StatCard label="Total Pods" value={pods.length} subtext="across all namespaces" />
            <StatCard
              label="Healthy"
              value={runningPods}
              colorClass="border-l-4 border-l-green-400"
              subtext="Running / Succeeded"
            />
            {unhealthyPods > 0 && (
              <StatCard
                label="Unhealthy"
                value={unhealthyPods}
                colorClass="border-l-4 border-l-red-400"
                subtext="Need attention"
              />
            )}
            {clusterStatus?.version && (
              <StatCard label="K8s Version" value={clusterStatus.version} subtext="cluster version" />
            )}
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="border-b border-gray-200 bg-white px-6">
        <nav className="flex gap-1">
          {TABS.map(({ label, icon }, i) => (
            <button
              key={label}
              onClick={() => setActiveTab(i)}
              className={`flex items-center gap-1.5 py-3 px-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === i
                  ? 'border-indigo-600 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <span>{icon}</span>
              {label}
            </button>
          ))}
        </nav>
      </div>

      {/* Main content */}
      <main className="p-6 max-w-screen-xl mx-auto">
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
