import React from 'react';
import { useSelector } from 'react-redux';

export function RiskAssessmentCard() {
  const riskAssessment = useSelector((state) => state.complaint.riskAssessment);

  if (!riskAssessment) {
    return (
      <div className="risk-card-container empty-risk">
        <div className="card-header">
          <h4>AI Risk Triage Assessment</h4>
          <span className="disclaimer-tag">QA Review Required</span>
        </div>
        <p className="hint-text">
          Preliminary quality risk triage will be generated automatically once complaint details are logged.
        </p>
      </div>
    );
  }

  const severity = riskAssessment.severity_suggested || riskAssessment.severitySuggested || 'MEDIUM';
  const category = riskAssessment.complaint_category || riskAssessment.complaintCategory || 'Product Defect';
  const nextAction = riskAssessment.suggested_next_action || riskAssessment.suggestedNextAction || 'Route to QA Investigation';
  const details = riskAssessment.risk_details || riskAssessment.riskDetails || 'No details provided';
  const requiresQuarantine = Boolean(
    riskAssessment.requires_quarantine !== undefined
      ? riskAssessment.requires_quarantine
      : riskAssessment.requiresQuarantine
  );

  return (
    <div className="risk-card-container">
      <div className="card-header">
        <h4>AI Risk Triage Assessment</h4>
        <span className="disclaimer-tag">AI-assisted preliminary assessment — QA review required</span>
      </div>

      <div className="risk-grid">
        <div className="risk-item">
          <label>Suggested Severity</label>
          <span className={`severity-badge severity-${severity.toLowerCase()}`}>
            {severity}
          </span>
        </div>

        <div className="risk-item">
          <label>Quarantine Recommendation</label>
          <span className={`quarantine-badge ${requiresQuarantine ? 'quarantine-yes' : 'quarantine-no'}`}>
            {requiresQuarantine ? 'QUARANTINE RECOMMENDED' : 'NO QUARANTINE NEEDED'}
          </span>
        </div>

        <div className="risk-item full-width">
          <label>Risk Category</label>
          <span className="risk-value">{category}</span>
        </div>

        <div className="risk-item full-width">
          <label>Suggested Next Action</label>
          <div className="action-box">{nextAction}</div>
        </div>

        <div className="risk-item full-width">
          <label>Technical Risk Rationale</label>
          <p className="details-text">{details}</p>
        </div>
      </div>
    </div>
  );
}

export default RiskAssessmentCard;
