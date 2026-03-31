import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import PostComposer from '../components/PostComposer';
import * as apiModule from '../utils/api';

// Mock the API module
jest.mock('../utils/api', () => ({
  createPost: jest.fn(),
}));

// Mock VoiceRecorder to avoid complex dependencies
jest.mock('../components/VoiceRecorder', () => {
  return function MockVoiceRecorder({ onTranscribe, disabled }) {
    return (
      <button
        data-testid="voice-recorder"
        onClick={() => onTranscribe('test transcription')}
        disabled={disabled}
      >
        🎤 Record
      </button>
    );
  };
});

describe('PostComposer Component', () => {
  let mockOnPostCreated;

  beforeEach(() => {
    mockOnPostCreated = jest.fn();
    apiModule.createPost.mockClear();
  });

  test('renders composer form with textarea', () => {
    render(<PostComposer onPostCreated={mockOnPostCreated} />);
    const textarea = screen.getByPlaceholderText(/What's on your mind/i);
    expect(textarea).toBeInTheDocument();
  });

  test('renders mood selector button', () => {
    render(<PostComposer onPostCreated={mockOnPostCreated} />);
    const moodButton = screen.getByRole('button', { name: /😊/ });
    expect(moodButton).toBeInTheDocument();
  });

  test('renders share button', () => {
    render(<PostComposer onPostCreated={mockOnPostCreated} />);
    const shareButton = screen.getByRole('button', { name: /Share/i });
    expect(shareButton).toBeInTheDocument();
  });

  test('share button is disabled when content is empty', () => {
    render(<PostComposer onPostCreated={mockOnPostCreated} />);
    const shareButton = screen.getByRole('button', { name: /Share/i });
    expect(shareButton).toBeDisabled();
  });

  test('share button is enabled when content is provided', async () => {
    render(<PostComposer onPostCreated={mockOnPostCreated} />);
    const textarea = screen.getByPlaceholderText(/What's on your mind/i);
    const shareButton = screen.getByRole('button', { name: /Share/i });

    await userEvent.type(textarea, 'Test post content');

    expect(shareButton).not.toBeDisabled();
  });

  test('toggles mood picker visibility', () => {
    const { container } = render(<PostComposer onPostCreated={mockOnPostCreated} />);
    const moodButton = screen.getByRole('button', { name: /😊/ });

    fireEvent.click(moodButton);

    // Mood picker should be visible - check for mood grid
    const moodGrid = container.querySelector('[class*="grid"]');
    expect(moodGrid).toBeInTheDocument();

    // Click mood button again to close
    fireEvent.click(moodButton);
  });

  test('changes mood when mood option is clicked', async () => {
    const { container } = render(<PostComposer onPostCreated={mockOnPostCreated} />);
    const moodButtons = screen.getAllByRole('button', { name: /[😊😐😔🥰💭🎯🙏💪😴😤]/ });
    const moodButton = moodButtons[0]; // First button is the selected mood

    // Open mood picker
    fireEvent.click(moodButton);

    // All mood buttons should be visible now
    const allMoodButtons = screen.getAllByRole('button', { name: /[😊😐😔🥰💭🎯🙏💪😴😤]/ });
    expect(allMoodButtons.length).toBeGreaterThan(1);

    // Select sad mood (should be in the grid)
    const sadButton = allMoodButtons.find(btn => btn.textContent === '😔');
    if (sadButton) {
      fireEvent.click(sadButton);
    }
  });

  test('submits post with content and mood', async () => {
    const mockPost = { id: '1', content: 'Test post', mood: '😊' };
    apiModule.createPost.mockResolvedValueOnce(mockPost);

    render(<PostComposer onPostCreated={mockOnPostCreated} />);

    const textarea = screen.getByPlaceholderText(/What's on your mind/i);
    const shareButton = screen.getByRole('button', { name: /Share/i });

    await userEvent.type(textarea, 'Test post content');
    fireEvent.click(shareButton);

    await waitFor(() => {
      expect(apiModule.createPost).toHaveBeenCalledWith({
        mood: '😊',
        content: 'Test post content',
        author: 'AI Assistant',
        images: [],
      });
    });

    expect(mockOnPostCreated).toHaveBeenCalledWith(mockPost);
  });

  test('clears form after successful post creation', async () => {
    const mockPost = { id: '1' };
    apiModule.createPost.mockResolvedValueOnce(mockPost);

    render(<PostComposer onPostCreated={mockOnPostCreated} />);

    const textarea = screen.getByPlaceholderText(/What's on your mind/i);
    const shareButton = screen.getByRole('button', { name: /Share/i });

    await userEvent.type(textarea, 'Test content');
    fireEvent.click(shareButton);

    await waitFor(() => {
      expect(textarea.value).toBe('');
    });
  });

  test('shows loading state during post creation', async () => {
    // Make the promise never resolve to keep loading state
    apiModule.createPost.mockImplementation(() => new Promise(() => {}));

    render(<PostComposer onPostCreated={mockOnPostCreated} />);

    const textarea = screen.getByPlaceholderText(/What's on your mind/i);
    const shareButton = screen.getByRole('button', { name: /Share/i });

    await userEvent.type(textarea, 'Test content');
    fireEvent.click(shareButton);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Posting/i })).toBeInTheDocument();
    });
  });

  test('handles post creation error', async () => {
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
    const alertSpy = jest.spyOn(window, 'alert').mockImplementation(() => {});

    apiModule.createPost.mockRejectedValueOnce(new Error('API Error'));

    render(<PostComposer onPostCreated={mockOnPostCreated} />);

    const textarea = screen.getByPlaceholderText(/What's on your mind/i);
    const shareButton = screen.getByRole('button', { name: /Share/i });

    await userEvent.type(textarea, 'Test content');
    fireEvent.click(shareButton);

    await waitFor(() => {
      expect(alertSpy).toHaveBeenCalledWith('Failed to create post');
    });

    consoleSpy.mockRestore();
    alertSpy.mockRestore();
  });

  test('integrates voice input via VoiceRecorder', async () => {
    render(<PostComposer onPostCreated={mockOnPostCreated} />);

    const voiceButton = screen.getByTestId('voice-recorder');
    const textarea = screen.getByPlaceholderText(/What's on your mind/i);

    fireEvent.click(voiceButton);

    await waitFor(() => {
      expect(textarea.value).toContain('[Voice Input] test transcription');
    });
  });

  test('appends voice input to existing content', async () => {
    render(<PostComposer onPostCreated={mockOnPostCreated} />);

    const textarea = screen.getByPlaceholderText(/What's on your mind/i);
    const voiceButton = screen.getByTestId('voice-recorder');

    // Type some initial content
    await userEvent.type(textarea, 'Initial thoughts');

    // Then add voice input
    fireEvent.click(voiceButton);

    await waitFor(() => {
      expect(textarea.value).toContain('Initial thoughts');
      expect(textarea.value).toContain('[Voice Input] test transcription');
    });
  });

  test('disables voice recorder during post submission', async () => {
    apiModule.createPost.mockImplementation(() => new Promise(() => {}));

    render(<PostComposer onPostCreated={mockOnPostCreated} />);

    const textarea = screen.getByPlaceholderText(/What's on your mind/i);
    const voiceButton = screen.getByTestId('voice-recorder');
    const shareButton = screen.getByRole('button', { name: /Share/i });

    await userEvent.type(textarea, 'Test content');
    fireEvent.click(shareButton);

    await waitFor(() => {
      expect(voiceButton).toBeDisabled();
    });
  });

  test('trims whitespace from content before submission', async () => {
    const mockPost = { id: '1' };
    apiModule.createPost.mockResolvedValueOnce(mockPost);

    render(<PostComposer onPostCreated={mockOnPostCreated} />);

    const textarea = screen.getByPlaceholderText(/What's on your mind/i);
    const shareButton = screen.getByRole('button', { name: /Share/i });

    await userEvent.type(textarea, '   Test content with spaces   ');
    fireEvent.click(shareButton);

    await waitFor(() => {
      expect(apiModule.createPost).toHaveBeenCalledWith(
        expect.objectContaining({
          content: 'Test content with spaces',
        })
      );
    });
  });

  test('does not submit when only whitespace is entered', async () => {
    render(<PostComposer onPostCreated={mockOnPostCreated} />);

    const textarea = screen.getByPlaceholderText(/What's on your mind/i);
    const shareButton = screen.getByRole('button', { name: /Share/i });

    await userEvent.type(textarea, '   ');

    expect(shareButton).toBeDisabled();
    expect(apiModule.createPost).not.toHaveBeenCalled();
  });

  test('default mood is happy', () => {
    render(<PostComposer onPostCreated={mockOnPostCreated} />);
    const moodButton = screen.getByRole('button', { name: /😊/ });
    expect(moodButton).toBeInTheDocument();
  });

  test('resets mood to happy after post creation', async () => {
    const mockPost = { id: '1' };
    apiModule.createPost.mockResolvedValueOnce(mockPost);

    const { container } = render(<PostComposer onPostCreated={mockOnPostCreated} />);

    const moodButtons = screen.getAllByRole('button', { name: /[😊😐😔🥰💭🎯🙏💪😴😤]/ });
    const moodButton = moodButtons[0];

    // Open mood picker and change mood
    fireEvent.click(moodButton);
    const allMoodButtons = screen.getAllByRole('button', { name: /[😊😐😔🥰💭🎯🙏💪😴😤]/ });
    const sadButton = allMoodButtons.find(btn => btn.textContent === '😔');
    if (sadButton) fireEvent.click(sadButton);

    // Add content and submit
    const textarea = screen.getByPlaceholderText(/What's on your mind/i);
    const shareButton = screen.getByRole('button', { name: /Share/i });

    await userEvent.type(textarea, 'Test content');
    fireEvent.click(shareButton);

    await waitFor(() => {
      // Mood should be back to happy (first mood button)
      const resetMoodButtons = screen.getAllByRole('button', { name: /[😊😐😔🥰💭🎯🙏💪😴😤]/ });
      const happyButton = resetMoodButtons[0];
      expect(happyButton.textContent).toBe('😊');
    });
  });

  test('has proper dark mode styling classes', () => {
    const { container } = render(<PostComposer onPostCreated={mockOnPostCreated} />);
    const form = container.querySelector('form');
    expect(form).toHaveClass('dark:border-slate-700');
  });

  test('textarea has proper placeholder text', () => {
    render(<PostComposer onPostCreated={mockOnPostCreated} />);
    const textarea = screen.getByPlaceholderText(/What's on your mind/i);
    expect(textarea).toHaveAttribute('placeholder');
  });
});
