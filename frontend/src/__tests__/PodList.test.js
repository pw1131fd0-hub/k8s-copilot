import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import PodList from '../components/PodList';
import * as api from '../utils/api';

// Mock the API
jest.mock('../utils/api', () => ({
  diagnosePod: jest.fn(),
}));

describe('PodList Component', () => {
  const mockPods = [
    { name: 'running-pod', namespace: 'default', status: 'Running', ip: '10.0.0.1' },
    { name: 'pending-pod', namespace: 'default', status: 'Pending', ip: null },
    { name: 'failed-pod', namespace: 'kube-system', status: 'Failed', ip: '10.0.0.3' },
  ];

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Loading State', () => {
    test('displays loading spinner when loading is true', () => {
      render(<PodList pods={[]} loading={true} error={null} />);

      expect(screen.getByText('Loading pods...')).toBeInTheDocument();
    });
  });

  describe('Error State', () => {
    test('displays error message when error is provided', () => {
      render(<PodList pods={[]} loading={false} error="Failed to fetch pods" />);

      expect(screen.getByText(/Failed to fetch pods/)).toBeInTheDocument();
    });
  });

  describe('Empty State', () => {
    test('displays "No pods to display" when pods array is empty', () => {
      render(<PodList pods={[]} loading={false} error={null} />);

      expect(screen.getByText('No pods to display.')).toBeInTheDocument();
    });
  });

  describe('Pod List Display', () => {
    test('renders all pods in the table', () => {
      render(<PodList pods={mockPods} loading={false} error={null} />);

      // Pods may appear multiple times (in unhealthy and all pods sections)
      expect(screen.getAllByText('running-pod')).toHaveLength(1);
      expect(screen.getAllByText('pending-pod')).toHaveLength(2); // unhealthy + all
      expect(screen.getAllByText('failed-pod')).toHaveLength(2); // unhealthy + all
    });

    test('displays correct status badges', () => {
      render(<PodList pods={mockPods} loading={false} error={null} />);

      // Running pod appears once (only in All Pods)
      expect(screen.getAllByText('Running')).toHaveLength(1);
      // Pending and Failed appear twice (in Unhealthy and All Pods sections)
      expect(screen.getAllByText('Pending')).toHaveLength(2);
      expect(screen.getAllByText('Failed')).toHaveLength(2);
    });

    test('shows unhealthy pods section when unhealthy pods exist', () => {
      render(<PodList pods={mockPods} loading={false} error={null} />);

      expect(screen.getByText(/Unhealthy Pods/)).toBeInTheDocument();
      expect(screen.getByText(/\(2\)/)).toBeInTheDocument();
    });

    test('shows IP address for pods with IP', () => {
      render(<PodList pods={mockPods} loading={false} error={null} />);

      expect(screen.getAllByText('10.0.0.1')[0]).toBeInTheDocument();
    });

    test('shows dash for pods without IP', () => {
      render(<PodList pods={mockPods} loading={false} error={null} />);

      const dashElements = screen.getAllByText('—');
      expect(dashElements.length).toBeGreaterThan(0);
    });
  });

  describe('Diagnose Button', () => {
    test('renders diagnose button for each pod', () => {
      render(<PodList pods={mockPods} loading={false} error={null} />);

      const diagnoseButtons = screen.getAllByRole('button', { name: /Diagnose/i });
      // Each pod appears in both "All Pods" section, and unhealthy ones also in "Unhealthy Pods"
      expect(diagnoseButtons.length).toBeGreaterThanOrEqual(3);
    });

    test('calls diagnosePod API when button is clicked', async () => {
      const mockDiagnoseResult = jest.fn();
      api.diagnosePod.mockResolvedValueOnce({
        pod_name: 'running-pod',
        root_cause: 'Test cause',
      });

      render(
        <PodList
          pods={[mockPods[0]]}
          loading={false}
          error={null}
          onDiagnoseResult={mockDiagnoseResult}
        />
      );

      const diagnoseButton = screen.getByRole('button', { name: 'Diagnose' });
      fireEvent.click(diagnoseButton);

      await waitFor(() => {
        expect(api.diagnosePod).toHaveBeenCalledWith('running-pod', 'default');
      });

      await waitFor(() => {
        expect(mockDiagnoseResult).toHaveBeenCalledWith({
          pod_name: 'running-pod',
          root_cause: 'Test cause',
        });
      });
    });

    test('handles API errors gracefully', async () => {
      const mockDiagnoseResult = jest.fn();
      api.diagnosePod.mockRejectedValueOnce(new Error('Network error'));

      render(
        <PodList
          pods={[mockPods[0]]}
          loading={false}
          error={null}
          onDiagnoseResult={mockDiagnoseResult}
        />
      );

      const diagnoseButton = screen.getByRole('button', { name: 'Diagnose' });
      fireEvent.click(diagnoseButton);

      await waitFor(() => {
        expect(mockDiagnoseResult).toHaveBeenCalledWith({
          error: 'Network error',
          pod_name: 'running-pod',
        });
      });
    });

    test('disables button while diagnosing', async () => {
      api.diagnosePod.mockImplementation(
        () => new Promise((resolve) => setTimeout(resolve, 1000))
      );

      render(<PodList pods={[mockPods[0]]} loading={false} error={null} />);

      const diagnoseButton = screen.getByRole('button', { name: 'Diagnose' });
      fireEvent.click(diagnoseButton);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: 'Diagnosing…' })).toBeDisabled();
      });
    });
  });

  describe('Status Badge', () => {
    test('renders Unknown status for unrecognized status', () => {
      const podsWithUnknown = [
        { name: 'unknown-pod', namespace: 'default', status: 'SomeWeirdStatus', ip: null },
      ];

      render(<PodList pods={podsWithUnknown} loading={false} error={null} />);

      // The Unknown status badge appears in the table
      const unknownBadges = screen.getAllByText('Unknown');
      expect(unknownBadges.length).toBeGreaterThan(0);
    });

    test('renders Succeeded status correctly', () => {
      const podsWithSucceeded = [
        { name: 'job-pod', namespace: 'default', status: 'Succeeded', ip: null },
      ];

      render(<PodList pods={podsWithSucceeded} loading={false} error={null} />);

      const succeededBadges = screen.getAllByText('Succeeded');
      expect(succeededBadges.length).toBeGreaterThan(0);
    });
  });
});
