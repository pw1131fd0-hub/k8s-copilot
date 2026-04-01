import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import ShareModal from '../components/ShareModal';
import * as api from '../utils/api';

jest.mock('../utils/api');

describe('ShareModal', () => {
  const mockOnClose = jest.fn();
  const mockOnShared = jest.fn();
  const mockPostId = 'post-123';

  beforeEach(() => {
    jest.clearAllMocks();
    api.getGroups.mockResolvedValue([
      { id: 'group-1', name: 'Team A', member_count: 3 },
      { id: 'group-2', name: 'Team B', member_count: 5 },
    ]);
  });

  it('renders the share modal', async () => {
    render(
      <ShareModal
        postId={mockPostId}
        onClose={mockOnClose}
        onShared={mockOnShared}
      />
    );

    await waitFor(() => {
      expect(screen.getByText(/Share Post/i)).toBeInTheDocument();
    });
  });

  it('loads groups on mount', async () => {
    render(
      <ShareModal
        postId={mockPostId}
        onClose={mockOnClose}
        onShared={mockOnShared}
      />
    );

    await waitFor(() => {
      expect(api.getGroups).toHaveBeenCalled();
      expect(screen.getByText('Team A')).toBeInTheDocument();
    });
  });

  it('shows error when no recipients selected', async () => {
    render(
      <ShareModal
        postId={mockPostId}
        onClose={mockOnClose}
        onShared={mockOnShared}
      />
    );

    const shareButton = await screen.findByRole('button', { name: /Share/i });
    fireEvent.click(shareButton);

    await waitFor(() => {
      expect(screen.getByText(/Select users or groups/i)).toBeInTheDocument();
    });
  });

  it('calls sharePost API when sharing with emails', async () => {
    api.sharePost.mockResolvedValue([{ id: 'share-1' }]);

    render(
      <ShareModal
        postId={mockPostId}
        onClose={mockOnClose}
        onShared={mockOnShared}
      />
    );

    const emailInput = screen.getByPlaceholderText(/user1@example.com/i);
    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });

    const shareButton = await screen.findByRole('button', { name: /Share/i });
    fireEvent.click(shareButton);

    await waitFor(() => {
      expect(api.sharePost).toHaveBeenCalled();
    });
  });
});
