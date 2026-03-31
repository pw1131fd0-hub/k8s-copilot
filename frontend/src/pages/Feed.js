import React, { useState, useEffect } from 'react';
import PostCard from '../components/PostCard';
import PostComposer from '../components/PostComposer';
import { fetchPosts } from '../utils/api';

export default function Feed() {
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [selectedMoodFilter, setSelectedMoodFilter] = useState(null);

  useEffect(() => {
    loadPosts();
  }, [offset]);

  const loadPosts = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchPosts(20, offset);
      setPosts(offset === 0 ? data.posts : [...posts, ...data.posts]);
      setTotal(data.total);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handlePostCreated = (newPost) => {
    setPosts([newPost, ...posts]);
    setTotal(total + 1);
  };

  const handlePostDeleted = (postId) => {
    setPosts(posts.filter(p => p.id !== postId));
    setTotal(Math.max(0, total - 1));
  };

  const filteredPosts = selectedMoodFilter
    ? posts.filter(p => p.mood.includes(selectedMoodFilter))
    : posts;

  const MOOD_FILTERS = [
    { emoji: '😊', label: 'Happy' },
    { emoji: '😐', label: 'Neutral' },
    { emoji: '😔', label: 'Sad' },
    { emoji: '🥰', label: 'Grateful' },
    { emoji: '💭', label: 'Thoughtful' },
    { emoji: '🎯', label: 'Ambitious' },
  ];

  return (
    <main className="flex-1 max-w-2xl border-l border-r border-slate-800 dark:border-slate-700 min-h-screen">
      {/* Sticky Composer */}
      <div className="sticky top-16 z-40 border-b border-slate-800 dark:border-slate-700 bg-slate-900/95 dark:bg-slate-900/95 backdrop-blur">
        <PostComposer onPostCreated={handlePostCreated} />
      </div>

      {/* Mood Filters */}
      <div className="border-b border-slate-800 dark:border-slate-700 px-4 py-3 flex gap-2 overflow-x-auto">
        <button
          onClick={() => setSelectedMoodFilter(null)}
          className={`px-3 py-1.5 rounded-full text-sm font-medium transition-colors whitespace-nowrap ${
            selectedMoodFilter === null
              ? 'bg-blue-600 text-white'
              : 'bg-slate-800 dark:bg-slate-800 text-slate-300 dark:text-slate-300 hover:bg-slate-700'
          }`}
        >
          All
        </button>
        {MOOD_FILTERS.map((mood) => (
          <button
            key={mood.emoji}
            onClick={() => setSelectedMoodFilter(mood.emoji)}
            className={`px-3 py-1.5 rounded-full text-sm font-medium transition-colors whitespace-nowrap ${
              selectedMoodFilter === mood.emoji
                ? 'bg-blue-600 text-white'
                : 'bg-slate-800 dark:bg-slate-800 text-slate-300 dark:text-slate-300 hover:bg-slate-700'
            }`}
          >
            {mood.emoji} {mood.label}
          </button>
        ))}
      </div>

      {/* Posts Feed */}
      <div className="divide-y divide-slate-800 dark:divide-slate-700">
        {error && (
          <div className="p-4 text-center text-red-400">
            <p>Error loading posts: {error}</p>
          </div>
        )}

        {filteredPosts.length === 0 && !loading ? (
          <div className="text-center py-12 text-slate-400">
            <p className="text-lg mb-2">No posts yet</p>
            <p className="text-sm">Share your first thought with the world!</p>
          </div>
        ) : (
          filteredPosts.map((post) => (
            <PostCard
              key={post.id}
              post={post}
              onDeleted={handlePostDeleted}
            />
          ))
        )}

        {loading && (
          <div className="p-4 text-center">
            <div className="inline-block">
              <div className="w-8 h-8 border-4 border-slate-700 border-t-blue-500 rounded-full animate-spin" />
            </div>
          </div>
        )}
      </div>

      {/* Load More Button */}
      {!loading && posts.length < total && (
        <div className="p-4 border-t border-slate-800 dark:border-slate-700 text-center">
          <button
            onClick={() => setOffset(offset + 20)}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
          >
            Load More
          </button>
        </div>
      )}
    </main>
  );
}
