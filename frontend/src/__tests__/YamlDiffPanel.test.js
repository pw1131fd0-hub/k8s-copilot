import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import YamlDiffPanel from '../components/YamlDiffPanel';
import * as api from '../utils/api';

// Mock the API
jest.mock('../utils/api', () => ({
  diffYaml: jest.fn(),
}));

// Mock Monaco Editor
jest.mock('@monaco-editor/react', () => {
  return function MockEditor({ value, onChange }) {
    return (
      <textarea
        data-testid="monaco-editor"
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
    );
  };
});

describe('YamlDiffPanel Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Initial Render', () => {
    test('renders two editors', () => {
      render(<YamlDiffPanel />);

      const editors = screen.getAllByTestId('monaco-editor');
      expect(editors).toHaveLength(2);
    });

    test('renders compare button', () => {
      render(<YamlDiffPanel />);

      expect(screen.getByText('🔍 Compare YAML')).toBeInTheDocument();
    });

    test('renders header title', () => {
      render(<YamlDiffPanel />);

      expect(screen.getByText('📊 YAML Diff')).toBeInTheDocument();
    });

    test('renders source and target labels', () => {
      render(<YamlDiffPanel />);

      expect(screen.getByText('📁 Source (A)')).toBeInTheDocument();
      expect(screen.getByText('📁 Target (B)')).toBeInTheDocument();
    });

    test('editors contain sample YAML content', () => {
      render(<YamlDiffPanel />);

      const editors = screen.getAllByTestId('monaco-editor');
      expect(editors[0].value).toContain('replicas: 2');
      expect(editors[1].value).toContain('replicas: 3');
    });
  });

  describe('Compare Operation', () => {
    test('calls diffYaml API when compare button is clicked', async () => {
      api.diffYaml.mockResolvedValue({
        differences: {},
        summary: { total_changes: 0 },
        risk_assessment: [],
      });

      render(<YamlDiffPanel />);

      const compareButton = screen.getByText('🔍 Compare YAML');
      fireEvent.click(compareButton);

      await waitFor(() => {
        expect(api.diffYaml).toHaveBeenCalled();
      });
    });

    test('shows comparing state while API call is in progress', async () => {
      api.diffYaml.mockImplementation(
        () => new Promise((resolve) => setTimeout(resolve, 100))
      );

      render(<YamlDiffPanel />);

      const compareButton = screen.getByText('🔍 Compare YAML');
      fireEvent.click(compareButton);

      expect(screen.getByText('Comparing…')).toBeInTheDocument();
    });

    test('displays identical banner when no differences', async () => {
      api.diffYaml.mockResolvedValue({
        differences: {},
        summary: { total_changes: 0, values_changed: 0, items_added: 0, items_removed: 0 },
        risk_assessment: [],
      });

      render(<YamlDiffPanel />);

      const compareButton = screen.getByText('🔍 Compare YAML');
      fireEvent.click(compareButton);

      await waitFor(() => {
        expect(screen.getByText('✅ YAMLs are identical')).toBeInTheDocument();
      });
    });

    test('displays differences count when changes found', async () => {
      api.diffYaml.mockResolvedValue({
        differences: {
          values_changed: { "root['spec']['replicas']": { old_value: 2, new_value: 3 } },
        },
        summary: { total_changes: 1, values_changed: 1, items_added: 0, items_removed: 0 },
        risk_assessment: [],
      });

      render(<YamlDiffPanel />);

      const compareButton = screen.getByText('🔍 Compare YAML');
      fireEvent.click(compareButton);

      await waitFor(() => {
        expect(screen.getByText(/1 difference found/)).toBeInTheDocument();
      });
    });
  });

  describe('Error Handling', () => {
    test('displays error message when API call fails', async () => {
      api.diffYaml.mockRejectedValue(new Error('Server error'));

      render(<YamlDiffPanel />);

      const compareButton = screen.getByText('🔍 Compare YAML');
      fireEvent.click(compareButton);

      await waitFor(() => {
        expect(screen.getByText(/Server error/)).toBeInTheDocument();
      });
    });

    test('displays YAML parse error from API', async () => {
      api.diffYaml.mockResolvedValue({
        error: 'Invalid YAML syntax on line 5',
      });

      render(<YamlDiffPanel />);

      const compareButton = screen.getByText('🔍 Compare YAML');
      fireEvent.click(compareButton);

      await waitFor(() => {
        expect(screen.getByText(/Invalid YAML syntax/)).toBeInTheDocument();
      });
    });
  });

  describe('Differences Display', () => {
    test('renders value changes', async () => {
      api.diffYaml.mockResolvedValue({
        differences: {
          values_changed: {
            "root['spec']['replicas']": { old_value: 2, new_value: 3 },
          },
        },
        summary: { total_changes: 1, values_changed: 1, items_added: 0, items_removed: 0 },
        risk_assessment: [],
      });

      render(<YamlDiffPanel />);

      const compareButton = screen.getByText('🔍 Compare YAML');
      fireEvent.click(compareButton);

      await waitFor(() => {
        expect(screen.getByText('Modified')).toBeInTheDocument();
        expect(screen.getByText('2')).toBeInTheDocument();
        expect(screen.getByText('3')).toBeInTheDocument();
      });
    });

    test('renders added items', async () => {
      api.diffYaml.mockResolvedValue({
        differences: {
          dictionary_item_added: {
            "root['metadata']['labels']": { env: 'production' },
          },
        },
        summary: { total_changes: 1, values_changed: 0, items_added: 1, items_removed: 0 },
        risk_assessment: [],
      });

      render(<YamlDiffPanel />);

      const compareButton = screen.getByText('🔍 Compare YAML');
      fireEvent.click(compareButton);

      await waitFor(() => {
        expect(screen.getByText('Added Key')).toBeInTheDocument();
      });
    });

    test('renders removed items', async () => {
      api.diffYaml.mockResolvedValue({
        differences: {
          dictionary_item_removed: {
            "root['metadata']['annotations']": { old: 'value' },
          },
        },
        summary: { total_changes: 1, values_changed: 0, items_added: 0, items_removed: 1 },
        risk_assessment: [],
      });

      render(<YamlDiffPanel />);

      const compareButton = screen.getByText('🔍 Compare YAML');
      fireEvent.click(compareButton);

      await waitFor(() => {
        expect(screen.getByText('Removed Key')).toBeInTheDocument();
      });
    });
  });

  describe('Risk Assessment', () => {
    test('renders risk assessment section when present', async () => {
      api.diffYaml.mockResolvedValue({
        differences: {
          values_changed: { "root['spec']['replicas']": { old_value: 2, new_value: 3 } },
        },
        summary: { total_changes: 1, values_changed: 1, items_added: 0, items_removed: 0 },
        risk_assessment: [
          { path: 'spec.replicas', risk: 'HIGH', message: 'Replica count change affects availability' },
        ],
      });

      render(<YamlDiffPanel />);

      const compareButton = screen.getByText('🔍 Compare YAML');
      fireEvent.click(compareButton);

      await waitFor(() => {
        expect(screen.getByText('⚠️ Risk Assessment')).toBeInTheDocument();
        expect(screen.getByText('HIGH')).toBeInTheDocument();
        expect(screen.getByText('Replica count change affects availability')).toBeInTheDocument();
      });
    });

    test('shows high risk count badge', async () => {
      api.diffYaml.mockResolvedValue({
        differences: {
          values_changed: { "root['spec']['replicas']": { old_value: 2, new_value: 3 } },
        },
        summary: { total_changes: 1, values_changed: 1, items_added: 0, items_removed: 0 },
        risk_assessment: [
          { path: 'spec.replicas', risk: 'HIGH', message: 'Risk 1' },
          { path: 'spec.image', risk: 'HIGH', message: 'Risk 2' },
        ],
      });

      render(<YamlDiffPanel />);

      const compareButton = screen.getByText('🔍 Compare YAML');
      fireEvent.click(compareButton);

      await waitFor(() => {
        expect(screen.getByText('2 high risk')).toBeInTheDocument();
      });
    });

    test('renders MEDIUM risk correctly', async () => {
      api.diffYaml.mockResolvedValue({
        differences: {
          values_changed: { "root['spec']['env']": { old_value: 'dev', new_value: 'prod' } },
        },
        summary: { total_changes: 1, values_changed: 1, items_added: 0, items_removed: 0 },
        risk_assessment: [
          { path: 'spec.env', risk: 'MEDIUM', message: 'Environment change' },
        ],
      });

      render(<YamlDiffPanel />);

      const compareButton = screen.getByText('🔍 Compare YAML');
      fireEvent.click(compareButton);

      await waitFor(() => {
        expect(screen.getByText('MEDIUM')).toBeInTheDocument();
      });
    });

    test('renders LOW risk correctly', async () => {
      api.diffYaml.mockResolvedValue({
        differences: {
          values_changed: { "root['metadata']['name']": { old_value: 'old', new_value: 'new' } },
        },
        summary: { total_changes: 1, values_changed: 1, items_added: 0, items_removed: 0 },
        risk_assessment: [
          { path: 'metadata.name', risk: 'LOW', message: 'Name change' },
        ],
      });

      render(<YamlDiffPanel />);

      const compareButton = screen.getByText('🔍 Compare YAML');
      fireEvent.click(compareButton);

      await waitFor(() => {
        expect(screen.getByText('LOW')).toBeInTheDocument();
      });
    });
  });

  describe('Editor Interaction', () => {
    test('updates source YAML when editor A changes', () => {
      render(<YamlDiffPanel />);

      const editors = screen.getAllByTestId('monaco-editor');
      fireEvent.change(editors[0], { target: { value: 'kind: Pod' } });

      expect(editors[0].value).toBe('kind: Pod');
    });

    test('updates target YAML when editor B changes', () => {
      render(<YamlDiffPanel />);

      const editors = screen.getAllByTestId('monaco-editor');
      fireEvent.change(editors[1], { target: { value: 'kind: Service' } });

      expect(editors[1].value).toBe('kind: Service');
    });
  });

  describe('Type Changes', () => {
    test('renders type change correctly', async () => {
      api.diffYaml.mockResolvedValue({
        differences: {
          type_changes: {
            "root['spec']['port']": { old_type: 'str', new_type: 'int', old_value: '80', new_value: 80 },
          },
        },
        summary: { total_changes: 1, values_changed: 0, items_added: 0, items_removed: 0 },
        risk_assessment: [],
      });

      render(<YamlDiffPanel />);

      const compareButton = screen.getByText('🔍 Compare YAML');
      fireEvent.click(compareButton);

      await waitFor(() => {
        expect(screen.getByText('Type Changed')).toBeInTheDocument();
        expect(screen.getByText('str')).toBeInTheDocument();
        expect(screen.getByText('int')).toBeInTheDocument();
      });
    });
  });
});
