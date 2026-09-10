import React, { useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { setComplaint } from '../../store/complaintSlice';
import { addMessage } from '../../store/copilotSlice';
import { commitComplaint } from '../../services/api';

export function CommitQMSButton() {
  const dispatch = useDispatch();
  const currentComplaint = useSelector((state) => state.complaint.currentComplaint);
  const [isCommitting, setIsCommitting] = useState(false);
  const [showConfirmModal, setShowConfirmModal] = useState(false);

  if (!currentComplaint || !currentComplaint.id) {
    return null;
  }

  const isCommitted = currentComplaint.status === 'COMMITTED';
  const qmsRefNumber = currentComplaint.qms_reference_number;

  const handleCommitConfirm = async () => {
    setShowConfirmModal(false);
    setIsCommitting(true);

    try {
      const updatedComplaint = await commitComplaint(currentComplaint.id);
      dispatch(setComplaint(updatedComplaint));
      
      dispatch(
        addMessage({
          sender: 'assistant',
          content: `Complaint formally committed to the QMS Ledger! Assigned Reference Number: ${updatedComplaint.qms_reference_number || 'QMS-2026-001'}.`,
          intent: 'QMS_COMMIT',
        })
      );
    } catch (err) {
      console.error('Failed to commit complaint to QMS:', err);
      dispatch(
        addMessage({
          sender: 'assistant',
          content: `Failed to commit complaint to QMS Ledger: ${err.message}`,
          isError: true,
        })
      );
    } finally {
      setIsCommitting(false);
    }
  };

  return (
    <div className="qms-commit-wrapper">
      {isCommitted ? (
        <div className="qms-committed-banner">
          <div className="committed-status-header">
            <span className="qms-badge-committed">✓ COMMITTED TO QMS LEDGER</span>
          </div>
          {qmsRefNumber && (
            <div className="qms-ref-display">
              <label>QMS Reference Number:</label>
              <span className="qms-ref-code">{qmsRefNumber}</span>
            </div>
          )}
        </div>
      ) : (
        <div className="qms-action-box">
          <button
            type="button"
            className="commit-qms-btn"
            onClick={() => setShowConfirmModal(true)}
            disabled={isCommitting}
          >
            {isCommitting ? 'Freezing Payload to Ledger...' : '🔒 Commit to QMS Ledger'}
          </button>
          <span className="commit-hint">
            Freezes current complaint data & AI risk assessment into immutable QMS ledger snapshot.
          </span>
        </div>
      )}

      {showConfirmModal && (
        <div className="modal-backdrop">
          <div className="confirm-modal-card">
            <h4>Commit Complaint to QMS Ledger</h4>
            <p>
              Are you sure you want to commit this complaint to the QMS Ledger?
            </p>
            <p className="modal-subtext">
              This action will assign a permanent QMS Reference Number, freeze the extracted payload and AI risk assessment snapshot, and transition status from DRAFT to COMMITTED.
            </p>
            <div className="modal-actions">
              <button
                type="button"
                className="modal-btn-cancel"
                onClick={() => setShowConfirmModal(false)}
              >
                Cancel
              </button>
              <button
                type="button"
                className="modal-btn-confirm"
                onClick={handleCommitConfirm}
              >
                Confirm Commit
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default CommitQMSButton;
