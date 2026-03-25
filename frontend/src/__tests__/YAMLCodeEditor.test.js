import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import YAMLCodeEditor from '../components/YAMLCodeEditor';
import * as api from '../utils/api';

// Mock the API
jest.mock('../utils/api', () => ({
  scanYaml: jest.fn(),
}));

// Mock Monaco Editor - simple version
jest.mock('@monaco-editor/react', () => ({
  __esModule: true,
  default: ({ value, onChange }) => (
    <textarea
      data-testid="monaco-editor"
      value={value}
      onChange={(e) => onChange(e.target.value)}
    />
  ),
}));

describe('YAMLCodeEditor Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Initial Render', () => {
    test('renders editor with default YAML', () => {
      render(<YAMLCodeEditor />);

      const editor = screen.getByTestId('monaco-editor');
      expect(editor.value).toContain('apiVersion: apps/v1');
      expect(editor.value).toContain('kind: Deployment');
    });

    test('renders scan button', () => {
      render(<YAMLCodeEditor />);

      expect(screen.getByText('🔍 Scan YAML')).toBeInTheDocument();
    });

    test('renders header title', () => {
      render(<YAMLCodeEditor />);

      expect(screen.getByText('📝 YAML Editor')).toBeInTheDocument();
    });
  });

  describe('Scan Operation', () => {
    test('calls scanYaml API when scan button is clicked', async () => {
      api.scanYaml.mockResolvedValue({
        issues: [],
        total_issues: 0,
        has_errors: false,
      });

      render(<YAMLCodeEditor />);

      const scanButton = screen.getByText('🔍 Scan YAML');
      fireEvent.click(scanButton);

      await waitFor(() => {
        expect(api.scanYaml).toHaveBeenCalled();
      });
    });

    test('shows scanning state while API call is in progress', async () => {
      api.scanYaml.mockImplementation(
        () => new Promise((resolve) => setTimeout(resolve, 100))
      );

      render(<YAMLCodeEditor />);

      const scanButton = screen.getByText('🔍 Scan YAML');
      fireEvent.click(scanButton);

      expect(screen.getByText('Scanning…')).toBeInTheDocument();
    });

    test('displays no critical issues banner when scan passes', async () => {
      api.scanYaml.mockResolvedValue({
        issues: [],
        total_issues: 0,
        has_errors: false,
      });

      render(<YAMLCodeEditor />);

      const scanButton = screen.getByText('🔍 Scan YAML');
      fireEvent.click(scanButton);

      await waitFor(() => {
        expect(screen.getByText('✅ No critical issues')).toBeInTheDocument();
      });
    });

    test('displays issues found banner when scan finds errors', async () => {
      api.scanYaml.mockResolvedValue({
        issues: [
          { severity: 'ERROR', rule: 'no-resource-limits', message: 'Missing limits' },
        ],
        total_issues: 1,
        has_errors: true,
      });

      render(<YAMLCodeEditor />);

      const scanButton = screen.getByText('🔍 Scan YAML');
      fireEvent.click(scanButton);

      await waitFor(() => {
        expect(screen.getByText('❌ Issues found')).toBeInTheDocument();
      });
    });
  });

  describe('Error Handling', () => {
    test('displays error message when scan fails', async () => {
      api.scanYaml.mockRejectedValue(new Error('Server unavailable'));

      render(<YAMLCodeEditor />);

      const scanButton = screen.getByText('🔍 Scan YAML');
      fireEvent.click(scanButton);

      await waitFor(() => {
        expect(screen.getByText('Scan Failed')).toBeInTheDocument();
        expect(screen.getByText('Server unavailable')).toBeInTheDocument();
      });
    });
  });

  describe('Issues Display', () => {
    const mockScanResult = {
      issues: [
        { severity: 'ERROR', rule: 'no-resource-limits', message: 'Container missing limits' },
        { severity: 'WARNING', rule: 'latest-image-tag', message: 'Using latest tag' },
        { severity: 'INFO', rule: 'suggestion', message: 'Consider adding probes' },
      ],
      total_issues: 3,
      has_errors: true,
    };

    test('renders all issues', async () => {
      api.scanYaml.mockResolvedValue(mockScanResult);

      render(<YAMLCodeEditor />);

      const scanButton = screen.getByText('🔍 Scan YAML');
      fireEvent.click(scanButton);

      await waitFor(() => {
        expect(screen.getByText('Container missing limits')).toBeInTheDocument();
        expect(screen.getByText('Using latest tag')).toBeInTheDocument();
        expect(screen.getByText('Consider adding probes')).toBeInTheDocument();
      });
    });

    test('displays severity badges', async () => {
      api.scanYaml.mockResolvedValue(mockScanResult);

      render(<YAMLCodeEditor />);

      const scanButton = screen.getByText('🔍 Scan YAML');
      fireEvent.click(scanButton);

      await waitFor(() => {
        expect(screen.getAllByText('ERROR').length).toBeGreaterThan(0);
        expect(screen.getAllByText('WARNING').length).toBeGreaterThan(0);
        expect(screen.getAllByText('INFO').length).toBeGreaterThan(0);
      });
    });

    test('displays rule names', async () => {
      api.scanYaml.mockResolvedValue(mockScanResult);

      render(<YAMLCodeEditor />);

      const scanButton = screen.getByText('🔍 Scan YAML');
      fireEvent.click(scanButton);

      await waitFor(() => {
        expect(screen.getByText('no-resource-limits')).toBeInTheDocument();
        expect(screen.getByText('latest-image-tag')).toBeInTheDocument();
      });
    });
  });

  describe('Filter Tabs', () => {
    const mockScanResult = {
      issues: [
        { severity: 'ERROR', rule: 'error-rule', message: 'Error message' },
        { severity: 'WARNING', rule: 'warning-rule', message: 'Warning message' },
      ],
      total_issues: 2,
      has_errors: true,
    };

    test('renders filter buttons after scan', async () => {
      api.scanYaml.mockResolvedValue(mockScanResult);

      render(<YAMLCodeEditor />);

      const scanButton = screen.getByText('🔍 Scan YAML');
      fireEvent.click(scanButton);

      await waitFor(() => {
        expect(screen.getByText('All (2)')).toBeInTheDocument();
        expect(screen.getByText('Errors (1)')).toBeInTheDocument();
        expect(screen.getByText('Warnings (1)')).toBeInTheDocument();
      });
    });

    test('filters issues when ERROR filter is clicked', async () => {
      api.scanYaml.mockResolvedValue(mockScanResult);

      render(<YAMLCodeEditor />);

      const scanButton = screen.getByText('🔍 Scan YAML');
      fireEvent.click(scanButton);

      await waitFor(() => {
        expect(screen.getByText('Errors (1)')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Errors (1)'));

      await waitFor(() => {
        expect(screen.getByText('Error message')).toBeInTheDocument();
        expect(screen.queryByText('Warning message')).not.toBeInTheDocument();
      });
    });
  });

  describe('AI Suggestions', () => {
    test('displays AI suggestions when present', async () => {
      api.scanYaml.mockResolvedValue({
        issues: [{ severity: 'WARNING', rule: 'test', message: 'test' }],
        total_issues: 1,
        has_errors: false,
        ai_suggestions: 'Add resource limits to prevent OOM issues.',
      });

      render(<YAMLCodeEditor />);

      const scanButton = screen.getByText('🔍 Scan YAML');
      fireEvent.click(scanButton);

      await waitFor(() => {
        expect(screen.getByText('🤖 AI Suggestions')).toBeInTheDocument();
        expect(screen.getByText('Add resource limits to prevent OOM issues.')).toBeInTheDocument();
      });
    });

    test('does not display AI suggestions section when not present', async () => {
      api.scanYaml.mockResolvedValue({
        issues: [],
        total_issues: 0,
        has_errors: false,
      });

      render(<YAMLCodeEditor />);

      const scanButton = screen.getByText('🔍 Scan YAML');
      fireEvent.click(scanButton);

      await waitFor(() => {
        expect(screen.queryByText('🤖 AI Suggestions')).not.toBeInTheDocument();
      });
    });
  });

  describe('Editor Interaction', () => {
    test('updates YAML content when editor changes', () => {
      render(<YAMLCodeEditor />);

      const editor = screen.getByTestId('monaco-editor');
      fireEvent.change(editor, { target: { value: 'kind: Pod' } });

      expect(editor.value).toBe('kind: Pod');
    });
  });
});
