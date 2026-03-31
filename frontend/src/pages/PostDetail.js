import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import CommentSection from '../components/CommentSection';
import { fetchPost, toggleLike, deletePost } from '../utils/api';

function formatDate(dateStr) {
  return new Date(dateStr).toLocaleString();
}

export default function PostDetail() {
  const { postId } = useParams();
  const navigate = useNavigate();
  const [post, setPost] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [liked, setLiked] = useState(false);
  const [likeCount, setLikeCount] = useState(0);

  useEffect(() => {
    loadPost();
  }, [postId]);

  const loadPost = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchPost(postId);
      setPost(data);
      setLiked(data.liked);
      setLikeCount(data.like_count);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleToggleLike = async () => {
    try {
      const result = await toggleLike(postId);
      setLiked(result.liked);
      setLikeCount(result.like_count);
    } catch (error) {
      console.error('Failed to toggle like:', error);
    }
  };

  const handleDelete = async () => {
    if (!window.confirm('Delete this post?')) return;

    try {
      await deletePost(postId);
      navigate('/');
    } catch (error) {
      console.error('Failed to delete post:', error);
      alert('Failed to delete post');
    }
  };

  const handleCommentAdded = () => {
    // Reload post to get updated comment count
    loadPost();
  };

  if (loading) {
    return (
      <main className="flex-1 max-w-2xl border-l border-r border-slate-800 dark:border-slate-700 min-h-screen flex items-center justify-center">
        <div className="text-slate-400">Loading...</div>
      </main>
    );
  }

  if (error || !post) {
    return (
      <main className="flex-1 max-w-2xl border-l border-r border-slate-800 dark:border-slate-700 min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-400 mb-4">{error || 'Post not found'}</p>
          <button
            onClick={() => navigate('/')}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg"
          >
            Back to Feed
          </button>
        </div>
      </main>
    );
  }

  return (
    <main className="flex-1 max-w-2xl border-l border-r border-slate-800 dark:border-slate-700 min-h-screen">
      {/* Back Button */}
      <div className="sticky top-16 z-40 border-b border-slate-800 dark:border-slate-700 bg-slate-900/95 dark:bg-slate-900/95 backdrop-blur p-4">
        <button
          onClick={() => navigate('/')}
          className="text-blue-500 hover:text-blue-400 font-medium"
        >
          ← Back
        </button>
      </div>

      {/* Post */}
      <div className="border-b border-slate-800 dark:border-slate-700 p-4">
        <div className="flex gap-3">
          <div className="text-4xl">{post.mood}</div>
          <div className="flex-1">
            <div className="flex items-center justify-between mb-2">
              <div>
                <span className="font-bold text-slate-100 dark:text-slate-100">
                  {post.author}
                </span>
              </div>
              <button
                onClick={handleDelete}
                className="p-1 rounded hover:bg-slate-700 dark:hover:bg-slate-700 text-slate-400 dark:text-slate-400 transition-colors"
                title="Delete"
              >
                🗑️
              </button>
            </div>
            <p className="text-sm text-slate-500 dark:text-slate-500 mb-3">
              {formatDate(post.created_at)}
            </p>
            <p className="text-slate-100 dark:text-slate-100 whitespace-pre-wrap text-base leading-relaxed">
              {post.content}
            </p>

            {/* Images */}
            {post.images && post.images.length > 0 && (
              <div className="mt-4 grid grid-cols-2 gap-2 rounded-lg overflow-hidden">
                {post.images.slice(0, 4).map((img, idx) => (
                  <img
                    key={idx}
                    src={img}
                    alt="Post"
                    className="w-full h-48 object-cover"
                  />
                ))}
              </div>
            )}

            {/* Engagement */}
            <div className="mt-4 flex gap-6 text-slate-500 dark:text-slate-500 text-sm border-t border-slate-700 dark:border-slate-700 pt-4">
              <span>{post.comment_count} comments</span>
              <span>{likeCount} likes</span>
            </div>

            {/* Engagement Buttons */}
            <div className="mt-4 flex gap-4">
              <button
                onClick={handleToggleLike}
                className={`flex-1 py-2 rounded font-medium transition-colors ${
                  liked
                    ? 'text-red-500 hover:bg-red-500/10'
                    : 'text-slate-400 dark:text-slate-400 hover:bg-slate-800 dark:hover:bg-slate-800'
                }`}
              >
                {liked ? '❤️' : '🤍'} Like
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Comments */}
      <CommentSection postId={postId} onCommentAdded={handleCommentAdded} />
    </main>
  );
}
