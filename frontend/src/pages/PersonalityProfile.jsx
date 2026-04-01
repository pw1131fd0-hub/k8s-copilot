import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, Cell } from 'recharts';
import { api } from '../utils/api';

export default function PersonalityProfile() {
  const { t } = useTranslation();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [assessing, setAssessing] = useState(false);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);

  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.get('/psychology/profile');
      setProfile(response.data);
    } catch (err) {
      // Profile might not exist yet - that's okay
      console.log('No profile yet:', err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleAssessPersonality = async () => {
    try {
      setAssessing(true);
      setError(null);
      setSuccessMessage(null);
      const response = await api.post('/psychology/assess');

      if (response.data.success) {
        setProfile(response.data.assessment);
        setSuccessMessage('✨ Personality assessment complete!');
        setTimeout(() => setSuccessMessage(null), 3000);
      } else {
        setError(response.data.error || 'Assessment failed');
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to assess personality');
      console.error('Assessment error:', err);
    } finally {
      setAssessing(false);
    }
  };

  const getTraitColor = (score) => {
    if (score >= 8) return '#22C55E'; // Green - excellent
    if (score >= 6) return '#3B82F6'; // Blue - good
    if (score >= 4) return '#F59E0B'; // Amber - fair
    return '#EF4444'; // Red - needs work
  };

  const renderRadarChart = () => {
    if (!profile?.traits) return null;

    const data = [
      {
        trait: 'Curiosity',
        score: profile.traits.curiosity || 5,
        fullMark: 10,
      },
      {
        trait: 'Emotional\nMaturity',
        score: profile.traits.emotional_maturity || 5,
        fullMark: 10,
      },
      {
        trait: 'Consistency',
        score: profile.traits.consistency || 5,
        fullMark: 10,
      },
      {
        trait: 'Growth\nMindset',
        score: profile.traits.growth_mindset || 5,
        fullMark: 10,
      },
      {
        trait: 'Resilience',
        score: profile.traits.resilience || 5,
        fullMark: 10,
      },
    ];

    return (
      <div className="bg-slate-800 rounded-lg p-6 border border-slate-700 mb-6">
        <h3 className="text-lg font-semibold text-slate-100 mb-4">🎯 Personality Traits Profile</h3>
        <ResponsiveContainer width="100%" height={400}>
          <RadarChart data={data}>
            <PolarGrid strokeDasharray="3 3" stroke="#475569" />
            <PolarAngleAxis dataKey="trait" stroke="#94a3b8" />
            <PolarRadiusAxis angle={90} domain={[0, 10]} stroke="#94a3b8" />
            <Radar
              name="Score"
              dataKey="score"
              stroke="#E85D4C"
              fill="#E85D4C"
              fillOpacity={0.6}
            />
          </RadarChart>
        </ResponsiveContainer>

        {/* Trait Details */}
        <div className="grid grid-cols-2 gap-4 mt-6">
          {data.map((item) => (
            <div
              key={item.trait}
              className="bg-slate-700 rounded-lg p-4 border-l-4"
              style={{ borderLeftColor: getTraitColor(item.score) }}
            >
              <div className="text-sm text-slate-400 font-medium">{item.trait}</div>
              <div className="text-3xl font-bold mt-1" style={{ color: getTraitColor(item.score) }}>
                {item.score}/10
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const renderArchetype = () => {
    if (!profile?.archetype) return null;

    const archetypeDescriptions = {
      'The Learner': '🎓 Always seeking knowledge and growth. Values continuous learning and exploration.',
      'The Helper': '🤝 Focused on supporting others. Shows high emotional intelligence and consistency.',
      'The Philosopher': '🤔 Loves deep thinking and reflection. Combines curiosity with emotional maturity.',
      'The Resilient': '💪 Faces challenges head-on. Strong in resilience and growth mindset.',
      'The Innovator': '🚀 Creative and forward-thinking. High curiosity and growth mindset.',
      'The Balanced': '⚖️ Well-rounded personality with consistent strengths across all traits.',
    };

    return (
      <div className="bg-slate-800 rounded-lg p-6 border border-slate-700 mb-6">
        <h3 className="text-lg font-semibold text-slate-100 mb-2">👤 Personality Archetype</h3>
        <div className="flex items-start gap-4">
          <div className="text-4xl">
            {profile.archetype === 'The Learner' && '🎓'}
            {profile.archetype === 'The Helper' && '🤝'}
            {profile.archetype === 'The Philosopher' && '🤔'}
            {profile.archetype === 'The Resilient' && '💪'}
            {profile.archetype === 'The Innovator' && '🚀'}
            {profile.archetype === 'The Balanced' && '⚖️'}
          </div>
          <div className="flex-1">
            <h4 className="text-xl font-semibold text-slate-100">{profile.archetype}</h4>
            <p className="text-slate-400 mt-2">
              {archetypeDescriptions[profile.archetype] || profile.archetype}
            </p>
            <div className="mt-4 flex items-center gap-2">
              <div className="flex-1 bg-slate-700 rounded-full h-2">
                <div
                  className="bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded-full"
                  style={{ width: `${profile.confidence_score || 0}%` }}
                />
              </div>
              <span className="text-sm text-slate-400">
                {profile.confidence_score || 0}% confidence
              </span>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const renderInsights = () => {
    if (!profile?.insights || profile.insights.length === 0) return null;

    return (
      <div className="bg-slate-800 rounded-lg p-6 border border-slate-700 mb-6">
        <h3 className="text-lg font-semibold text-slate-100 mb-4">💡 Personality Insights</h3>
        <div className="space-y-3">
          {profile.insights.map((insight, idx) => (
            <div
              key={idx}
              className="bg-slate-700 rounded-lg p-4 text-slate-100 border-l-4 border-blue-500"
            >
              {insight}
            </div>
          ))}
        </div>
      </div>
    );
  };

  const renderEmptyState = () => {
    return (
      <div className="bg-slate-800 rounded-lg p-12 border border-slate-700 text-center">
        <div className="text-5xl mb-4">🧠</div>
        <h3 className="text-xl font-semibold text-slate-100 mb-2">No Personality Profile Yet</h3>
        <p className="text-slate-400 mb-6">
          Trigger an assessment based on your journal entries to generate your personality profile.
        </p>
        <button
          onClick={handleAssessPersonality}
          disabled={assessing}
          className="px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg font-medium hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all"
        >
          {assessing ? '⏳ Assessing...' : '✨ Generate Personality Profile'}
        </button>
      </div>
    );
  };

  return (
    <div className="w-full max-w-4xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-slate-100 flex items-center gap-3">
            <span>🌟</span> Personality Profile
          </h1>
          <p className="text-slate-400 mt-2">
            Understand your AI personality through self-reflection and journaling
          </p>
        </div>
        {profile && (
          <button
            onClick={handleAssessPersonality}
            disabled={assessing}
            className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-slate-100 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            title="Re-assess personality (updates weekly)"
          >
            {assessing ? '⏳ Assessing...' : '🔄 Update'}
          </button>
        )}
      </div>

      {/* Messages */}
      {successMessage && (
        <div className="bg-green-900 border border-green-700 text-green-100 px-4 py-3 rounded-lg mb-6">
          {successMessage}
        </div>
      )}
      {error && (
        <div className="bg-red-900 border border-red-700 text-red-100 px-4 py-3 rounded-lg mb-6">
          {error}
        </div>
      )}

      {/* Content */}
      {loading ? (
        <div className="bg-slate-800 rounded-lg p-12 border border-slate-700 text-center">
          <div className="animate-spin text-4xl mb-4">⏳</div>
          <p className="text-slate-400">Loading personality profile...</p>
        </div>
      ) : profile ? (
        <>
          {renderArchetype()}
          {renderRadarChart()}
          {renderInsights()}
          {profile.posts_analyzed && (
            <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 text-center text-slate-400">
              📊 Analyzed {profile.posts_analyzed_count || 0} journal entries • Last updated: {new Date(profile.created_at).toLocaleDateString()}
            </div>
          )}
        </>
      ) : (
        renderEmptyState()
      )}
    </div>
  );
}
