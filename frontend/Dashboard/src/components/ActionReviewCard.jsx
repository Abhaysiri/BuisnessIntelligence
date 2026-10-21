import React, { useState } from 'react';
import { CheckCircle2, XCircle, AlertTriangle, MessageSquare, ShieldCheck, Clock } from 'lucide-react';

export default function ActionReviewCard({ recommendation, userRole = 'Analyst' }) {
  const [status, setStatus] = useState(recommendation.status || 'pending'); // 'pending' | 'approved' | 'rejected' | 'changes_requested'
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showCommentBox, setShowCommentBox] = useState(false);
  const [commentText, setCommentText] = useState('');
  const [decisionNote, setDecisionNote] = useState('');

  const recId = recommendation.recommendation_id || recommendation.id || 'rec-default';
  const actionTitle = recommendation.action || 'Recommended Operational Action';
  const rationale = recommendation.rationale || 'Mitigate identified KPI variance.';
  const ownerRole = recommendation.owner_role || 'Operations Lead';
  const decisionRight = recommendation.decision_right || 'REQUIRES_HUMAN_REVIEW';

  const isHumanReviewRequired = 
    decisionRight.toUpperCase().includes('HUMAN') || 
    decisionRight.toUpperCase().includes('REVIEW');

  const handleDecision = async (decision) => {
    setIsSubmitting(true);
    try {
      const resp = await fetch(`http://127.0.0.1:8000/api/v1/human-decisions/${encodeURIComponent(recId)}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          decision: decision,
          comment: commentText || (decision === 'approve' ? 'Approved in review' : 'Rejected in review'),
          user_id: userRole || 'analyst_user'
        })
      });

      if (resp.ok) {
        if (decision === 'approve') setStatus('approved');
        else if (decision === 'reject') setStatus('rejected');
        else setStatus('changes_requested');
        setDecisionNote(commentText);
        setShowCommentBox(false);
      } else {
        const err = await resp.text();
        console.error('Decision recording failed:', err);
      }
    } catch (e) {
      console.error('Error recording human decision:', e);
      // Fallback optimistic update
      if (decision === 'approve') setStatus('approved');
      else if (decision === 'reject') setStatus('rejected');
      else setStatus('changes_requested');
      setShowCommentBox(false);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="mt-3 p-4 bg-slate-50 border border-slate-200 rounded-xl transition-all">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2">
          <ShieldCheck size={18} className="text-blue-600 shrink-0" />
          <span className="text-xs font-bold uppercase tracking-wider text-slate-700">
            Governed Action Review
          </span>
          <span className={`text-[11px] font-semibold px-2 py-0.5 rounded-full ${
            isHumanReviewRequired ? 'bg-amber-100 text-amber-800' : 'bg-emerald-100 text-emerald-800'
          }`}>
            {decisionRight}
          </span>
        </div>

        {status === 'approved' && (
          <span className="inline-flex items-center gap-1 text-xs font-semibold text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200">
            <CheckCircle2 size={13} /> Approved by {userRole}
          </span>
        )}
        {status === 'rejected' && (
          <span className="inline-flex items-center gap-1 text-xs font-semibold text-rose-700 bg-rose-50 px-2.5 py-1 rounded-full border border-rose-200">
            <XCircle size={13} /> Rejected by {userRole}
          </span>
        )}
        {status === 'changes_requested' && (
          <span className="inline-flex items-center gap-1 text-xs font-semibold text-amber-700 bg-amber-50 px-2.5 py-1 rounded-full border border-amber-200">
            <AlertTriangle size={13} /> Changes Requested
          </span>
        )}
        {status === 'pending' && (
          <span className="inline-flex items-center gap-1 text-xs font-medium text-slate-500">
            <Clock size={13} /> Pending Review
          </span>
        )}
      </div>

      <div className="mt-2.5">
        <h4 className="text-sm font-semibold text-slate-900">{actionTitle}</h4>
        <p className="text-xs text-slate-600 mt-1 leading-relaxed">{rationale}</p>
        <div className="flex items-center gap-4 mt-2 text-[11px] text-slate-500">
          <span>Assigned Owner: <strong className="text-slate-700">{ownerRole}</strong></span>
          {recommendation.expected_impact && (
            <span>Expected Impact: <strong className="text-slate-700">{JSON.stringify(recommendation.expected_impact)}</strong></span>
          )}
        </div>
      </div>

      {status === 'pending' && (
        <div className="mt-4 pt-3 border-t border-slate-200 flex flex-col gap-2">
          {showCommentBox && (
            <div className="mb-2">
              <textarea
                value={commentText}
                onChange={(e) => setCommentText(e.target.value)}
                placeholder="Add reviewer notes or requested modifications..."
                className="w-full text-xs bg-white border border-slate-300 rounded-lg p-2.5 focus:outline-none focus:ring-1 focus:ring-blue-500 resize-none text-slate-800"
                rows="2"
              />
            </div>
          )}

          <div className="flex items-center justify-end gap-2">
            {!showCommentBox && (
              <button
                type="button"
                onClick={() => setShowCommentBox(true)}
                className="text-xs text-slate-600 hover:text-slate-800 font-medium px-2.5 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-100 transition-colors cursor-pointer flex items-center gap-1"
              >
                <MessageSquare size={13} /> Notes
              </button>
            )}

            <button
              type="button"
              disabled={isSubmitting}
              onClick={() => handleDecision('request_changes')}
              className="text-xs font-semibold text-amber-700 bg-amber-50 hover:bg-amber-100 border border-amber-300 px-3 py-1.5 rounded-lg transition-colors cursor-pointer disabled:opacity-50"
            >
              Modify
            </button>

            <button
              type="button"
              disabled={isSubmitting}
              onClick={() => handleDecision('reject')}
              className="text-xs font-semibold text-rose-700 bg-rose-50 hover:bg-rose-100 border border-rose-300 px-3 py-1.5 rounded-lg transition-colors cursor-pointer disabled:opacity-50"
            >
              Reject
            </button>

            <button
              type="button"
              disabled={isSubmitting}
              onClick={() => handleDecision('approve')}
              className="text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 px-3 py-1.5 rounded-lg transition-colors cursor-pointer shadow-xs disabled:opacity-50"
            >
              Approve Action
            </button>
          </div>
        </div>
      )}

      {decisionNote && status !== 'pending' && (
        <div className="mt-3 pt-2 border-t border-slate-200 text-xs text-slate-500 italic">
          Review Note: "{decisionNote}"
        </div>
      )}
    </div>
  );
}
