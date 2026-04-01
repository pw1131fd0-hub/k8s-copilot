import React from 'react';
import { useTranslation } from 'react-i18next';
import LanguageSwitcher from './LanguageSwitcher';
import NotificationBell from './NotificationBell';

export default function Header({ theme, onThemeToggle, userId = 'user' }) {
  const { t } = useTranslation();
  return (
    <header className="sticky top-0 z-50 bg-slate-900 dark:bg-slate-900 border-b border-slate-800 dark:border-slate-700 backdrop-blur supports-[backdrop-filter]:bg-slate-900/75">
      <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
        {/* Logo */}
        <div className="flex items-center gap-3">
          <span className="text-3xl select-none">🦞</span>
          <div>
            <h1 className="text-xl font-bold text-slate-100 dark:text-slate-100 leading-tight">
              {t('common.appName')}
            </h1>
            <p className="text-xs text-slate-400 dark:text-slate-500 leading-none">
              {t('home.subtitle')}
            </p>
          </div>
        </div>

        {/* Controls: NotificationBell + Language Switcher + Theme Toggle */}
        <div className="flex items-center gap-3">
          <NotificationBell userId={userId} />
          <LanguageSwitcher />
          <button
          onClick={onThemeToggle}
          className="p-2 rounded-lg bg-slate-800 dark:bg-slate-800 hover:bg-slate-700 dark:hover:bg-slate-700 transition-colors text-slate-300 dark:text-slate-400"
          title="Toggle theme"
          aria-label="Toggle theme"
        >
          {theme === 'dark' ? (
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0zm-.464 4.95l.707.707a1 1 0 001.414-1.414l-.707-.707a1 1 0 00-1.414 1.414zm2.12-10.607a1 1 0 010 1.414l-.707.707a1 1 0 11-1.414-1.414l.707-.707a1 1 0 011.414 0zM17 11a1 1 0 100-2h-1a1 1 0 100 2h1zm-7 4a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zM5.05 6.464A1 1 0 106.464 5.05l-.707-.707a1 1 0 00-1.414 1.414l.707.707zm5.657-9.193a1 1 0 00-1.414 0l-.707.707A1 1 0 005.05 6.464l.707-.707a1 1 0 001.414-1.414zM5 8a1 1 0 100-2H4a1 1 0 000 2h1z" clipRule="evenodd" />
            </svg>
          ) : (
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path d="M17.293 13.293A8 8 0 016.707 2.707a8.001 8.001 0 1010.586 10.586z" />
            </svg>
          )}
          </button>
        </div>
      </div>
    </header>
  );
}
