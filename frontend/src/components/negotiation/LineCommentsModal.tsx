import React, { useEffect, useState } from 'react';
import { LineComment } from '../../types';
import { negotiationApi } from '../../services/negotiationApi';
import { portalApi } from '../../services/portalApi';
import { MessageSquare, Send, Lock, X } from 'lucide-react';

interface LineCommentsModalProps {
  quotationId: string;
  quotationItemId: string;
  itemName: string;
  isPortal?: boolean;
  onClose: () => void;
}

export const LineCommentsModal: React.FC<LineCommentsModalProps> = ({
  quotationId,
  quotationItemId,
  itemName,
  isPortal = false,
  onClose,
}) => {
  const [comments, setComments] = useState<LineComment[]>([]);
  const [newComment, setNewComment] = useState<string>('');
  const [isInternalOnly, setIsInternalOnly] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(true);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fetchComments = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = isPortal
        ? await portalApi.getComments(quotationId)
        : await negotiationApi.getLineComments(quotationId, quotationItemId);
      setComments(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load line comments');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchComments();
  }, [quotationId, quotationItemId]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newComment.trim()) return;

    try {
      setSubmitting(true);
      setError(null);
      if (isPortal) {
        await portalApi.createComment(quotationId, {
          quotation_item_id: quotationItemId,
          comment_text: newComment.trim(),
        });
      } else {
        await negotiationApi.createLineComment(quotationId, {
          quotation_item_id: quotationItemId,
          comment_text: newComment.trim(),
          is_internal_only: isInternalOnly,
        });
      }
      setNewComment('');
      await fetchComments();
    } catch (err: any) {
      setError(err.message || 'Failed to post comment');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full overflow-hidden shadow-2xl flex flex-col max-h-[85vh]">
        {/* Modal Header */}
        <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-850">
          <div>
            <h3 className="text-base font-semibold text-white flex items-center gap-2">
              <MessageSquare className="w-5 h-5 text-indigo-400" />
              Line Item Discussion
            </h3>
            <p className="text-xs text-slate-400 truncate max-w-sm">{itemName}</p>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Comment Stream */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {error && (
            <div className="p-3 bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs rounded-lg">
              {error}
            </div>
          )}

          {loading ? (
            <div className="text-center py-8 text-slate-400 text-sm animate-pulse">
              Loading discussion thread...
            </div>
          ) : comments.length === 0 ? (
            <div className="text-center py-10 text-slate-400 text-sm">
              No comments posted on this line item yet.
            </div>
          ) : (
            comments.map((comment) => (
              <div
                key={comment.id}
                className={`p-3.5 rounded-xl border ${
                  comment.is_internal_only
                    ? 'bg-amber-950/20 border-amber-800/40 text-amber-100'
                    : comment.author_type === 'CUSTOMER_PORTAL'
                    ? 'bg-indigo-950/30 border-indigo-800/40 text-indigo-100 ml-4'
                    : 'bg-slate-800/60 border-slate-700/60 text-slate-100 mr-4'
                }`}
              >
                <div className="flex items-center justify-between text-xs mb-1.5">
                  <span className="font-semibold text-slate-200 flex items-center gap-1.5">
                    {comment.author_name}
                    {comment.is_internal_only && (
                      <span className="inline-flex items-center gap-1 text-[10px] bg-amber-500/20 text-amber-300 px-1.5 py-0.5 rounded border border-amber-500/30 font-normal">
                        <Lock className="w-3 h-3" /> Internal Only
                      </span>
                    )}
                  </span>
                  <span className="text-[11px] text-slate-400">
                    {new Date(comment.created_at).toLocaleString()}
                  </span>
                </div>
                <p className="text-sm whitespace-pre-wrap">{comment.comment_text}</p>
              </div>
            ))
          )}
        </div>

        {/* Comment Input */}
        <form onSubmit={handleSubmit} className="p-4 border-t border-slate-800 bg-slate-900/90 space-y-3">
          {!isPortal && (
            <label className="flex items-center gap-2 text-xs text-slate-300 cursor-pointer">
              <input
                type="checkbox"
                checked={isInternalOnly}
                onChange={(e) => setIsInternalOnly(e.target.checked)}
                className="rounded border-slate-700 bg-slate-800 text-indigo-500 focus:ring-indigo-500"
              />
              <span className="flex items-center gap-1">
                <Lock className="w-3.5 h-3.5 text-amber-400" /> Make this comment internal-only (invisible to customer)
              </span>
            </label>
          )}

          <div className="flex gap-2">
            <input
              type="text"
              value={newComment}
              onChange={(e) => setNewComment(e.target.value)}
              placeholder="Type your comment..."
              className="flex-1 bg-slate-800 border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-indigo-500 placeholder-slate-500"
              disabled={submitting}
            />
            <button
              type="submit"
              disabled={submitting || !newComment.trim()}
              className="px-4 py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-sm font-semibold rounded-xl flex items-center gap-2 transition"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
