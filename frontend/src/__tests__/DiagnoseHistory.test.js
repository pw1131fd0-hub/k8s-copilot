import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import DiagnoseHistory from '../components/DiagnoseHistory';
import * as api from '../utils/api';

// Mock react-markdown
jest.mock('react-markdown', () => {
  return function MockReactMarkdown({ children }) {
    return <div data-testid="markdown">{children}</div>;
  };
});

// Mock the API
jest.mock('../utils/api', () => ({
  fetchDiagnoseHistory: jest.fn(),
  fetchPodDiagnoseHistory: jest.fn(),
}));

describe('DiagnoseHistory Component', () => {
  const mockRecords = [
    {
      id: '1',
      pod_name: 'web-app-pod',
      namespace: 'default',
      error_type: 'CrashLoopBackOff',
      created_at: '2026-03-07T10:00:00Z',
      ai_analysis: JSON.stringify({
        root_cause: 'OOM killed',
        remediation: 'Increase memory limits',
        detailed_analysis: 'Memory usage exceeded limit',
      }),
    },
    {
      id: '2',
      pod_name: 'api-server',
      namespace: 'production',
      error_type: 'ImagePullBackOff',
      created_at: '2026-03-06T15:30:00Z',
      ai_analysis: JSON.stringify({
        root_cause: 'Image not found',
        remediation: 'Check image name and registry',
      }),
    },
  ];

  beforeEach(() => {
    jest.clearAllMocks();
    api.fetchDiagnoseHistory.mockResolvedValue(mockRecords);
  });

  describe('Loading State', () => {
    test('displays loading indicator initially', async () => {
      api.fetchDiagnoseHistory.mockImplementation(
        () => new Promise(() => {}) // Never resolves
      );

      render(<DiagnoseHistory />);

      expect(screen.getByText('Loading history...')).toBeInTheDocument();
    });
  });

  describe('Error State', () => {
    test('displays error message on API failure', async () => {
      api.fetchDiagnoseHistory.mockRejectedValue(new Error('Network error'));

      render(<DiagnoseHistory />);

      await waitFor(() => {
        expect(screen.getByText(/Network error/)).toBeInTheDocument();
      });
    });
  });

  describe('Empty State', () => {
    test('displays empty message when no records', async () => {
      api.fetchDiagnoseHistory.mockResolvedValue([]);

      render(<DiagnoseHistory />);

      await waitFor(() => {
        expect(screen.getByText('No diagnosis records found.')).toBeInTheDocument();
      });
    });
  });

  describe('Records Display', () => {
    test('renders all records as cards', async () => {
      render(<DiagnoseHistory />);

      await waitFor(() => {
        expect(screen.getByText('web-app-pod')).toBeInTheDocument();
        expect(screen.getByText('api-server')).toBeInTheDocument();
      });
    });

    test('shows namespace for each record', async () => {
      render(<DiagnoseHistory />);

      await waitFor(() => {
        expect(screen.getByText('default')).toBeInTheDocument();
        expect(screen.getByText('production')).toBeInTheDocument();
      });
    });

    test('shows error type badge', async () => {
      render(<DiagnoseHistory />);

      await waitFor(() => {
        expect(screen.getByText('CrashLoopBackOff')).toBeInTheDocument();
        expect(screen.getByText('ImagePullBackOff')).toBeInTheDocument();
      });
    });

    test('displays record count', async () => {
      render(<DiagnoseHistory />);

      await waitFor(() => {
        expect(screen.getByText('2 records')).toBeInTheDocument();
      });
    });
  });

  describe('Refresh Button', () => {
    test('calls fetchDiagnoseHistory on refresh click', async () => {
      render(<DiagnoseHistory />);

      await waitFor(() => {
        expect(screen.getByText('web-app-pod')).toBeInTheDocument();
      });

      const refreshButton = screen.getByText('Refresh');
      fireEvent.click(refreshButton);

      await waitFor(() => {
        expect(api.fetchDiagnoseHistory).toHaveBeenCalledTimes(2);
      });
    });
  });

  describe('Detail Panel', () => {
    test('opens detail panel when record card is clicked', async () => {
      render(<DiagnoseHistory />);

      await waitFor(() => {
        expect(screen.getByText('web-app-pod')).toBeInTheDocument();
      });

      const card = screen.getByText('web-app-pod').closest('div[class*="cursor-pointer"]');
      fireEvent.click(card);

      await waitFor(() => {
        expect(screen.getByText('📜 Diagnosis Record')).toBeInTheDocument();
        expect(screen.getByText('OOM killed')).toBeInTheDocument();
      });
    });

    test('closes detail panel when close button is clicked', async () => {
      render(<DiagnoseHistory />);

      await waitFor(() => {
        expect(screen.getByText('web-app-pod')).toBeInTheDocument();
      });

      const card = screen.getByText('web-app-pod').closest('div[class*="cursor-pointer"]');
      fireEvent.click(card);

      await waitFor(() => {
        expect(screen.getByText('📜 Diagnosis Record')).toBeInTheDocument();
      });

      const closeButton = screen.getByLabelText('Close panel');
      fireEvent.click(closeButton);

      await waitFor(() => {
        expect(screen.queryByText('📜 Diagnosis Record')).not.toBeInTheDocument();
      });
    });

    test('displays remediation section in detail panel', async () => {
      render(<DiagnoseHistory />);

      await waitFor(() => {
        expect(screen.getByText('web-app-pod')).toBeInTheDocument();
      });

      const card = screen.getByText('web-app-pod').closest('div[class*="cursor-pointer"]');
      fireEvent.click(card);

      await waitFor(() => {
        expect(screen.getByText('🛠️ Remediation')).toBeInTheDocument();
      });
    });
  });

  describe('Search and Filter', () => {
    test('renders search mode dropdown', async () => {
      render(<DiagnoseHistory />);

      await waitFor(() => {
        expect(screen.getByText('web-app-pod')).toBeInTheDocument();
      });

      expect(screen.getByDisplayValue('All Records')).toBeInTheDocument();
    });

    test('shows pod name input when filter mode is selected', async () => {
      render(<DiagnoseHistory />);

      await waitFor(() => {
        expect(screen.getByText('web-app-pod')).toBeInTheDocument();
      });

      const select = screen.getByDisplayValue('All Records');
      fireEvent.change(select, { target: { value: 'filter' } });

      expect(screen.getByPlaceholderText('Pod name...')).toBeInTheDocument();
    });

    test('filters records by pod name in filter mode', async () => {
      render(<DiagnoseHistory />);

      await waitFor(() => {
        expect(screen.getByText('web-app-pod')).toBeInTheDocument();
        expect(screen.getByText('api-server')).toBeInTheDocument();
      });

      const select = screen.getByDisplayValue('All Records');
      fireEvent.change(select, { target: { value: 'filter' } });

      const input = screen.getByPlaceholderText('Pod name...');
      fireEvent.change(input, { target: { value: 'web' } });

      await waitFor(() => {
        expect(screen.getByText('web-app-pod')).toBeInTheDocument();
        expect(screen.queryByText('api-server')).not.toBeInTheDocument();
      });
    });

    test('searches exact pod match in pod mode', async () => {
      api.fetchPodDiagnoseHistory.mockResolvedValue([mockRecords[0]]);

      render(<DiagnoseHistory />);

      await waitFor(() => {
        expect(screen.getByText('web-app-pod')).toBeInTheDocument();
      });

      const select = screen.getByDisplayValue('All Records');
      fireEvent.change(select, { target: { value: 'pod' } });

      const input = screen.getByPlaceholderText('Pod name...');
      fireEvent.change(input, { target: { value: 'web-app-pod' } });

      const searchButton = screen.getByText('Search');
      fireEvent.click(searchButton);

      await waitFor(() => {
        expect(api.fetchPodDiagnoseHistory).toHaveBeenCalledWith('web-app-pod');
      });
    });
  });

  describe('Parse Analysis', () => {
    test('handles raw analysis string when JSON is invalid', async () => {
      const recordWithInvalidJson = [{
        ...mockRecords[0],
        ai_analysis: 'This is not valid JSON but useful text',
      }];
      api.fetchDiagnoseHistory.mockResolvedValue(recordWithInvalidJson);

      render(<DiagnoseHistory />);

      await waitFor(() => {
        expect(screen.getByText('web-app-pod')).toBeInTheDocument();
      });

      const card = screen.getByText('web-app-pod').closest('div[class*="cursor-pointer"]');
      fireEvent.click(card);

      await waitFor(() => {
        expect(screen.getByText('📄 Raw Output')).toBeInTheDocument();
      });
    });

    test('handles null ai_analysis gracefully', async () => {
      const recordWithNullAnalysis = [{
        ...mockRecords[0],
        ai_analysis: null,
      }];
      api.fetchDiagnoseHistory.mockResolvedValue(recordWithNullAnalysis);

      render(<DiagnoseHistory />);

      await waitFor(() => {
        expect(screen.getByText('web-app-pod')).toBeInTheDocument();
      });

      const card = screen.getByText('web-app-pod').closest('div[class*="cursor-pointer"]');
      fireEvent.click(card);

      await waitFor(() => {
        expect(screen.getByText('No analysis data available.')).toBeInTheDocument();
      });
    });
  });
});
