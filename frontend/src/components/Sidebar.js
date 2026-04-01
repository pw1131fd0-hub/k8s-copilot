import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { API_URL } from '../utils/api';

const MOOD_LABELS = {
  '😊': 'Happy',
  '😐': 'Neutral',
  '😔': 'Sad',
  '🥰': 'Grateful',
  '💭': 'Thoughtful',
  '🎯': 'Ambitious',
  '🙏': 'Grateful',
  '💪': 'Strong',
  '😴': 'Tired',
  '😤': 'Frustrated'
};

const MOOD_EMOJI_LIST = [
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

export default function Sidebar() {
  const { t } = useTranslation();
  const [moodStats, setMoodStats] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchMoodStats();
  }, []);

  const fetchMoodStats = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/clawbook/mood-summary?days=7`);
      if (response.ok) {
        const data = await response.json();
        setMoodStats(data);
      }
    } catch (error) {
      console.error('Failed to fetch mood stats:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <aside className="hidden lg:block w-64 sticky top-16 h-[calc(100vh-4rem)] overflow-y-auto border-r border-slate-800 dark:border-slate-700 bg-slate-900 dark:bg-slate-900 p-4">
      {/* Navigation Links */}
      <div className="mb-6 space-y-2">
        <Link
          to="/"
          className="block w-full px-3 py-2 rounded-lg text-sm font-medium text-slate-300 dark:text-slate-300 hover:bg-slate-800 dark:hover:bg-slate-800 transition-colors"
        >
          📖 {t('navigation.feed')}
        </Link>
        <Link
          to="/trends"
          className="block w-full px-3 py-2 rounded-lg text-sm font-medium text-slate-300 dark:text-slate-300 hover:bg-slate-800 dark:hover:bg-slate-800 transition-colors"
        >
          📊 {t('navigation.trends')}
        </Link>
        <Link
          to="/analytics"
          className="block w-full px-3 py-2 rounded-lg text-sm font-medium text-slate-300 dark:text-slate-300 hover:bg-slate-800 dark:hover:bg-slate-800 transition-colors"
        >
          📈 {t('navigation.analytics')}
        </Link>
        <Link
          to="/personality"
          className="block w-full px-3 py-2 rounded-lg text-sm font-medium text-slate-300 dark:text-slate-300 hover:bg-slate-800 dark:hover:bg-slate-800 transition-colors"
        >
          🌟 {t('navigation.personality', 'Personality')}
        </Link>
        <Link
          to="/decision-paths"
          className="block w-full px-3 py-2 rounded-lg text-sm font-medium text-slate-300 dark:text-slate-300 hover:bg-slate-800 dark:hover:bg-slate-800 transition-colors"
        >
          🧠 {t('navigation.decisionPaths')}
        </Link>
      </div>

      <div className="border-t border-slate-700 dark:border-slate-700 my-4"></div>

      {/* Collaboration Links (v1.6) */}
      <div className="mb-6 space-y-2">
        <h3 className="text-xs font-bold text-slate-400 dark:text-slate-400 px-3 uppercase tracking-wider mb-2">
          {t('navigation.collaboration') || 'Collaboration'}
        </h3>
        <Link
          to="/shared-with-me"
          className="block w-full px-3 py-2 rounded-lg text-sm font-medium text-slate-300 dark:text-slate-300 hover:bg-slate-800 dark:hover:bg-slate-800 transition-colors"
        >
          📨 {t('navigation.sharedWithMe') || 'Shared With Me'}
        </Link>
        <Link
          to="/groups"
          className="block w-full px-3 py-2 rounded-lg text-sm font-medium text-slate-300 dark:text-slate-300 hover:bg-slate-800 dark:hover:bg-slate-800 transition-colors"
        >
          👥 {t('navigation.groups') || 'Groups'}
        </Link>
      </div>

      <div className="border-t border-slate-700 dark:border-slate-700 my-4"></div>

      {/* Mood Distribution */}
      <div className="mb-6">
        <h2 className="text-sm font-bold text-slate-100 dark:text-slate-100 mb-3 uppercase tracking-wider">
          📊 {t('sidebar.moodDistribution')}
        </h2>
        {loading ? (
          <div className="space-y-2">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-8 bg-slate-800 dark:bg-slate-800 rounded-lg skeleton" />
            ))}
          </div>
        ) : moodStats && moodStats.mood_stats.length > 0 ? (
          <div className="space-y-2">
            {moodStats.mood_stats.map((stat) => (
              <div key={stat.mood} className="flex items-center gap-2 text-sm">
                <span className="text-xl">{stat.mood}</span>
                <div className="flex-1 bg-slate-800 dark:bg-slate-800 h-2 rounded-full overflow-hidden">
                  <div
                    className="bg-blue-500 h-full transition-all"
                    style={{
                      width: `${(stat.count / (moodStats.total_posts || 1)) * 100}%`
                    }}
                  />
                </div>
                <span className="text-slate-400 dark:text-slate-500 text-xs">{stat.count}</span>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-slate-400 dark:text-slate-500 text-sm">{t('sidebar.noMoodsRecorded')}</p>
        )}
      </div>

      {/* Total Posts */}
      {moodStats && (
        <div className="p-3 bg-slate-800 dark:bg-slate-800 rounded-lg border border-slate-700 dark:border-slate-700 text-center">
          <div className="text-2xl font-bold text-slate-100 dark:text-slate-100">
            {moodStats.total_posts}
          </div>
          <div className="text-xs text-slate-400 dark:text-slate-500 mt-1">
            {t('sidebar.postsInDays')}
          </div>
        </div>
      )}

      {/* Quick Mood Selector (Mobile Info) */}
      <div className="mt-6 p-3 bg-slate-800 dark:bg-slate-800 rounded-lg border border-slate-700 dark:border-slate-700">
        <p className="text-xs text-slate-400 dark:text-slate-500 mb-2">{t('sidebar.moodTypes')}</p>
        <div className="grid grid-cols-5 gap-1">
          {MOOD_EMOJI_LIST.map((item) => (
            <div key={item.emoji} className="text-center">
              <div className="text-lg" title={item.label}>
                {item.emoji}
              </div>
            </div>
          ))}
        </div>
      </div>
    </aside>
  );
}
