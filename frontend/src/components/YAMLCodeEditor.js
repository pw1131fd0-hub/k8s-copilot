import React, { useState } from 'react';
import Editor from '@monaco-editor/react';
import { scanYaml } from '../utils/api';

const SEVERITY_CONFIG = {
  ERROR: { bg: 'bg-red-50', border: 'border-red-300', icon: '❌', text: 'text-red-700' },
  WARNING: { bg: 'bg-yellow-50', border: 'border-yellow-300', icon: '⚠️', text: 'text-yellow-700' },
  INFO: { bg: 'bg-blue-50', border: 'border-blue-300', icon: 'ℹ️', text: 'text-blue-700' },
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

  const handleScan = async () => {
    setScanning(true);
    setResult(null);
    setError(null);
    try {
      const data = await scanYaml(yaml);
      setResult(data);
    } catch (e) {
      setError(e.message || 'Scan failed');
    } finally {
      setScanning(false);
    }
  };

  const markers = result?.issues
    ?.filter((i) => i.line)
    .map((i) => ({
      startLineNumber: i.line,
      endLineNumber: i.line,
      startColumn: 1,
      endColumn: 100,
      message: i.message,
      severity: i.severity === 'ERROR' ? 8 : 4,
    })) || [];

  return (
    <div className="flex flex-col gap-4">
      {/* Toolbar */}
      <div className="flex items-center justify-between">
        <h2 className="text-base font-semibold text-gray-700">📝 YAML Editor</h2>
        <button
          onClick={handleScan}
          disabled={scanning}
          className="px-4 py-1.5 text-sm font-medium rounded bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50 transition-colors"
        >
          {scanning ? 'Scanning…' : '🔍 Scan YAML'}
        </button>
      </div>

      {/* Monaco Editor */}
      <div className="rounded-lg overflow-hidden border border-gray-200">
        <Editor
          height="350px"
          language="yaml"
          value={yaml}
          onChange={(v) => setYaml(v || '')}
          theme="vs-light"
          options={{
            minimap: { enabled: false },
            fontSize: 13,
            lineNumbers: 'on',
            scrollBeyondLastLine: false,
          }}
          beforeMount={(monaco) => {
            // Attach markers after scan
            if (markers.length > 0) {
              const model = monaco.editor.getModels()[0];
              if (model) monaco.editor.setModelMarkers(model, 'lobster', markers);
            }
          }}
        />
      </div>

      {/* Results panel */}
      {error && (
        <div className="rounded bg-red-50 border border-red-200 p-3 text-sm text-red-700">
          ⚠️ {error}
        </div>
      )}

      {result && (
        <div className="space-y-3">
          <div className="flex items-center gap-3">
            <span className={`text-sm font-medium ${result.has_errors ? 'text-red-600' : 'text-green-600'}`}>
              {result.has_errors ? '❌ Issues found' : '✅ No critical issues'}
            </span>
            <span className="text-xs text-gray-500">{result.total_issues} issue(s) detected</span>
          </div>

          {result.issues.map((issue, idx) => {
            const cfg = SEVERITY_CONFIG[issue.severity] || SEVERITY_CONFIG.INFO;
            return (
              <div key={idx} className={`rounded border p-3 ${cfg.bg} ${cfg.border}`}>
                <div className="flex items-start gap-2">
                  <span>{cfg.icon}</span>
                  <div>
                    <span className={`text-xs font-semibold ${cfg.text} uppercase mr-2`}>{issue.severity}</span>
                    <span className="text-xs font-mono text-gray-500">[{issue.rule}]</span>
                    <p className={`text-sm mt-0.5 ${cfg.text}`}>{issue.message}</p>
                  </div>
                </div>
              </div>
            );
          })}

          {result.ai_suggestions && (
            <div className="rounded border border-indigo-200 bg-indigo-50 p-3 text-sm text-indigo-800">
              <p className="font-semibold mb-1">🤖 AI Suggestions</p>
              <p className="whitespace-pre-wrap">{result.ai_suggestions}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
