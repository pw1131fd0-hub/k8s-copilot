import React, { useState } from 'react';
import Editor from '@monaco-editor/react';
import { diffYaml } from '../utils/api';

const CHANGE_TYPE_CONFIG = {
  values_changed: { icon: '✏️', label: 'Modified', bg: 'bg-amber-50', border: 'border-amber-200', text: 'text-amber-700' },
  iterable_item_added: { icon: '➕', label: 'Added', bg: 'bg-green-50', border: 'border-green-200', text: 'text-green-700' },
  iterable_item_removed: { icon: '➖', label: 'Removed', bg: 'bg-red-50', border: 'border-red-200', text: 'text-red-700' },
  dictionary_item_added: { icon: '➕', label: 'Added Key', bg: 'bg-green-50', border: 'border-green-200', text: 'text-green-700' },
  dictionary_item_removed: { icon: '➖', label: 'Removed Key', bg: 'bg-red-50', border: 'border-red-200', text: 'text-red-700' },
  type_changes: { icon: '🔄', label: 'Type Changed', bg: 'bg-purple-50', border: 'border-purple-200', text: 'text-purple-700' },
};

function formatPath(path) {
  return path
    .replace(/^root\['?/, '')
    .replace(/'\]$/g, '')
    .replace(/'\]\['?/g, '.')
    .replace(/\[(\d+)\]/g, '[$1]');
}

function DiffChangeCard({ changeType, path, value }) {
  const cfg = CHANGE_TYPE_CONFIG[changeType] || CHANGE_TYPE_CONFIG.values_changed;

  return (
    <div className={`rounded-xl border p-3 ${cfg.bg} ${cfg.border}`}>
      <div className="flex items-start gap-2">
        <span className="text-lg shrink-0">{cfg.icon}</span>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-1">
            <span className={`text-xs font-bold uppercase tracking-wide ${cfg.text}`}>
              {cfg.label}
            </span>
            <code className="text-xs bg-white/60 border border-current/20 rounded px-1.5 py-0.5 text-gray-700 font-mono truncate max-w-[400px]">
              {formatPath(path)}
            </code>
          </div>
          {changeType === 'values_changed' && value && (
            <div className="space-y-1 text-sm">
              <div className="flex items-start gap-2">
                <span className="text-xs text-gray-500 w-12 shrink-0 font-medium">Old:</span>
                <pre className="text-red-600 bg-red-50 px-2 py-0.5 rounded text-xs font-mono whitespace-pre-wrap break-all">
                  {JSON.stringify(value.old_value, null, 2)}
                </pre>
              </div>
              <div className="flex items-start gap-2">
                <span className="text-xs text-gray-500 w-12 shrink-0 font-medium">New:</span>
                <pre className="text-green-600 bg-green-50 px-2 py-0.5 rounded text-xs font-mono whitespace-pre-wrap break-all">
                  {JSON.stringify(value.new_value, null, 2)}
                </pre>
              </div>
            </div>
          )}
          {changeType === 'type_changes' && value && (
            <p className="text-xs text-gray-600">
              Type changed from <code className="bg-white px-1 rounded">{value.old_type}</code> to <code className="bg-white px-1 rounded">{value.new_type}</code>
            </p>
          )}
          {changeType.includes('added') && typeof value === 'object' && (
            <pre className="text-xs text-green-700 bg-white/50 rounded p-2 mt-1 font-mono whitespace-pre-wrap">
              {JSON.stringify(value, null, 2)}
            </pre>
          )}
          {changeType.includes('removed') && typeof value === 'object' && (
            <pre className="text-xs text-red-700 bg-white/50 rounded p-2 mt-1 font-mono whitespace-pre-wrap">
              {JSON.stringify(value, null, 2)}
            </pre>
          )}
        </div>
      </div>
    </div>
  );
}

const SAMPLE_YAML_A = `apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  replicas: 2
  selector:
    matchLabels:
      app: my-app
  template:
    metadata:
      labels:
        app: my-app
    spec:
      containers:
      - name: my-app
        image: my-app:1.0.0
        resources:
          limits:
            cpu: 100m
            memory: 128Mi
`;

const SAMPLE_YAML_B = `apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: my-app
  template:
    metadata:
      labels:
        app: my-app
    spec:
      containers:
      - name: my-app
        image: my-app:2.0.0
        resources:
          limits:
            cpu: 200m
            memory: 256Mi
`;

export default function YamlDiffPanel() {
  const [yamlA, setYamlA] = useState(SAMPLE_YAML_A);
  const [yamlB, setYamlB] = useState(SAMPLE_YAML_B);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleDiff = async () => {
    setLoading(true);
    setResult(null);
    setError(null);
    try {
      const data = await diffYaml(yamlA, yamlB);
      setResult(data);
    } catch (e) {
      setError(e.message || 'Diff failed');
    } finally {
      setLoading(false);
    }
  };

  const totalChanges = result
    ? Object.entries(result).reduce((sum, [key, val]) => {
        if (key === 'error') return sum;
        if (Array.isArray(val)) return sum + val.length;
        if (typeof val === 'object') return sum + Object.keys(val).length;
        return sum;
      }, 0)
    : 0;

  const renderChanges = () => {
    if (!result || result.error) return null;
    const changes = [];
    Object.entries(result).forEach(([changeType, data]) => {
      if (!CHANGE_TYPE_CONFIG[changeType]) return;
      if (Array.isArray(data)) {
        data.forEach((path, idx) => {
          changes.push(
            <DiffChangeCard key={`${changeType}-${idx}`} changeType={changeType} path={path} value={null} />
          );
        });
      } else if (typeof data === 'object') {
        Object.entries(data).forEach(([path, value]) => {
          changes.push(
            <DiffChangeCard key={`${changeType}-${path}`} changeType={changeType} path={path} value={value} />
          );
        });
      }
    });
    return changes;
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-base font-semibold text-gray-700">📊 YAML Diff</h2>
        <button
          onClick={handleDiff}
          disabled={loading}
          className="flex items-center gap-1.5 px-4 py-1.5 text-sm font-medium rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50 transition-colors shadow-sm"
        >
          {loading ? (
            <>
              <svg className="animate-spin h-3.5 w-3.5" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
              </svg>
              Comparing…
            </>
          ) : (
            <>🔍 Compare YAML</>
          )}
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-gray-600">📁 Source (A)</span>
            <span className="text-xs text-gray-400">e.g., dev environment</span>
          </div>
          <div className="rounded-xl overflow-hidden border border-gray-200 shadow-sm">
            <Editor
              height="280px"
              language="yaml"
              value={yamlA}
              onChange={(v) => setYamlA(v || '')}
              theme="vs-light"
              options={{
                minimap: { enabled: false },
                fontSize: 12,
                lineNumbers: 'on',
                scrollBeyondLastLine: false,
                renderLineHighlight: 'gutter',
              }}
            />
          </div>
        </div>

        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-gray-600">📁 Target (B)</span>
            <span className="text-xs text-gray-400">e.g., prod environment</span>
          </div>
          <div className="rounded-xl overflow-hidden border border-gray-200 shadow-sm">
            <Editor
              height="280px"
              language="yaml"
              value={yamlB}
              onChange={(v) => setYamlB(v || '')}
              theme="vs-light"
              options={{
                minimap: { enabled: false },
                fontSize: 12,
                lineNumbers: 'on',
                scrollBeyondLastLine: false,
                renderLineHighlight: 'gutter',
              }}
            />
          </div>
        </div>
      </div>

      {error && (
        <div className="rounded-xl bg-red-50 border border-red-200 p-4 text-red-700 text-sm">
          ⚠️ {error}
        </div>
      )}

      {result?.error && (
        <div className="rounded-xl bg-red-50 border border-red-200 p-4 text-red-700 text-sm">
          ⚠️ YAML Parse Error: {result.error}
        </div>
      )}

      {result && !result.error && (
        <div className={`rounded-xl border p-4 ${
          totalChanges === 0
            ? 'bg-green-50 border-green-200'
            : 'bg-amber-50 border-amber-200'
        }`}>
          <div className="flex items-center gap-2">
            <span className={`text-sm font-semibold ${totalChanges === 0 ? 'text-green-700' : 'text-amber-700'}`}>
              {totalChanges === 0 ? '✅ YAMLs are identical' : `📊 ${totalChanges} difference${totalChanges !== 1 ? 's' : ''} found`}
            </span>
          </div>
        </div>
      )}

      {result && !result.error && totalChanges > 0 && (
        <div className="space-y-2">
          <h3 className="text-sm font-semibold text-gray-700">Differences:</h3>
          <div className="space-y-2">
            {renderChanges()}
          </div>
        </div>
      )}
    </div>
  );
}
