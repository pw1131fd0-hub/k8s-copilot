import React, { useState, useRef, useEffect } from 'react';
import Editor from '@monaco-editor/react';
import { scanYaml } from '../utils/api';

const SEVERITY_CONFIG = {
  ERROR:   { bg: 'bg-red-50',    border: 'border-red-300',    icon: '❌', text: 'text-red-700',    badge: 'bg-red-100 text-red-700',    label: 'Error'   },
  WARNING: { bg: 'bg-amber-50',  border: 'border-amber-300',  icon: '⚠️', text: 'text-amber-700',  badge: 'bg-amber-100 text-amber-700', label: 'Warning' },
  INFO:    { bg: 'bg-blue-50',   border: 'border-blue-300',   icon: 'ℹ️', text: 'text-blue-700',   badge: 'bg-blue-100 text-blue-700',   label: 'Info'    },
};

const DEFAULT_YAML = `apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  replicas: 1
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
        image: my-app:latest
`;

export default function YAMLCodeEditor() {
  const [yaml, setYaml] = useState(DEFAULT_YAML);
  const [scanning, setScanning] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState('ALL');

  const editorRef = useRef(null);
  const monacoRef = useRef(null);

  const handleEditorDidMount = (editor, monaco) => {
    editorRef.current = editor;
    monacoRef.current = monaco;
  };

  // Update editor markers whenever results change
  useEffect(() => {
    if (!monacoRef.current || !editorRef.current) return;
    const model = editorRef.current.getModel();
    if (!model) return;
    const markers = (result?.issues || [])
      .filter((i) => i.line)
      .map((i) => ({
        startLineNumber: i.line,
        endLineNumber: i.line,
        startColumn: 1,
        endColumn: 200,
        message: `[${i.rule}] ${i.message}`,
        severity:
          i.severity === 'ERROR'
            ? monacoRef.current.MarkerSeverity.Error
            : i.severity === 'WARNING'
            ? monacoRef.current.MarkerSeverity.Warning
            : monacoRef.current.MarkerSeverity.Info,
      }));
    monacoRef.current.editor.setModelMarkers(model, 'lobster', markers);
  }, [result]);

  const handleScan = async () => {
    setScanning(true);
    setResult(null);
    setError(null);
    setFilter('ALL');
    try {
      const data = await scanYaml(yaml);
      setResult(data);
    } catch (e) {
      setError(e.message || 'Scan failed');
    } finally {
      setScanning(false);
    }
  };

  const counts = {
    ERROR:   result?.issues?.filter((i) => i.severity === 'ERROR').length   || 0,
    WARNING: result?.issues?.filter((i) => i.severity === 'WARNING').length || 0,
    INFO:    result?.issues?.filter((i) => i.severity === 'INFO').length    || 0,
  };

  const visibleIssues =
    filter === 'ALL'
      ? result?.issues || []
      : (result?.issues || []).filter((i) => i.severity === filter);

  return (
    <div className="flex flex-col gap-4">
      {/* Toolbar */}
      <div className="flex items-center justify-between">
        <h2 className="text-base font-semibold text-gray-700">📝 YAML Editor</h2>
        <button
          onClick={handleScan}
          disabled={scanning}
          className="flex items-center gap-1.5 px-4 py-1.5 text-sm font-medium rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50 transition-colors shadow-sm"
        >
          {scanning ? (
            <>
              <svg className="animate-spin h-3.5 w-3.5" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
              </svg>
              Scanning…
            </>
          ) : (
            <>🔍 Scan YAML</>
          )}
        </button>
      </div>

      {/* Monaco Editor */}
      <div className="rounded-xl overflow-hidden border border-gray-200 shadow-sm">
        <Editor
          height="360px"
          language="yaml"
          value={yaml}
          onChange={(v) => setYaml(v || '')}
          theme="vs-light"
          options={{
            minimap: { enabled: false },
            fontSize: 13,
            lineNumbers: 'on',
            scrollBeyondLastLine: false,
            renderLineHighlight: 'gutter',
          }}
          onMount={handleEditorDidMount}
        />
      </div>

      {/* Error from backend */}
      {error && (
        <div className="flex items-start gap-2.5 rounded-xl bg-red-50 border border-red-200 p-4 text-sm text-red-700 shadow-sm">
          <span className="mt-0.5 shrink-0">🚨</span>
          <div>
            <p className="font-semibold">Scan Failed</p>
            <p className="mt-0.5 text-red-600">{error}</p>
          </div>
        </div>
      )}

      {/* Summary banner */}
      {result && (
        <div className={`rounded-xl border p-4 shadow-sm ${
          result.has_errors
            ? 'bg-red-50 border-red-200'
            : 'bg-green-50 border-green-200'
        }`}>
          <div className="flex flex-wrap items-center gap-3">
            <span className={`text-sm font-semibold ${result.has_errors ? 'text-red-700' : 'text-green-700'}`}>
              {result.has_errors ? '❌ Issues found' : '✅ No critical issues'}
            </span>
            <span className="text-xs text-gray-500">
              {result.total_issues} issue{result.total_issues !== 1 ? 's' : ''} detected
            </span>
            {/* Per-severity count chips */}
            <div className="flex gap-2 ml-auto flex-wrap">
              {(['ERROR', 'WARNING', 'INFO']).map((sev) => (
                counts[sev] > 0 && (
                  <span
                    key={sev}
                    className={`text-xs font-semibold px-2 py-0.5 rounded-full ${SEVERITY_CONFIG[sev].badge}`}
                  >
                    {counts[sev]} {SEVERITY_CONFIG[sev].label}{counts[sev] !== 1 ? 's' : ''}
                  </span>
                )
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Filter tabs */}
      {result && result.total_issues > 0 && (
        <div className="flex gap-1.5 flex-wrap">
          {['ALL', 'ERROR', 'WARNING', 'INFO'].map((f) => {
            const count = f === 'ALL' ? result.total_issues : counts[f];
            if (f !== 'ALL' && count === 0) return null;
            const active = filter === f;
            const cfg = f !== 'ALL' ? SEVERITY_CONFIG[f] : null;
            return (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`text-xs font-medium px-3 py-1 rounded-full border transition-colors ${
                  active
                    ? cfg
                      ? `${cfg.badge} border-current`
                      : 'bg-indigo-600 text-white border-indigo-600'
                    : 'bg-white text-gray-500 border-gray-200 hover:border-gray-300'
                }`}
              >
                {f === 'ALL' ? `All (${count})` : `${cfg.label}s (${count})`}
              </button>
            );
          })}
        </div>
      )}

      {/* Issue list */}
      {result && visibleIssues.length > 0 && (
        <div className="space-y-2">
          {visibleIssues.map((issue, idx) => {
            const cfg = SEVERITY_CONFIG[issue.severity] || SEVERITY_CONFIG.INFO;
            return (
              <div key={idx} className={`rounded-xl border p-3.5 ${cfg.bg} ${cfg.border} shadow-sm`}>
                <div className="flex items-start gap-2.5">
                  <span className="text-base shrink-0 mt-0.5">{cfg.icon}</span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap mb-1">
                      <span className={`text-xs font-bold uppercase tracking-wide ${cfg.text}`}>
                        {issue.severity}
                      </span>
                      <span className="text-xs font-mono bg-white/60 border border-current/20 rounded px-1.5 py-0.5 text-gray-600">
                        {issue.rule}
                      </span>
                      {issue.line && (
                        <span className="text-xs font-mono text-gray-400 ml-auto">
                          Line {issue.line}
                        </span>
                      )}
                    </div>
                    <p className={`text-sm ${cfg.text}`}>{issue.message}</p>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* AI suggestions */}
      {result?.ai_suggestions && (
        <div className="rounded-xl border border-indigo-200 bg-gradient-to-br from-indigo-50 to-violet-50 p-4 shadow-sm">
          <p className="text-sm font-semibold text-indigo-800 mb-2 flex items-center gap-1.5">
            🤖 AI Suggestions
          </p>
          <p className="text-sm text-indigo-700 whitespace-pre-wrap leading-relaxed">
            {result.ai_suggestions}
          </p>
        </div>
      )}
    </div>
  );
}

