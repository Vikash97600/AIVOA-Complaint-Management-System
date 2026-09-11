import React, { useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import {
  selectCurrentComplaint,
  selectComplaintId,
  selectCompleteness,
  selectDuplicateDetection,
  selectSummary,
  selectCopilotProcessing,
} from '../store/selectors';
import {
  checkCompletenessThunk,
  detectDuplicatesThunk,
  generateSummaryThunk,
} from '../store/thunks';

export function AIInsightsPanel() {
  const dispatch = useDispatch();
  const currentComplaint = useSelector(selectCurrentComplaint);
  const complaintId = useSelector(selectComplaintId);
  const completeness = useSelector(selectCompleteness);
  const duplicateDetection = useSelector(selectDuplicateDetection);
  const summary = useSelector(selectSummary);
  const isProcessing = useSelector(selectCopilotProcessing);

  const [loadingAction, setLoadingAction] = useState(null);

  if (!currentComplaint || !complaintId) {
    return null;
  }

  const handleCheckCompleteness = async () => {
    setLoadingAction('completeness');
    try {
      await dispatch(checkCompletenessThunk(complaintId)).unwrap();
    } catch (err) {
      console.error('Failed checking completeness:', err);
    } finally {
      setLoadingAction(null);
    }
  };

  const handleDetectDuplicates = async () => {
    setLoadingAction('duplicate');
    try {
      await dispatch(detectDuplicatesThunk(complaintId)).unwrap();
    } catch (err) {
      console.error('Failed detecting duplicates:', err);
    } finally {
      setLoadingAction(null);
    }
  };

  const handleGenerateSummary = async () => {
    setLoadingAction('summary');
    try {
      await dispatch(generateSummaryThunk(complaintId)).unwrap();
    } catch (err) {
      console.error('Failed generating summary:', err);
    } finally {
      setLoadingAction(null);
    }
  };

  return (
    <div className="ai-insights-container">
      <div className="insights-header">
        <h4>AI Intelligent Complaint Assistance</h4>
        <span className="insights-pill">Bonus AI Tools</span>
      </div>

      <div className="insights-grid">
        {/* 1. Completeness Checker Card */}
        <div className="insight-card completeness-card">
          <div className="card-top-row">
            <h5>Completeness Checker</h5>
            <button
              type="button"
              className="insight-action-btn"
              onClick={handleCheckCompleteness}
              disabled={isProcessing || loadingAction === 'completeness'}
            >
              {loadingAction === 'completeness' ? 'Checking...' : 'Check Completeness'}
            </button>
          </div>

          {completeness ? (
            <div className="completeness-content">
              <div className="score-row">
                <div className="score-badge-circle">
                  <span className="score-number">{completeness.completion_score}%</span>
                </div>
                <div className="score-meta">
                  <span className={`status-label label-${completeness.status_label.toLowerCase().replace(/\s+/g, '-')}`}>
                    {completeness.status_label}
                  </span>
                  <span className="sub-hint">AI-assisted completeness assessment</span>
                </div>
              </div>

              {completeness.missing_fields && completeness.missing_fields.length > 0 && (
                <div className="missing-fields-box">
                  <label>Missing Fields:</label>
                  <div className="tags-row">
                    {completeness.missing_fields.map((f, i) => (
                      <span key={i} className="field-tag">{f}</span>
                    ))}
                  </div>
                </div>
              )}

              {completeness.recommendations && completeness.recommendations.length > 0 && (
                <ul className="recommendations-list">
                  {completeness.recommendations.map((rec, i) => (
                    <li key={i}>{rec}</li>
                  ))}
                </ul>
              )}
            </div>
          ) : (
            <p className="hint-text">Evaluate if mandatory details are filled prior to QMS submission.</p>
          )}
        </div>

        {/* 2. Duplicate Detection Card */}
        <div className="insight-card duplicate-card">
          <div className="card-top-row">
            <h5>Duplicate Complaint Detection</h5>
            <button
              type="button"
              className="insight-action-btn"
              onClick={handleDetectDuplicates}
              disabled={isProcessing || loadingAction === 'duplicate'}
            >
              {loadingAction === 'duplicate' ? 'Searching DB...' : 'Search Duplicates'}
            </button>
          </div>

          {duplicateDetection ? (
            <div className="duplicate-content">
              <div className={`duplicate-banner ${duplicateDetection.is_duplicate ? 'duplicate-warn' : 'duplicate-clean'}`}>
                <span className="dup-status-title">
                  {duplicateDetection.is_duplicate ? '⚠️ Potential Duplicate Detected' : '✓ No Duplicate Candidates Found'}
                </span>
                <p className="dup-reasoning">{duplicateDetection.summary_reasoning}</p>
              </div>

              {duplicateDetection.matches && duplicateDetection.matches.length > 0 && (
                <div className="candidate-list">
                  <label>Candidate Database Matches:</label>
                  {duplicateDetection.matches.slice(0, 3).map((match, i) => (
                    <div key={i} className="candidate-item">
                      <div className="candidate-meta">
                        <span className="cand-ref">{match.qms_reference_number || match.complaint_id.slice(0, 8)}</span>
                        <span className="cand-score">{Math.round(match.similarity_score * 100)}% Match</span>
                      </div>
                      <div className="cand-reasons">
                        {match.reasons.map((r, idx) => (
                          <span key={idx} className="reason-pill">{r}</span>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ) : (
            <p className="hint-text">Search MySQL database for potential candidate duplicates matching product or batch.</p>
          )}
        </div>

        {/* 3. Executive Complaint Summary Card */}
        <div className="insight-card summary-card">
          <div className="card-top-row">
            <h5>Executive Complaint Summary</h5>
            <button
              type="button"
              className="insight-action-btn"
              onClick={handleGenerateSummary}
              disabled={isProcessing || loadingAction === 'summary'}
            >
              {loadingAction === 'summary' ? 'Summarizing...' : 'Generate Summary'}
            </button>
          </div>

          {summary ? (
            <div className="summary-content">
              <p className="summary-paragraph">{summary.summary_text}</p>
              {summary.key_facts && summary.key_facts.length > 0 && (
                <div className="key-facts-box">
                  <label>Key Facts:</label>
                  <ul className="facts-list">
                    {summary.key_facts.map((fact, i) => (
                      <li key={i}>{fact}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ) : (
            <p className="hint-text">Generate a 2-3 sentence executive QA overview using Groq gemma2-9b-it.</p>
          )}
        </div>
      </div>
    </div>
  );
}

export default AIInsightsPanel;
