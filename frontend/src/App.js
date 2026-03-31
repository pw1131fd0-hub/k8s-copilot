import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import OfflineIndicator from './components/OfflineIndicator';
import Feed from './pages/Feed';
import PostDetail from './pages/PostDetail';
import Trends from './pages/Trends';
import { initOfflineSupport } from './utils/pwa';
import './App.css';

export default function App() {
  const [theme, setTheme] = useState(() => {
    // Default to dark theme
    const saved = localStorage.getItem('clawbook-theme');
    return saved || 'dark';
  });

  useEffect(() => {
    // Initialize PWA offline support (skip in test environment)
    if (process.env.NODE_ENV !== 'test') {
      initOfflineSupport().catch(error => {
        console.error('Failed to initialize offline support:', error);
      });
    }
  }, []);

  useEffect(() => {
    localStorage.setItem('clawbook-theme', theme);
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prev => prev === 'dark' ? 'light' : 'dark');
  };

  return (
    <BrowserRouter>
      <div className={`${theme === 'dark' ? 'dark bg-slate-950 text-slate-100' : 'bg-white text-slate-900'} min-h-screen transition-colors duration-300`}>
        <Header theme={theme} onThemeToggle={toggleTheme} />
        <OfflineIndicator />

        <div className="flex max-w-7xl mx-auto">
          <Sidebar />

          <Routes>
            <Route path="/" element={<Feed />} />
            <Route path="/post/:postId" element={<PostDetail />} />
            <Route path="/trends" element={<Trends />} />
          </Routes>
        </div>
      </div>
    </BrowserRouter>
  );
}
