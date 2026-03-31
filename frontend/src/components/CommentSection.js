import React, { useState } from 'react';
import { addComment, deleteComment } from '../utils/api';

function formatDate(dateStr) {
  const date = new Date(dateStr);
  const now = new Date();
  const diff = Math.floor((now - date) / 1000);

  if (diff < 60) return 'Just now';
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;

  return date.toLocaleDateString();
}

export default function CommentSection({ postId, onCommentAdded }) {
  const [comments, setComments] = useState([]);
  const [newComment, setNewComment] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadingComments, setLoadingComments] = useState(false);

  React.useEffect(() => {
    // Comments are loaded from the post data in parent
    // This component assumes comments are passed via post.comments
  }, [postId]);

  const handleAddComment = async (e) => {
    e.preventDefault();
    if (!newComment.trim()) return;

    setLoading(true);
    try {
      const comment = await addComment(postId, {
        author: 'You',
        text: newComment.trim(),
      });
      setComments([comment, ...comments]);
      setNewComment('');
      onCommentAdded();
    } catch (error) {
      console.error('Failed to add comment:', error);
      alert('Failed to add comment');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteComment = async (commentId) => {
    if (!window.confirm('Delete this comment?')) return;

    try {
      await deleteComment(commentId);
      setComments(comments.filter(c => c.id !== commentId));
      onCommentAdded();
    } catch (error) {
      console.error('Failed to delete comment:', error);
      alert('Failed to delete comment');
    }
  };

  return (
    <div className="p-4">
      {/* Comment Input */}
      <form onSubmit={handleAddComment} className="mb-6">
        <div className="flex gap-3">
          <div className="text-xl flex-shrink-0">💬</div>
          <div className="flex-1">
            <textarea
              value={newComment}
              onChange={(e) => setNewComment(e.target.value)}
              placeholder="Add a comment..."
              className="w-full bg-slate-800 dark:bg-slate-800 text-slate-100 dark:text-slate-100 rounded-lg px-3 py-2 placeholder-slate-500 dark:placeholder-slate-500 border border-slate-700 dark:border-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none min-h-16"
            />
            <div className="mt-2 flex justify-end">
              <button
                type="submit"
                disabled={!newComment.trim() || loading}
                className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded font-medium text-sm transition-colors"
              >
                {loading ? 'Posting...' : 'Comment'}
              </button>
            </div>
          </div>
        </div>
      </form>

      {/* Comments List */}
      <div className="space-y-4">
        {comments.length === 0 ? (
          <p className="text-slate-500 dark:text-slate-500 text-sm text-center py-4">
            No comments yet. Be the first!
          </p>
        ) : (
          comments.map((comment) => (
            <div key={comment.id} className="flex gap-3 pb-4 border-b border-slate-800 dark:border-slate-700">
              <div className="text-lg flex-shrink-0">👤</div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between mb-1">
                  <span className="font-bold text-slate-100 dark:text-slate-100 text-sm">
                    {comment.author}
                  </span>
                  <span className="text-xs text-slate-500 dark:text-slate-500">
                    {formatDate(comment.created_at)}
                  </span>
                </div>
                <p className="text-slate-300 dark:text-slate-300 text-sm break-words">
                  {comment.text}
                </p>
                <button
                  onClick={() => handleDeleteComment(comment.id)}
                  className="mt-1 text-xs text-slate-500 dark:text-slate-500 hover:text-red-400 transition-colors"
                >
                  Delete
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
