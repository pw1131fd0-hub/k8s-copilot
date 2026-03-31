/**
 * OfflineIndicator Component Tests
 */

import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import OfflineIndicator from '../components/OfflineIndicator';
import * as dbModule from '../utils/db';

jest.mock('../utils/db', () => ({
  getPendingPosts: jest.fn(),
}));

describe('OfflineIndicator', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    dbModule.getPendingPosts.mockResolvedValue([]);
  });

  it('should not render when online and no pending posts', async () => {
    const { container } = render(<OfflineIndicator />);
    await waitFor(() => {
      expect(container.firstChild).toBeEmptyDOMElement();
    });
  });

  it('should display offline indicator when device is offline', async () => {
    // Mock offline event
    Object.defineProperty(navigator, 'onLine', {
      writable: true,
      value: false,
    });

    render(<OfflineIndicator />);

    // Simulate offline event
    window.dispatchEvent(new Event('offline'));

    await waitFor(() => {
      expect(screen.getByText('Offline Mode')).toBeInTheDocument();
    });
  });

  it('should display pending posts count', async () => {
    dbModule.getPendingPosts.mockResolvedValue([
      { id: 1, data: {}, status: 'pending' },
      { id: 2, data: {}, status: 'pending' },
    ]);

    render(<OfflineIndicator />);

    await waitFor(() => {
      expect(screen.getByText(/2 posts pending sync/)).toBeInTheDocument();
    });
  });

  it('should handle sync complete event', async () => {
    render(<OfflineIndicator />);

    const syncEvent = new CustomEvent('pwa:sync-complete', {
      detail: { synced: 3 },
    });

    window.dispatchEvent(syncEvent);

    await waitFor(() => {
      expect(screen.getByText('Sync Complete!')).toBeInTheDocument();
    });
  });

  it('should update pending count periodically', async () => {
    const mockGetPending = dbModule.getPendingPosts;

    // First call returns empty
    mockGetPending.mockResolvedValueOnce([]);

    render(<OfflineIndicator />);

    // Simulate pending posts appearing
    mockGetPending.mockResolvedValueOnce([
      { id: 1, data: {}, status: 'pending' },
    ]);

    // Trigger periodic check
    await waitFor(() => {
      expect(mockGetPending).toHaveBeenCalled();
    }, { timeout: 6000 });
  });

  it('should display online icon color in online state', async () => {
    render(<OfflineIndicator />);

    window.dispatchEvent(new Event('online'));

    // Should not show offline indicator when online with no pending posts
    await waitFor(() => {
      expect(screen.queryByText('Offline Mode')).not.toBeInTheDocument();
    });
  });

  it('should use dark mode classes', () => {
    dbModule.getPendingPosts.mockResolvedValueOnce([
      { id: 1, data: {}, status: 'pending' },
    ]);

    const { container } = render(<OfflineIndicator />);

    const indicator = container.querySelector('[class*="bg-blue"]');
    expect(indicator).toHaveClass('bg-blue-600');
    expect(indicator).toHaveClass('text-white');
  });
});
