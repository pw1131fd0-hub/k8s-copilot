import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import CommentThread from '../components/CommentThread';
import * as api from '../utils/api';

jest.mock('../utils/api');

describe('CommentThread', () => {
  const mockPostId = 'post-123';
  const mockOnCommentAdded = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    api.getCollaborationComments.mockResolvedValue([
      {
        id: 'comment-1',
        content: 'Great post!',
        author_id: 'user-1',
        is_suggestion: false,
        status: null,
      },
      {
        id: 'comment-2',
        content: 'Consider this...',
        author_id: 'user-2',
        is_suggestion: true,
        status: 'pending',
      },
    ]);
  });

  it('renders the comment thread', async () => {
    render(
      <CommentThread
        postId={mockPostId}
        onCommentAdded={mockOnCommentAdded}
      />
    );

    await waitFor(() => {
      expect(screen.getByText(/Collaboration Comments/i)).toBeInTheDocument();
    });
  });

  it('loads comments on mount', async () => {
    render(
      <CommentThread
        postId={mockPostId}
        onCommentAdded={mockOnCommentAdded}
      />
    );

    await waitFor(() => {
      expect(api.getCollaborationComments).toHaveBeenCalledWith(mockPostId);
      expect(screen.getByText('Great post!')).toBeInTheDocument();
    });
  });

  it('displays suggestion indicator for suggestions', async () => {
    render(
      <CommentThread
        postId={mockPostId}
        onCommentAdded={mockOnCommentAdded}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Suggestion')).toBeInTheDocument();
    });
  });

  it('allows adding new comments', async () => {
    api.addCollaborationComment.mockResolvedValue({
      id: 'comment-3',
      content: 'New comment',
      author_id: 'user-1',
      is_suggestion: false,
      status: null,
    });

    render(
      <CommentThread
        postId={mockPostId}
        onCommentAdded={mockOnCommentAdded}
      />
    );

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/Add a comment/i)).toBeInTheDocument();
    });

    const textarea = screen.getByPlaceholderText(/Add a comment/i);
    fireEvent.change(textarea, { target: { value: 'New comment' } });

    const postButton = screen.getByRole('button', { name: /Post Comment/i });
    fireEvent.click(postButton);

    await waitFor(() => {
      expect(api.addCollaborationComment).toHaveBeenCalled();
    });
  });
});
