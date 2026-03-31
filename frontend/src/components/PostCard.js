import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { toggleLike, deletePost } from '../utils/api';

function formatDate(dateStr) {
  const date = new Date(dateStr);
  const now = new Date();
  const diff = Math.floor((now - date) / 1000);

  if (diff < 60) return 'Just now';
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  if (diff < 604800) return `${Math.floor(diff / 86400)}d ago`;

  return date.toLocaleDateString();
}

export default function PostCard({ post, onDeleted }) {
  const [liked, setLiked] = useState(post.liked);
  const [likeCount, setLikeCount] = useState(post.like_count);
  const [loading, setLoading] = useState(false);

  const handleToggleLike = async () => {
    setLoading(true);
    try {
      const result = await toggleLike(post.id);
      setLiked(result.liked);
      setLikeCount(result.like_count);
    } catch (error) {
      console.error('Failed to toggle like:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!window.confirm('Delete this post?')) return;

    try {
      await deletePost(post.id);
      onDeleted(post.id);
    } catch (error) {
      console.error('Failed to delete post:', error);
      alert('Failed to delete post');
    }
  };

  return (
    <Link
      to={`/post/${post.id}`}
      className="block p-4 hover:bg-slate-850 dark:hover:bg-slate-850 transition-colors cursor-pointer"
    >
      <div className="flex gap-3">
        {/* Avatar/Mood */}
        <div className="text-2xl flex-shrink-0">{post.mood}</div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          {/* Header */}
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <span className="font-bold text-slate-100 dark:text-slate-100">
                {post.author}
              </span>
              <span className="text-sm text-slate-500 dark:text-slate-500">
                {formatDate(post.created_at)}
              </span>
            </div>
            <button
              onClick={(e) => {
                e.preventDefault();
                handleDelete();
              }}
              className="p-1 rounded hover:bg-slate-700 dark:hover:bg-slate-700 text-slate-400 dark:text-slate-400 transition-colors"
              title="Delete"
            >
              🗑️
            </button>
          </div>

          {/* Content */}
          <p className="text-slate-100 dark:text-slate-100 whitespace-pre-wrap line-clamp-3">
            {post.content}
          </p>

          {/* Images */}
          {post.images && post.images.length > 0 && (
            <div className="mt-3 grid grid-cols-2 gap-2 rounded-lg overflow-hidden">
              {post.images.slice(0, 4).map((img, idx) => (
                <img
                  key={idx}
                  src={img}
                  alt="Post"
                  className="w-full h-32 object-cover"
                />
              ))}
            </div>
          )}

          {/* Engagement Stats */}
          <div className="mt-3 flex gap-4 text-sm text-slate-500 dark:text-slate-500">
            <span>{post.comment_count} comments</span>
            <span>{likeCount} likes</span>
          </div>

          {/* Engagement Buttons */}
          <div className="mt-3 flex gap-4 border-t border-slate-700 dark:border-slate-700 pt-3">
            <button
              onClick={(e) => {
                e.preventDefault();
                handleToggleLike();
              }}
              disabled={loading}
              className={`flex-1 py-1.5 rounded text-sm font-medium transition-colors ${
                liked
                  ? 'text-red-500 hover:bg-red-500/10'
                  : 'text-slate-400 dark:text-slate-400 hover:bg-slate-800 dark:hover:bg-slate-800'
              }`}
            >
              {liked ? '❤️' : '🤍'} Like
            </button>
            <button
              onClick={(e) => {
                e.preventDefault();
                // Navigation is handled by Link
              }}
              className="flex-1 py-1.5 rounded text-sm font-medium text-slate-400 dark:text-slate-400 hover:bg-slate-800 dark:hover:bg-slate-800 transition-colors"
            >
              💬 Reply
            </button>
          </div>
        </div>
      </div>
    </Link>
  );
}
