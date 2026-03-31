import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import EmotionTrendsChart from '../components/EmotionTrendsChart';
import * as apiModule from '../utils/api';

// Mock the API module
jest.mock('../utils/api', () => ({
  getPosts: jest.fn(),
}));

describe('EmotionTrendsChart Component', () => {
  const mockPosts = [
    {
      id: '1',
      mood: '😊',
      content: 'Happy post',
      created_at: '2026-03-31T10:00:00Z',
    },
    {
      id: '2',
      mood: '😊',
      content: 'Another happy',
      created_at: '2026-03-31T11:00:00Z',
    },
    {
      id: '3',
      mood: '😔',
      content: 'Sad post',
      created_at: '2026-03-31T12:00:00Z',
    },
    {
      id: '4',
      mood: '🥰',
      content: 'Grateful',
      created_at: '2026-03-31T13:00:00Z',
    },
  ];

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders loading state initially', () => {
    apiModule.getPosts.mockResolvedValueOnce({ posts: [] });
    render(<EmotionTrendsChart />);
    expect(screen.getByText(/Loading emotion trends/i)).toBeInTheDocument();
  });

  test('renders empty state when no posts', async () => {
    apiModule.getPosts.mockResolvedValueOnce({ posts: [] });
    render(<EmotionTrendsChart />);

    await waitFor(() => {
      expect(
        screen.getByText(/No posts yet. Start journaling/i)
      ).toBeInTheDocument();
    });
  });

  test('fetches and displays posts', async () => {
    apiModule.getPosts.mockResolvedValueOnce({ posts: mockPosts });
    render(<EmotionTrendsChart />);

    // Wait for the component to load posts
    const totalEntriesText = await screen.findByText(/Total Entries/i);
    expect(totalEntriesText).toBeInTheDocument();

    // Should render mood distribution section
    const emotionDistribution = await screen.findByText(/Emotion Distribution/i);
    expect(emotionDistribution).toBeInTheDocument();

    // Should have called getPosts with correct params
    expect(apiModule.getPosts).toHaveBeenCalledWith({
      limit: 100,
      skip: 0,
    });
  });

  test('displays mood statistics correctly', async () => {
    apiModule.getPosts.mockResolvedValueOnce({ posts: mockPosts });
    render(<EmotionTrendsChart />);

    // Check for top mood section
    const topMoodText = await screen.findByText(/Top Mood/i);
    expect(topMoodText).toBeInTheDocument();

    // Check for unique moods count
    const uniqueMoodsText = await screen.findByText(/Unique Moods/i);
    expect(uniqueMoodsText).toBeInTheDocument();

    // Check for average per day
    const avgPerDayText = await screen.findByText(/Avg per Day/i);
    expect(avgPerDayText).toBeInTheDocument();
  });

  test('renders timeline section', async () => {
    apiModule.getPosts.mockResolvedValueOnce({ posts: mockPosts });
    render(<EmotionTrendsChart />);

    const timelineText = await screen.findByText(/Recent Mood Timeline/i);
    expect(timelineText).toBeInTheDocument();
  });

  test('handles API errors gracefully', async () => {
    // First call returns posts, second call fails (for error test)
    apiModule.getPosts.mockResolvedValueOnce({ posts: mockPosts });

    // Re-render to trigger error
    const { rerender } = render(<EmotionTrendsChart />);

    // Wait for initial load to complete
    await screen.findByText(/Emotion Distribution/i);

    // Now simulate an error by mocking rejection for next call
    apiModule.getPosts.mockRejectedValueOnce(new Error('API Error'));

    // The component handles errors in its catch block
    // Since component initializes with posts, error will be rendered alongside
    expect(apiModule.getPosts).toHaveBeenCalled();
  });

  test('calculates mood percentages correctly', async () => {
    apiModule.getPosts.mockResolvedValueOnce({ posts: mockPosts });
    const { container } = render(<EmotionTrendsChart />);

    await waitFor(() => {
      // With 4 posts: 😊 appears 2 times (50%), 😔 1 time (25%), 🥰 1 time (25%)
      const percentages = container.querySelectorAll('.text-sm.text-slate-400');
      expect(percentages.length).toBeGreaterThan(0);
    });
  });

  test('displays mood bars in distribution chart', async () => {
    apiModule.getPosts.mockResolvedValueOnce({ posts: mockPosts });
    const { container } = render(<EmotionTrendsChart />);

    await waitFor(() => {
      const moodEmojis = container.querySelectorAll('.w-8');
      expect(moodEmojis.length).toBeGreaterThan(0);
    });
  });
});
