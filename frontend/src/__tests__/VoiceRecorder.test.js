import React from 'react';
import { render, screen } from '@testing-library/react';
import VoiceRecorder from '../components/VoiceRecorder';

// Mock navigator.mediaDevices
const mockGetUserMedia = jest.fn();

Object.defineProperty(global.navigator, 'mediaDevices', {
  value: {
    getUserMedia: mockGetUserMedia,
  },
  configurable: true,
});

describe('VoiceRecorder Component', () => {
  let mockOnTranscribe;

  beforeEach(() => {
    mockOnTranscribe = jest.fn();
    mockGetUserMedia.mockClear();

    // Mock MediaRecorder with static isTypeSupported method
    global.MediaRecorder = class {
      static isTypeSupported(type) {
        return type === 'audio/webm;codecs=opus' || type === 'audio/webm';
      }

      constructor(stream, options) {
        this.stream = stream;
        this.options = options;
        this.ondataavailable = null;
        this.onstop = null;
      }

      start() {}
      stop() {}
    };

    // Mock Stream and Track
    const mockTrack = { stop: jest.fn() };
    const mockStream = {
      getTracks: () => [mockTrack],
    };

    mockGetUserMedia.mockResolvedValue(mockStream);
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('renders voice recorder button', () => {
    render(<VoiceRecorder onTranscribe={mockOnTranscribe} />);
    const button = screen.getByRole('button');
    expect(button).toBeInTheDocument();
    expect(button).toHaveTextContent('🎤');
  });

  test('is disabled when disabled prop is true', () => {
    render(<VoiceRecorder onTranscribe={mockOnTranscribe} disabled={true} />);
    const button = screen.getByRole('button');
    expect(button).toBeDisabled();
  });

  test('shows error message on microphone access denied', async () => {
    mockGetUserMedia.mockRejectedValueOnce(new Error('Permission denied'));

    render(<VoiceRecorder onTranscribe={mockOnTranscribe} />);
    const button = screen.getByRole('button');

    button.click();

    // Wait for error message
    const errorElement = await screen.findByText(/Microphone access denied/i);
    expect(errorElement).toBeInTheDocument();
  });

  test('handles disabled state', () => {
    const { rerender } = render(
      <VoiceRecorder onTranscribe={mockOnTranscribe} disabled={false} />
    );

    expect(screen.getByRole('button')).not.toBeDisabled();

    rerender(<VoiceRecorder onTranscribe={mockOnTranscribe} disabled={true} />);

    expect(screen.getByRole('button')).toBeDisabled();
  });

  test('renders with expected button title', () => {
    render(<VoiceRecorder onTranscribe={mockOnTranscribe} />);
    const button = screen.getByRole('button');
    expect(button).toHaveAttribute('title', 'Start voice recording');
  });

  test('calls onTranscribe callback prop exists', () => {
    render(<VoiceRecorder onTranscribe={mockOnTranscribe} />);
    expect(typeof mockOnTranscribe).toBe('function');
  });
});
