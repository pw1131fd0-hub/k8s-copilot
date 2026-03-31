import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import ExportModal from '../components/ExportModal';

describe('ExportModal', () => {
  it('should not render when isOpen is false', () => {
    const { container } = render(
      <ExportModal isOpen={false} onClose={() => {}} />
    );
    expect(container.firstChild).toBeNull();
  });

  it('should render when isOpen is true', () => {
    render(<ExportModal isOpen={true} onClose={() => {}} />);
    expect(screen.getByText(/Export Journal/i)).toBeInTheDocument();
  });

  it('should have export format options', () => {
    render(<ExportModal isOpen={true} onClose={() => {}} />);
    const formatOptions = screen.getByText(/Export Format/i);
    expect(formatOptions).toBeInTheDocument();
  });

  it('should have date input labels', () => {
    render(<ExportModal isOpen={true} onClose={() => {}} />);
    expect(screen.getByText(/Start Date/i)).toBeInTheDocument();
    expect(screen.getByText(/End Date/i)).toBeInTheDocument();
  });

  it('should call onClose when cancel button is clicked', () => {
    const onClose = jest.fn();
    render(<ExportModal isOpen={true} onClose={onClose} />);
    fireEvent.click(screen.getByText('Cancel'));
    expect(onClose).toHaveBeenCalled();
  });

  it('should have export button', () => {
    render(<ExportModal isOpen={true} onClose={() => {}} />);
    const exportButton = screen.getByRole('button', { name: /Export/i });
    expect(exportButton).toBeInTheDocument();
  });

  it('should have CSV option in format select', () => {
    render(<ExportModal isOpen={true} onClose={() => {}} />);
    const csvOption = screen.getByText(/for spreadsheets/i);
    expect(csvOption).toBeInTheDocument();
  });

  it('should have Markdown option in format select', () => {
    render(<ExportModal isOpen={true} onClose={() => {}} />);
    const markdownOption = screen.getByText(/for reading/i);
    expect(markdownOption).toBeInTheDocument();
  });
});
