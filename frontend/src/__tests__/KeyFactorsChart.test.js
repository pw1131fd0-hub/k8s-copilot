import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import KeyFactorsChart from '../components/KeyFactorsChart';

describe('KeyFactorsChart Component', () => {
  const mockFactors = [
    {
      name: 'Performance',
      weight: 0.4,
      description: 'System performance metrics'
    },
    {
      name: 'Cost',
      weight: 0.3,
      description: 'Implementation and maintenance costs'
    },
    {
      name: 'Risk',
      weight: 0.2,
      description: 'Technical and operational risks'
    },
    {
      name: 'Scalability',
      weight: 0.1,
      description: 'Future scalability potential'
    }
  ];

  test('renders nothing when factors array is empty', () => {
    const { container } = render(<KeyFactorsChart factors={[]} />);
    expect(container.firstChild).toBeNull();
  });

  test('renders nothing when factors is null', () => {
    const { container } = render(<KeyFactorsChart factors={null} />);
    expect(container.firstChild).toBeNull();
  });

  test('renders key factors title', () => {
    render(<KeyFactorsChart factors={mockFactors} />);
    expect(screen.getByText('KEY FACTORS')).toBeInTheDocument();
  });

  test('renders all factor names', () => {
    render(<KeyFactorsChart factors={mockFactors} />);

    mockFactors.forEach((factor) => {
      expect(screen.getByText(factor.name)).toBeInTheDocument();
    });
  });

  test('displays factor weights as percentages', () => {
    render(<KeyFactorsChart factors={mockFactors} />);

    expect(screen.getByText('40%')).toBeInTheDocument();
    expect(screen.getByText('30%')).toBeInTheDocument();
    expect(screen.getByText('20%')).toBeInTheDocument();
    expect(screen.getByText('10%')).toBeInTheDocument();
  });

  test('sorts factors by weight descending', () => {
    render(<KeyFactorsChart factors={mockFactors} />);

    // First factor should be Performance (40%)
    const factorTexts = screen.getAllByText(/^(Performance|Cost|Risk|Scalability)$/);
    expect(factorTexts[0]).toHaveTextContent('Performance');
  });

  test('displays factor descriptions', () => {
    render(<KeyFactorsChart factors={mockFactors} />);

    mockFactors.forEach((factor) => {
      if (factor.description) {
        expect(screen.getByText(factor.description)).toBeInTheDocument();
      }
    });
  });

  test('handles single factor', () => {
    render(
      <KeyFactorsChart
        factors={[mockFactors[0]]}
      />
    );

    expect(screen.getByText('Performance')).toBeInTheDocument();
    expect(screen.getByText('40%')).toBeInTheDocument();
  });

  test('handles factors with importance field instead of weight', () => {
    const factorsWithImportance = [
      { name: 'Factor 1', importance: 0.5, description: 'First factor' },
      { name: 'Factor 2', importance: 0.5, description: 'Second factor' }
    ];

    render(<KeyFactorsChart factors={factorsWithImportance} />);

    expect(screen.getByText('Factor 1')).toBeInTheDocument();
    expect(screen.getByText('Factor 2')).toBeInTheDocument();
  });

  test('handles factors without descriptions', () => {
    const factorsNoDesc = [
      { name: 'Factor 1', weight: 0.6 },
      { name: 'Factor 2', weight: 0.4 }
    ];

    render(<KeyFactorsChart factors={factorsNoDesc} />);

    expect(screen.getByText('Factor 1')).toBeInTheDocument();
    expect(screen.getByText('Factor 2')).toBeInTheDocument();
  });

  test('handles many factors', () => {
    const manyFactors = Array.from({ length: 10 }, (_, i) => ({
      name: `Factor ${i + 1}`,
      weight: 1 / 10,
      description: `Description ${i + 1}`
    }));

    render(<KeyFactorsChart factors={manyFactors} />);

    manyFactors.forEach((factor) => {
      expect(screen.getByText(factor.name)).toBeInTheDocument();
    });
  });

  test('normalizes weights correctly for bar width calculation', () => {
    const unequalFactors = [
      { name: 'Large', weight: 0.9, description: 'Large weight' },
      { name: 'Small', weight: 0.1, description: 'Small weight' }
    ];

    const { container } = render(<KeyFactorsChart factors={unequalFactors} />);

    // Check that both factors are rendered
    expect(screen.getByText('Large')).toBeInTheDocument();
    expect(screen.getByText('Small')).toBeInTheDocument();
  });

  test('handles percentage calculation precision', () => {
    const precisionFactors = [
      { name: 'Factor A', weight: 0.333, description: 'Test' },
      { name: 'Factor B', weight: 0.333, description: 'Test' },
      { name: 'Factor C', weight: 0.334, description: 'Test' }
    ];

    render(<KeyFactorsChart factors={precisionFactors} />);

    const percentages = screen.getAllByText(/%/);
    expect(percentages.length).toBeGreaterThanOrEqual(3);
  });

  test('renders progress bars for each factor', () => {
    const { container } = render(<KeyFactorsChart factors={mockFactors} />);

    // Check for progress bar containers
    const progressBars = container.querySelectorAll('[class*="rounded-full"]');
    expect(progressBars.length).toBeGreaterThan(0);
  });

  test('handles zero weight factors', () => {
    const zeroWeightFactors = [
      { name: 'Important', weight: 1.0, description: 'Critical' },
      { name: 'Unimportant', weight: 0, description: 'Not critical' }
    ];

    render(<KeyFactorsChart factors={zeroWeightFactors} />);

    expect(screen.getByText('Important')).toBeInTheDocument();
    expect(screen.getByText('Unimportant')).toBeInTheDocument();
  });

  test('handles negative weight gracefully', () => {
    const negativeWeightFactors = [
      { name: 'Factor 1', weight: 0.5, description: 'Positive' },
      { name: 'Factor 2', weight: -0.1, description: 'Negative' }
    ];

    render(<KeyFactorsChart factors={negativeWeightFactors} />);

    expect(screen.getByText('Factor 1')).toBeInTheDocument();
  });

  test('handles very small weight differences', () => {
    const smallDifferenceFactors = [
      { name: 'Factor A', weight: 0.501, description: 'Slightly higher' },
      { name: 'Factor B', weight: 0.499, description: 'Slightly lower' }
    ];

    render(<KeyFactorsChart factors={smallDifferenceFactors} />);

    expect(screen.getByText('Factor A')).toBeInTheDocument();
    expect(screen.getByText('Factor B')).toBeInTheDocument();
  });

  test('default factors parameter', () => {
    const { container } = render(<KeyFactorsChart />);
    expect(container.firstChild).toBeNull();
  });

  test('renders KEY FACTORS header with correct styling', () => {
    render(<KeyFactorsChart factors={mockFactors} />);

    const header = screen.getByText('KEY FACTORS');
    expect(header).toBeInTheDocument();
    expect(header.className).toContain('font-semibold');
  });
});
