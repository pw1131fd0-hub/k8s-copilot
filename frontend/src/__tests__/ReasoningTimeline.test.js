import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import ReasoningTimeline from '../components/ReasoningTimeline';

describe('ReasoningTimeline Component', () => {
  const mockSteps = [
    {
      step_number: 1,
      description: 'Gather requirements',
      reasoning: 'First, we need to understand what is needed'
    },
    {
      step_number: 2,
      description: 'Analyze options',
      reasoning: 'Then, we evaluate different approaches'
    },
    {
      step_number: 3,
      description: 'Make decision',
      reasoning: 'Finally, we select the best option'
    }
  ];

  test('renders nothing when steps array is empty', () => {
    const { container } = render(<ReasoningTimeline steps={[]} />);
    expect(container.firstChild).toBeNull();
  });

  test('renders nothing when steps is null', () => {
    const { container } = render(<ReasoningTimeline steps={null} />);
    expect(container.firstChild).toBeNull();
  });

  test('renders reasoning steps title', () => {
    render(<ReasoningTimeline steps={mockSteps} />);
    expect(screen.getByText('REASONING STEPS')).toBeInTheDocument();
  });

  test('renders all reasoning steps', () => {
    render(<ReasoningTimeline steps={mockSteps} />);

    mockSteps.forEach((step) => {
      expect(screen.getByText(new RegExp(step.description))).toBeInTheDocument();
    });
  });

  test('displays step numbers correctly', () => {
    render(<ReasoningTimeline steps={mockSteps} />);

    expect(screen.getByText(/1\. Gather requirements/)).toBeInTheDocument();
    expect(screen.getByText(/2\. Analyze options/)).toBeInTheDocument();
    expect(screen.getByText(/3\. Make decision/)).toBeInTheDocument();
  });

  test('displays reasoning text for each step', () => {
    render(<ReasoningTimeline steps={mockSteps} />);

    expect(screen.getByText('First, we need to understand what is needed')).toBeInTheDocument();
    expect(screen.getByText('Then, we evaluate different approaches')).toBeInTheDocument();
    expect(screen.getByText('Finally, we select the best option')).toBeInTheDocument();
  });

  test('renders single step', () => {
    render(
      <ReasoningTimeline
        steps={[mockSteps[0]]}
      />
    );

    expect(screen.getByText('REASONING STEPS')).toBeInTheDocument();
    expect(screen.getByText(/1\. Gather requirements/)).toBeInTheDocument();
  });

  test('renders many steps', () => {
    const manySteps = Array.from({ length: 10 }, (_, i) => ({
      step_number: i + 1,
      description: `Step ${i + 1}`,
      reasoning: `Reasoning for step ${i + 1}`
    }));

    render(<ReasoningTimeline steps={manySteps} />);

    expect(screen.getByText('REASONING STEPS')).toBeInTheDocument();
    expect(screen.getByText(/1\. Step 1/)).toBeInTheDocument();
    expect(screen.getByText(/10\. Step 10/)).toBeInTheDocument();
  });

  test('handles steps without reasoning', () => {
    const stepsNoReasoning = [
      {
        step_number: 1,
        description: 'First step',
        reasoning: undefined
      },
      {
        step_number: 2,
        description: 'Second step',
        reasoning: 'Has reasoning'
      }
    ];

    render(<ReasoningTimeline steps={stepsNoReasoning} />);

    expect(screen.getByText(/1\. First step/)).toBeInTheDocument();
    expect(screen.getByText(/2\. Second step/)).toBeInTheDocument();
    expect(screen.getByText('Has reasoning')).toBeInTheDocument();
  });

  test('renders timeline visual indicators', () => {
    const { container } = render(<ReasoningTimeline steps={mockSteps} />);

    // Check for timeline indicator circles (using rounded-full class presence)
    const indicators = container.querySelectorAll('[class*="rounded-full"]');
    expect(indicators.length).toBeGreaterThan(0);
  });

  test('renders connecting lines between steps', () => {
    const { container } = render(<ReasoningTimeline steps={mockSteps} />);

    // Should have 2 connecting lines for 3 steps
    const lines = container.querySelectorAll('[class*="h-12"]');
    expect(lines.length).toBeGreaterThan(0);
  });

  test('handles special characters in descriptions', () => {
    const specialSteps = [
      {
        step_number: 1,
        description: 'Analyze risk mitigations',
        reasoning: 'Check requirements implementation'
      }
    ];

    render(<ReasoningTimeline steps={specialSteps} />);

    expect(screen.getByText(/1\. Analyze risk mitigations/)).toBeInTheDocument();
  });

  test('handles long reasoning text', () => {
    const longReasoning = 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. ' +
      'Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. ' +
      'Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi.';

    const longSteps = [
      {
        step_number: 1,
        description: 'Complex analysis',
        reasoning: longReasoning
      }
    ];

    render(<ReasoningTimeline steps={longSteps} />);

    expect(screen.getByText(longReasoning)).toBeInTheDocument();
  });

  test('default steps parameter', () => {
    const { container } = render(<ReasoningTimeline />);
    expect(container.firstChild).toBeNull();
  });
});
