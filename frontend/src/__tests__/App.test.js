import React from 'react';
import { render, screen } from '@testing-library/react';
import App from '../App';

// Mock react-router-dom for testing
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  BrowserRouter: ({ children }) => <div data-testid="browser-router">{children}</div>,
  Routes: ({ children }) => <div data-testid="routes">{children}</div>,
  Route: () => null,
  Navigate: () => null,
  useParams: () => ({}),
}));

// Mock Header to avoid complex dependencies
jest.mock('../components/Header', () => {
  return function MockHeader() {
    return <div data-testid="header">Header</div>;
  };
});

// Mock Sidebar to avoid complex dependencies
jest.mock('../components/Sidebar', () => {
  return function MockSidebar() {
    return <div data-testid="sidebar">Sidebar</div>;
  };
});

// Mock pages to avoid complex dependencies
jest.mock('../pages/Feed', () => {
  return function MockFeed() {
    return <div data-testid="feed">Feed</div>;
  };
});

jest.mock('../pages/PostDetail', () => {
  return function MockPostDetail() {
    return <div data-testid="post-detail">PostDetail</div>;
  };
});

jest.mock('../pages/Trends', () => {
  return function MockTrends() {
    return <div data-testid="trends">Trends</div>;
  };
});

describe('App Component', () => {
  beforeEach(() => {
    // Clear localStorage before each test
    localStorage.clear();
  });

  test('renders without crashing', () => {
    render(<App />);
    expect(screen.getByTestId('browser-router')).toBeInTheDocument();
  });

  test('contains Header component', () => {
    render(<App />);
    expect(screen.getByTestId('header')).toBeInTheDocument();
  });

  test('contains Sidebar component', () => {
    render(<App />);
    expect(screen.getByTestId('sidebar')).toBeInTheDocument();
  });

  test('contains Routes component', () => {
    render(<App />);
    expect(screen.getByTestId('routes')).toBeInTheDocument();
  });

  test('loads dark theme by default', () => {
    render(<App />);
    const container = document.documentElement;
    // Check if dark class is applied or theme is dark
    expect(localStorage.getItem('clawbook-theme')).toBe('dark');
  });

  test('saves theme preference to localStorage', () => {
    render(<App />);
    // Theme is initialized as 'dark' by default
    expect(localStorage.getItem('clawbook-theme')).toBe('dark');
  });

  test('applies correct styling classes', () => {
    const { container } = render(<App />);
    const mainDiv = container.querySelector('[class*="min-h-screen"]');
    expect(mainDiv).toBeInTheDocument();
  });
});
