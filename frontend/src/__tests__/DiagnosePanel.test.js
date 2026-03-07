import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import DiagnosePanel from '../components/DiagnosePanel';

// Mock react-markdown
jest.mock('react-markdown', () => {
  return function MockReactMarkdown({ children }) {
    return <div data-testid="markdown">{children}</div>;
  };
});

describe('DiagnosePanel Component', () => {
  const mockOnClose = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Null Result', () => {
    test('returns null when result is null', () => {
      const { container } = render(<DiagnosePanel result={null} onClose={mockOnClose} />);
      expect(container.firstChild).toBeNull();
    });

    test('returns null when result is undefined', () => {
      const { container } = render(<DiagnosePanel result={undefined} onClose={mockOnClose} />);
      expect(container.firstChild).toBeNull();
    });
  });

  describe('Error State', () => {
    test('displays error message when result has error', () => {
      const result = { error: 'API connection failed' };
      render(<DiagnosePanel result={result} onClose={mockOnClose} />);

      expect(screen.getByText(/API connection failed/)).toBeInTheDocument();
    });

    test('shows warning icon for error state', () => {
      const result = { error: 'Some error' };
      render(<DiagnosePanel result={result} onClose={mockOnClose} />);

      expect(screen.getByText(/⚠️/)).toBeInTheDocument();
    });
  });

  describe('Success State', () => {
    const successResult = {
      pod_name: 'test-pod',
      error_type: 'CrashLoopBackOff',
      root_cause: 'Database connection timeout',
      raw_analysis: '## Analysis\n\nThe pod failed due to DB timeout.',
      remediation: '1. Check database connectivity\n2. Increase timeout',
      model_used: 'openai/gpt-4o',
    };

    test('displays pod name in header', () => {
      render(<DiagnosePanel result={successResult} onClose={mockOnClose} />);
      expect(screen.getByText('test-pod')).toBeInTheDocument();
    });

    test('displays error type badge', () => {
      render(<DiagnosePanel result={successResult} onClose={mockOnClose} />);
      expect(screen.getByText('CrashLoopBackOff')).toBeInTheDocument();
    });

    test('displays root cause section', () => {
      render(<DiagnosePanel result={successResult} onClose={mockOnClose} />);
      expect(screen.getByText('🔍 Root Cause')).toBeInTheDocument();
      expect(screen.getByText('Database connection timeout')).toBeInTheDocument();
    });

    test('displays analysis section', () => {
      render(<DiagnosePanel result={successResult} onClose={mockOnClose} />);
      expect(screen.getByText('📋 Analysis')).toBeInTheDocument();
    });

    test('displays remediation section', () => {
      render(<DiagnosePanel result={successResult} onClose={mockOnClose} />);
      expect(screen.getByText('🛠️ Remediation')).toBeInTheDocument();
    });

    test('displays model used footer', () => {
      render(<DiagnosePanel result={successResult} onClose={mockOnClose} />);
      expect(screen.getByText('openai/gpt-4o')).toBeInTheDocument();
    });

    test('displays header title', () => {
      render(<DiagnosePanel result={successResult} onClose={mockOnClose} />);
      expect(screen.getByText('🦞 Lobster Diagnosis Report')).toBeInTheDocument();
    });
  });

  describe('Close Button', () => {
    test('calls onClose when close button is clicked', () => {
      const result = { root_cause: 'Test' };
      render(<DiagnosePanel result={result} onClose={mockOnClose} />);

      const closeButton = screen.getByLabelText('Close panel');
      fireEvent.click(closeButton);

      expect(mockOnClose).toHaveBeenCalledTimes(1);
    });
  });

  describe('Partial Results', () => {
    test('handles missing optional fields gracefully', () => {
      const partialResult = {
        root_cause: 'Something went wrong',
      };
      render(<DiagnosePanel result={partialResult} onClose={mockOnClose} />);

      expect(screen.getByText('Something went wrong')).toBeInTheDocument();
      // These sections should not appear
      expect(screen.queryByText('📋 Analysis')).not.toBeInTheDocument();
      expect(screen.queryByText('🛠️ Remediation')).not.toBeInTheDocument();
    });

    test('does not show error type when not present', () => {
      const result = { root_cause: 'Issue found' };
      render(<DiagnosePanel result={result} onClose={mockOnClose} />);

      expect(screen.queryByText('Error Type:')).not.toBeInTheDocument();
    });

    test('does not show model used when not present', () => {
      const result = { root_cause: 'Issue found' };
      render(<DiagnosePanel result={result} onClose={mockOnClose} />);

      expect(screen.queryByText('Analyzed by:')).not.toBeInTheDocument();
    });
  });
});
