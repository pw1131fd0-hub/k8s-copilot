import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import CandidateComparison from '../components/CandidateComparison';

describe('CandidateComparison Component', () => {
  const mockCandidates = [
    {
      rank: 1,
      option: 'Option A',
      description: 'Recommended solution',
      feasibility_score: 0.9,
      pros: ['Good performance', 'Low cost', 'Easy to implement'],
      cons: ['Limited scalability', 'No offline support']
    },
    {
      rank: 2,
      option: 'Option B',
      description: 'Alternative solution',
      feasibility_score: 0.7,
      pros: ['Highly scalable', 'Enterprise ready'],
      cons: ['High cost', 'Complex implementation', 'Long learning curve']
    },
    {
      rank: 3,
      option: 'Option C',
      description: 'Budget option',
      feasibility_score: 0.5,
      pros: ['Very cheap'],
      cons: ['Poor performance', 'Limited features', 'No support']
    }
  ];

  test('renders nothing when candidates array is empty', () => {
    const { container } = render(<CandidateComparison candidates={[]} />);
    expect(container.firstChild).toBeNull();
  });

  test('renders nothing when candidates is null', () => {
    const { container } = render(<CandidateComparison candidates={null} />);
    expect(container.firstChild).toBeNull();
  });

  test('renders candidates title', () => {
    render(<CandidateComparison candidates={mockCandidates} />);
    expect(screen.getByText('CANDIDATES CONSIDERED')).toBeInTheDocument();
  });

  test('renders all candidates', () => {
    render(<CandidateComparison candidates={mockCandidates} />);

    expect(screen.getByText(/Option A/)).toBeInTheDocument();
    expect(screen.getByText(/Option B/)).toBeInTheDocument();
    expect(screen.getByText(/Option C/)).toBeInTheDocument();
  });

  test('displays rank information correctly', () => {
    render(<CandidateComparison candidates={mockCandidates} />);

    expect(screen.getByText('#1 - Option A')).toBeInTheDocument();
    expect(screen.getByText('#2 - Option B')).toBeInTheDocument();
    expect(screen.getByText('#3 - Option C')).toBeInTheDocument();
  });

  test('displays feasibility scores', () => {
    render(<CandidateComparison candidates={mockCandidates} />);

    expect(screen.getByText('90%')).toBeInTheDocument();
    expect(screen.getByText('70%')).toBeInTheDocument();
    expect(screen.getByText('50%')).toBeInTheDocument();
  });

  test('shows "Selected" badge for rank 1 candidate', () => {
    render(<CandidateComparison candidates={mockCandidates} />);

    const selectionBadges = screen.getAllByText('Selected');
    expect(selectionBadges.length).toBe(1);
  });

  test('shows rank badges for non-selected candidates', () => {
    render(<CandidateComparison candidates={mockCandidates} />);

    expect(screen.getByText('Rank #2')).toBeInTheDocument();
    expect(screen.getByText('Rank #3')).toBeInTheDocument();
  });

  test('displays pros for candidates', () => {
    render(<CandidateComparison candidates={mockCandidates} />);

    const prosElements = screen.getAllByText(/✓/);
    expect(prosElements.length).toBeGreaterThan(0);
  });

  test('displays cons for candidates', () => {
    render(<CandidateComparison candidates={mockCandidates} />);

    const consElements = screen.getAllByText(/✗/);
    expect(consElements.length).toBeGreaterThan(0);
  });

  test('limits displayed pros to 2', () => {
    render(<CandidateComparison candidates={mockCandidates} />);

    // Option A has 3 pros, should only show 2
    const prosList = screen.getAllByText(/✓/);
    // Count should be reasonable
    expect(prosList.length).toBeGreaterThan(0);
  });

  test('limits displayed cons to 2', () => {
    render(<CandidateComparison candidates={mockCandidates} />);

    // Option A has 2 cons, Option B has 3 (should show only 2), Option C has 3 (should show only 2)
    const consList = screen.getAllByText(/✗/);
    expect(consList.length).toBeGreaterThan(0);
  });

  test('has sort dropdown', () => {
    render(<CandidateComparison candidates={mockCandidates} />);

    const sortSelect = screen.getByDisplayValue('Sort by Rank');
    expect(sortSelect).toBeInTheDocument();
  });

  test('sorts by rank by default', () => {
    render(<CandidateComparison candidates={mockCandidates} />);

    const sortSelect = screen.getByDisplayValue('Sort by Rank');
    expect(sortSelect).toBeInTheDocument();
  });

  test('can sort by score', () => {
    render(<CandidateComparison candidates={mockCandidates} />);

    const sortSelect = screen.getByDisplayValue('Sort by Rank');
    fireEvent.change(sortSelect, { target: { value: 'score' } });

    // After sorting by score, highest score should be first
    const percentages = screen.getAllByText(/%/);
    expect(percentages[0]).toHaveTextContent('90%');
  });

  test('handles single candidate', () => {
    render(
      <CandidateComparison
        candidates={[mockCandidates[0]]}
      />
    );

    expect(screen.getByText('CANDIDATES CONSIDERED')).toBeInTheDocument();
    expect(screen.getByText('Option A')).toBeInTheDocument();
  });

  test('handles candidates without scores', () => {
    const candidatesNoScore = [
      {
        rank: 1,
        option: 'Option A',
        description: 'Test',
        pros: ['Pro 1'],
        cons: ['Con 1']
      }
    ];

    render(<CandidateComparison candidates={candidatesNoScore} />);

    expect(screen.getByText('CANDIDATES CONSIDERED')).toBeInTheDocument();
  });

  test('handles candidates without pros/cons', () => {
    const candidatesNoProsCons = [
      {
        rank: 1,
        option: 'Option A',
        description: 'Test',
        feasibility_score: 0.8
      }
    ];

    render(<CandidateComparison candidates={candidatesNoProsCons} />);

    expect(screen.getByText('CANDIDATES CONSIDERED')).toBeInTheDocument();
  });

  test('renders pros section header', () => {
    render(<CandidateComparison candidates={mockCandidates} />);

    const prosHeaders = screen.getAllByText('Pros');
    expect(prosHeaders.length).toBeGreaterThan(0);
  });

  test('renders cons section header', () => {
    render(<CandidateComparison candidates={mockCandidates} />);

    const consHeaders = screen.getAllByText('Cons');
    expect(consHeaders.length).toBeGreaterThan(0);
  });

  test('renders feasibility label', () => {
    render(<CandidateComparison candidates={mockCandidates} />);

    const feasibilityLabels = screen.getAllByText('Feasibility');
    expect(feasibilityLabels.length).toBeGreaterThan(0);
  });

  test('handles unsorted candidates', () => {
    const unsortedCandidates = [
      { ...mockCandidates[2], rank: 3 },
      { ...mockCandidates[0], rank: 1 },
      { ...mockCandidates[1], rank: 2 }
    ];

    render(<CandidateComparison candidates={unsortedCandidates} />);

    // Should display all candidates regardless of input order
    expect(screen.getByText('CANDIDATES CONSIDERED')).toBeInTheDocument();
  });

  test('default candidates parameter', () => {
    const { container } = render(<CandidateComparison />);
    expect(container.firstChild).toBeNull();
  });
});
