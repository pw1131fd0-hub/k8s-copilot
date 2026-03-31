import React from 'react';
import { render, screen } from '@testing-library/react';
import Trends from '../pages/Trends';
import * as apiModule from '../utils/api';

// Mock EmotionTrendsChart component to avoid complex dependencies
jest.mock('../components/EmotionTrendsChart', () => {
  return function MockEmotionTrendsChart() {
    return <div data-testid="emotion-trends-chart">Emotion Trends Chart</div>;
  };
});

// Mock the API module
jest.mock('../utils/api', () => ({
  getPosts: jest.fn(),
}));

describe('Trends Page', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders Trends page title', () => {
    render(<Trends />);
    expect(screen.getByText(/Your Emotion Trends/i)).toBeInTheDocument();
  });

  test('displays page subtitle', () => {
    render(<Trends />);
    expect(
      screen.getByText(/Visualize your emotional journey over time/i)
    ).toBeInTheDocument();
  });

  test('renders EmotionTrendsChart component', () => {
    render(<Trends />);
    expect(screen.getByTestId('emotion-trends-chart')).toBeInTheDocument();
  });

  test('displays emoji icon in title', () => {
    render(<Trends />);
    const title = screen.getByText(/Your Emotion Trends/i);
    expect(title.textContent).toContain('📊');
  });

  test('main element has proper responsive classes', () => {
    const { container } = render(<Trends />);
    const main = container.querySelector('main');
    expect(main).toHaveClass('flex-1');
    expect(main).toHaveClass('max-w-4xl');
    expect(main).toHaveClass('mx-auto');
  });

  test('has proper dark mode styling', () => {
    const { container } = render(<Trends />);
    const header = container.querySelector('div[class*="sticky"]');
    // Check that header has dark mode related classes in its class string
    expect(header.className).toMatch(/dark:/);
    expect(header.className).toContain('dark:border-slate-700');
  });

  test('has proper spacing and padding', () => {
    const { container } = render(<Trends />);
    const content = container.querySelector('div.p-6');
    expect(content).toHaveClass('space-y-6');
  });
});
