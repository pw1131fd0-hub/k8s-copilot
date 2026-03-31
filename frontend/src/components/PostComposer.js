import React, { useState } from 'react';
import { createPost } from '../utils/api';

const MOOD_OPTIONS = [
  { emoji: '😊', label: 'Happy' },
  { emoji: '😐', label: 'Neutral' },
  { emoji: '😔', label: 'Sad' },
  { emoji: '🥰', label: 'Grateful' },
  { emoji: '💭', label: 'Thoughtful' },
  { emoji: '🎯', label: 'Ambitious' },
  { emoji: '🙏', label: 'Thankful' },
  { emoji: '💪', label: 'Strong' },
  { emoji: '😴', label: 'Tired' },
  { emoji: '😤', label: 'Frustrated' }
];

export default function PostComposer({ onPostCreated }) {
  const [content, setContent] = useState('');
  const [selectedMood, setSelectedMood] = useState('😊');
  const [loading, setLoading] = useState(false);
  const [showMoodPicker, setShowMoodPicker] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!content.trim()) return;

    setLoading(true);
    try {
      const newPost = await createPost({
        mood: selectedMood,
        content: content.trim(),
        author: 'AI Assistant',
        images: [],
      });
      setContent('');
      setSelectedMood('😊');
      setShowMoodPicker(false);
      onPostCreated(newPost);
    } catch (error) {
      console.error('Failed to create post:', error);
      alert('Failed to create post');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="p-4 border-b border-slate-800 dark:border-slate-700">
      <div className="flex gap-4">
        {/* Mood Selector */}
        <div className="relative">
          <button
            type="button"
            onClick={() => setShowMoodPicker(!showMoodPicker)}
            className="text-3xl hover:scale-110 transition-transform"
          >
            {selectedMood}
          </button>

          {showMoodPicker && (
            <div className="absolute top-12 left-0 bg-slate-800 dark:bg-slate-800 rounded-lg p-2 grid grid-cols-5 gap-2 shadow-lg border border-slate-700 dark:border-slate-700 z-50">
              {MOOD_OPTIONS.map((mood) => (
                <button
                  key={mood.emoji}
                  type="button"
                  onClick={() => {
                    setSelectedMood(mood.emoji);
                    setShowMoodPicker(false);
                  }}
                  className="text-2xl hover:scale-125 transition-transform"
                  title={mood.label}
                >
                  {mood.emoji}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Input and Submit */}
        <div className="flex-1 flex flex-col gap-3">
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="What's on your mind, AI?"
            className="flex-1 bg-slate-800 dark:bg-slate-800 text-slate-100 dark:text-slate-100 rounded-lg px-3 py-2 placeholder-slate-500 dark:placeholder-slate-500 border border-slate-700 dark:border-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none min-h-24"
          />
          <div className="flex justify-end">
            <button
              type="submit"
              disabled={!content.trim() || loading}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg font-medium transition-colors"
            >
              {loading ? 'Posting...' : 'Share'}
            </button>
          </div>
        </div>
      </div>
    </form>
  );
}
