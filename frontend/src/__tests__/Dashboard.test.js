import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import Dashboard from '../pages/Dashboard';
import * as api from '../utils/api';

// Mock react-markdown
jest.mock('react-markdown', () => {
  return function MockReactMarkdown({ children }) {
    return <div data-testid="markdown">{children}</div>;
  };
});

// Mock the API
jest.mock('../utils/api', () => ({
  fetchPods: jest.fn(),
  fetchClusterStatus: jest.fn(),
  diagnosePod: jest.fn(),
  scanYaml: jest.fn(),
  diffYaml: jest.fn(),
  fetchDiagnoseHistory: jest.fn(),
  fetchPodDiagnoseHistory: jest.fn(),
}));

// Mock Monaco Editor
jest.mock('@monaco-editor/react', () => {
  return function MockEditor({ value, onChange }) {
    return (
      <textarea
        data-testid="monaco-editor"
        value={value}
        onChange={(e) => onChange && onChange(e.target.value)}
      />
    );
  };
});

describe('Dashboard Component', () => {
  const mockPods = [
    { name: 'app-pod', namespace: 'default', status: 'Running', ip: '10.0.0.1' },
    { name: 'db-pod', namespace: 'default', status: 'Pending', ip: null },
  ];

  const mockClusterStatus = {
    status: 'connected',
    version: '1.28.0',
  };

  beforeEach(() => {
    jest.clearAllMocks();
    api.fetchPods.mockResolvedValue({ pods: mockPods });
    api.fetchClusterStatus.mockResolvedValue(mockClusterStatus);
    api.fetchDiagnoseHistory.mockResolvedValue([]);
  });

  describe('Header', () => {
    test('renders app title', async () => {
      render(<Dashboard />);

      expect(screen.getByText('Lobster K8s Copilot')).toBeInTheDocument();
    });

    test('renders lobster emoji', async () => {
      render(<Dashboard />);

      expect(screen.getByText('🦞')).toBeInTheDocument();
    });

    test('shows connected status when cluster is connected', async () => {
      render(<Dashboard />);

      await waitFor(() => {
        expect(screen.getByText('Connected')).toBeInTheDocument();
      });
    });

    test('shows disconnected status when cluster is disconnected', async () => {
      api.fetchClusterStatus.mockResolvedValue({ status: 'disconnected' });

      render(<Dashboard />);

      await waitFor(() => {
        expect(screen.getByText('Disconnected')).toBeInTheDocument();
      });
    });

    test('refresh button triggers data reload', async () => {
      render(<Dashboard />);

      await waitFor(() => {
        expect(screen.getByText('app-pod')).toBeInTheDocument();
      });

      const refreshButton = screen.getByText('Refresh');
      fireEvent.click(refreshButton);

      await waitFor(() => {
        expect(api.fetchPods).toHaveBeenCalledTimes(2);
      });
    });
  });

  describe('Stats Bar', () => {
    test('shows total pods count', async () => {
      render(<Dashboard />);

      await waitFor(() => {
        expect(screen.getByText('2')).toBeInTheDocument();
        expect(screen.getByText('Total Pods')).toBeInTheDocument();
      });
    });

    test('shows healthy pods count', async () => {
      render(<Dashboard />);

      await waitFor(() => {
        expect(screen.getByText('Healthy')).toBeInTheDocument();
        // Check Running / Succeeded subtitle instead of the specific count
        expect(screen.getByText('Running / Succeeded')).toBeInTheDocument();
      });
    });

    test('shows unhealthy pods count when present', async () => {
      render(<Dashboard />);

      await waitFor(() => {
        expect(screen.getByText('Unhealthy')).toBeInTheDocument();
      });
    });

    test('shows K8s version', async () => {
      render(<Dashboard />);

      await waitFor(() => {
        expect(screen.getByText('1.28.0')).toBeInTheDocument();
        expect(screen.getByText('K8s Version')).toBeInTheDocument();
      });
    });
  });

  describe('Tabs Navigation', () => {
    test('renders all tabs', async () => {
      render(<Dashboard />);

      expect(screen.getByText('Cluster Overview')).toBeInTheDocument();
      expect(screen.getByText('YAML Editor')).toBeInTheDocument();
      expect(screen.getByText('YAML Diff')).toBeInTheDocument();
      expect(screen.getByText('Diagnose History')).toBeInTheDocument();
    });

    test('shows PodList on Cluster Overview tab', async () => {
      render(<Dashboard />);

      await waitFor(() => {
        expect(screen.getByText('app-pod')).toBeInTheDocument();
      });
    });

    test('switches to YAML Editor tab', async () => {
      render(<Dashboard />);

      fireEvent.click(screen.getByText('YAML Editor'));

      await waitFor(() => {
        expect(screen.getByText('📝 YAML Editor')).toBeInTheDocument();
      });
    });

    test('switches to YAML Diff tab', async () => {
      render(<Dashboard />);

      fireEvent.click(screen.getByText('YAML Diff'));

      await waitFor(() => {
        expect(screen.getByText('📊 YAML Diff')).toBeInTheDocument();
      });
    });

    test('switches to Diagnose History tab', async () => {
      render(<Dashboard />);

      fireEvent.click(screen.getByText('Diagnose History'));

      await waitFor(() => {
        expect(screen.getByText('📜 Diagnose History')).toBeInTheDocument();
      });
    });
  });

  describe('DiagnosePanel Integration', () => {
    test('shows diagnose panel when diagnosis result is received', async () => {
      api.diagnosePod.mockResolvedValue({
        pod_name: 'app-pod',
        root_cause: 'Test diagnosis result',
      });

      render(<Dashboard />);

      await waitFor(() => {
        expect(screen.getByText('app-pod')).toBeInTheDocument();
      });

      const diagnoseButtons = screen.getAllByRole('button', { name: 'Diagnose' });
      fireEvent.click(diagnoseButtons[0]);

      await waitFor(() => {
        expect(screen.getByText('🦞 Lobster Diagnosis Report')).toBeInTheDocument();
        expect(screen.getByText('Test diagnosis result')).toBeInTheDocument();
      });
    });

    test('closes diagnose panel when close button is clicked', async () => {
      api.diagnosePod.mockResolvedValue({
        pod_name: 'app-pod',
        root_cause: 'Test diagnosis',
      });

      render(<Dashboard />);

      await waitFor(() => {
        expect(screen.getByText('app-pod')).toBeInTheDocument();
      });

      const diagnoseButtons = screen.getAllByRole('button', { name: 'Diagnose' });
      fireEvent.click(diagnoseButtons[0]);

      await waitFor(() => {
        expect(screen.getByText('🦞 Lobster Diagnosis Report')).toBeInTheDocument();
      });

      const closeButton = screen.getByLabelText('Close panel');
      fireEvent.click(closeButton);

      await waitFor(() => {
        expect(screen.queryByText('🦞 Lobster Diagnosis Report')).not.toBeInTheDocument();
      });
    });
  });

  describe('Loading State', () => {
    test('shows loading state initially', async () => {
      api.fetchPods.mockImplementation(() => new Promise(() => {}));

      render(<Dashboard />);

      expect(screen.getByText('Loading pods...')).toBeInTheDocument();
    });
  });

  describe('Error State', () => {
    test('shows error message on API failure', async () => {
      api.fetchPods.mockRejectedValue(new Error('API unavailable'));

      render(<Dashboard />);

      await waitFor(() => {
        expect(screen.getByText(/API unavailable/)).toBeInTheDocument();
      });
    });
  });

  describe('Empty State', () => {
    test('shows no pods message when pods array is empty', async () => {
      api.fetchPods.mockResolvedValue({ pods: [] });

      render(<Dashboard />);

      await waitFor(() => {
        expect(screen.getByText('No pods to display.')).toBeInTheDocument();
      });
    });

    test('does not show stats bar when no pods', async () => {
      api.fetchPods.mockResolvedValue({ pods: [] });

      render(<Dashboard />);

      await waitFor(() => {
        expect(screen.queryByText('Total Pods')).not.toBeInTheDocument();
      });
    });
  });

  describe('Stats Bar Visibility', () => {
    test('stats bar only visible on Cluster Overview tab', async () => {
      render(<Dashboard />);

      await waitFor(() => {
        expect(screen.getByText('Total Pods')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('YAML Editor'));

      await waitFor(() => {
        expect(screen.queryByText('Total Pods')).not.toBeInTheDocument();
      });
    });
  });
});
