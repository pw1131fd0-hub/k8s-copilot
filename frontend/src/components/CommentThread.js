import React, { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { useCommentUpdates } from '../hooks/useWebSocket';
import {
  getCollaborationComments,
  addCollaborationComment,
  deleteCollaborationComment,
  updateComment,
} from '../utils/api';

export default function CommentThread({ postId, onCommentAdded }) {
  const { t } = useTranslation();
  const [comments, setComments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [newComment, setNewComment] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  // Handle real-time comment updates from WebSocket
  const handleNewComment = useCallback((data) => {
    console.log('Real-time comment received:', data);
    const newCommentData = {
      id: data.comment_id,
      post_id: data.post_id,
      author_id: data.author_id,
      content: data.content,
      created_at: data.timestamp,
      is_suggestion: false,
    };
    setComments(prev => [...prev, newCommentData]);
  }, []);

  const handleCommentUpdated = useCallback((data) => {
    console.log('Comment updated:', data);
    setComments(prev =>
      prev.map(c =>
        c.id === data.comment_id
          ? { ...c, content: data.content, updated_at: data.updated_at }
          : c
      )
    );
  }, []);

  const handleCommentDeleted = useCallback((data) => {
    console.log('Comment deleted:', data);
    setComments(prev => prev.filter(c => c.id !== data.comment_id));
  }, []);

  // Subscribe to real-time comment updates
  useCommentUpdates(
    postId,
    handleNewComment,
    handleCommentUpdated,
    handleCommentDeleted
  );

  useEffect(() => {
    loadComments();
  }, [postId]);

  const loadComments = async () => {
    try {
      setLoading(true);
      const data = await getCollaborationComments(postId);
      setComments(Array.isArray(data) ? data : data.comments || []);
    } catch (err) {
      console.error('Failed to load comments:', err);
      setError(t('commentThread.loadError') || 'Failed to load comments');
    } finally {
      setLoading(false);
    }
  };

  const handleAddComment = async () => {
    if (!newComment.trim()) {
      setError(t('commentThread.emptyComment') || 'Comment cannot be empty');
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      const comment = await addCollaborationComment(postId, {
        content: newComment,
        is_suggestion: false,
      });

      setComments([...comments, comment]);
      setNewComment('');
      onCommentAdded?.();
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteComment = async (commentId) => {
    if (!window.confirm(t('commentThread.confirmDelete') || 'Delete this comment?')) {
      return;
    }

    try {
      await deleteCollaborationComment(commentId);
      setComments(comments.filter(c => c.id !== commentId));
    } catch (err) {
      setError(err.message);
    }
  };

  const handleAcceptSuggestion = async (commentId) => {
    try {
      await updateComment(commentId, 'accepted');
      setComments(
        comments.map(c =>
          c.id === commentId ? { ...c, status: 'accepted' } : c
        )
      );
    } catch (err) {
      setError(err.message);
    }
  };

  if (loading) {
    return (
      <div className="p-4 text-center text-slate-400 dark:text-slate-400">
        {t('common.loading') || 'Loading...'}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-bold text-slate-100 dark:text-slate-100">
        {t('commentThread.title') || 'Collaboration Comments'}
      </h3>

      {error && (
        <div className="p-3 bg-red-900 text-red-100 rounded">
          {error}
        </div>
      )}

      {/* Comments list */}
      <div className="space-y-3 max-h-80 overflow-y-auto">
        {comments.length === 0 ? (
          <div className="text-center text-slate-400 dark:text-slate-400 py-6">
            {t('commentThread.noComments') || 'No comments yet'}
          </div>
        ) : (
          comments.map(comment => (
            <div
              key={comment.id}
              className={`p-3 rounded-lg border-l-4 ${
                comment.is_suggestion
                  ? 'bg-slate-750 dark:bg-slate-750 border-l-amber-500'
                  : 'bg-slate-750 dark:bg-slate-750 border-l-blue-500'
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-slate-100 dark:text-slate-100">
                      {comment.author_id || 'Anonymous'}
                    </span>
                    {comment.is_suggestion && (
                      <span className="text-xs bg-amber-900 text-amber-100 px-2 py-1 rounded">
                        {t('commentThread.suggestion') || 'Suggestion'}
                      </span>
                    )}
                    {comment.status && (
                      <span
                        className={`text-xs px-2 py-1 rounded ${
                          comment.status === 'accepted'
                            ? 'bg-green-900 text-green-100'
                            : 'bg-slate-700 text-slate-300 dark:bg-slate-700 dark:text-slate-300'
                        }`}
                      >
                        {comment.status}
                      </span>
                    )}
                  </div>
                  <p className="text-slate-200 dark:text-slate-200 mt-2">{comment.content}</p>
                </div>
                <button
                  onClick={() => handleDeleteComment(comment.id)}
                  className="ml-2 p-1 text-slate-400 dark:text-slate-400 hover:text-red-400 dark:hover:text-red-400 transition-colors"
                  title={t('common.delete') || 'Delete'}
                >
                  🗑️
                </button>
              </div>

              {comment.is_suggestion && comment.status !== 'accepted' && (
                <button
                  onClick={() => handleAcceptSuggestion(comment.id)}
                  className="mt-2 px-3 py-1 bg-green-600 dark:bg-green-600 text-white text-sm rounded hover:bg-green-700 dark:hover:bg-green-700 transition-colors"
                >
                  {t('commentThread.accept') || 'Accept Suggestion'}
                </button>
              )}
            </div>
          ))
        )}
      </div>

      {/* New comment input */}
      <div className="border-t border-slate-700 dark:border-slate-700 pt-4">
        <textarea
          value={newComment}
          onChange={(e) => setNewComment(e.target.value)}
          placeholder={t('commentThread.placeholder') || 'Add a comment...'}
          className="w-full px-3 py-2 bg-slate-700 dark:bg-slate-700 text-slate-100 dark:text-slate-100 rounded border border-slate-600 dark:border-slate-600 focus:outline-none focus:border-blue-500 dark:focus:border-blue-500 resize-none h-20"
        />
        <button
          onClick={handleAddComment}
          disabled={submitting}
          className="mt-2 px-4 py-2 bg-blue-600 dark:bg-blue-600 text-white rounded hover:bg-blue-700 dark:hover:bg-blue-700 disabled:opacity-50 transition-colors"
        >
          {submitting ? (t('common.loading') || 'Posting...') : (t('commentThread.post') || 'Post Comment')}
        </button>
      </div>
    </div>
  );
}
