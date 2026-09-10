import React from 'react';
import { useSelector } from 'react-redux';
import { RiskAssessmentCard } from './RiskAssessmentCard';
import { CommitQMSButton } from './qms/CommitQMSButton';

export function ComplaintForm() {
  const currentComplaint = useSelector((state) => state.complaint.currentComplaint);
  const updatedFields = useSelector((state) => state.complaint.updatedFields) || [];

  const getFieldClass = (fieldName) => {
    return updatedFields.includes(fieldName) ? 'form-field updated-field' : 'form-field';
  };

  if (!currentComplaint) {
    return (
      <div className="complaint-form-container empty-state">
        <div className="empty-state-card">
          <h3>Log Customer Complaint</h3>
          <p className="hint-text">
            No active complaint record. Describe a customer complaint in the Copilot chat or upload a complaint document to auto-populate this form.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="complaint-form-container">
      <div className="form-header">
        <div className="title-row">
          <h3>Log Customer Complaint</h3>
          {currentComplaint.qms_reference_number && (
            <span className="qms-ref-pill">{currentComplaint.qms_reference_number}</span>
          )}
        </div>
        <span className={`status-tag status-${currentComplaint.status?.toLowerCase() || 'draft'}`}>
          {currentComplaint.status || 'DRAFT'}
        </span>
      </div>

      {currentComplaint.id && (
        <div className="form-row meta-row">
          <label>Complaint ID:</label>
          <span className="meta-value">{currentComplaint.id}</span>
        </div>
      )}

      <div className="form-section">
        <h4>Customer & Source Info</h4>
        <div className="form-grid">
          <div className={getFieldClass('customer_name')}>
            <label>Customer Name</label>
            <input type="text" value={currentComplaint.customer_name || ''} readOnly placeholder="Not provided" />
          </div>
          <div className={getFieldClass('complaint_source')}>
            <label>Complaint Source</label>
            <input type="text" value={currentComplaint.complaint_source || ''} readOnly placeholder="Not provided" />
          </div>
        </div>
      </div>

      <div className="form-section">
        <h4>Product & Batch Identification</h4>
        <div className="form-grid">
          <div className={getFieldClass('product_name')}>
            <label>Product Name</label>
            <input type="text" value={currentComplaint.product_name || ''} readOnly placeholder="Not provided" />
          </div>
          <div className={getFieldClass('strength_grade')}>
            <label>Strength / Grade</label>
            <input type="text" value={currentComplaint.strength_grade || ''} readOnly placeholder="Not provided" />
          </div>
          <div className={getFieldClass('batch_number')}>
            <label>Batch / Lot Number</label>
            <input type="text" value={currentComplaint.batch_number || ''} readOnly placeholder="Not provided" />
          </div>
          <div className={getFieldClass('affected_quantity')}>
            <label>Affected Quantity</label>
            <input type="text" value={currentComplaint.affected_quantity || ''} readOnly placeholder="Not provided" />
          </div>
          <div className={getFieldClass('manufacturing_date')}>
            <label>Manufacturing Date</label>
            <input type="text" value={currentComplaint.manufacturing_date || ''} readOnly placeholder="Not provided" />
          </div>
          <div className={getFieldClass('expiry_date')}>
            <label>Expiry Date</label>
            <input type="text" value={currentComplaint.expiry_date || ''} readOnly placeholder="Not provided" />
          </div>
        </div>
      </div>

      <div className="form-section">
        <h4>Defect & Category Analysis</h4>
        <div className="form-grid">
          <div className={getFieldClass('complaint_category')}>
            <label>Complaint Category</label>
            <input type="text" value={currentComplaint.complaint_category || ''} readOnly placeholder="Not provided" />
          </div>
          <div className={getFieldClass('defect_type')}>
            <label>Defect Type</label>
            <input type="text" value={currentComplaint.defect_type || ''} readOnly placeholder="Not provided" />
          </div>
        </div>
        <div className={getFieldClass('complaint_description')}>
          <label>Complaint Description</label>
          <textarea rows="3" value={currentComplaint.complaint_description || ''} readOnly placeholder="Not provided" />
        </div>
      </div>

      <div className="form-section risk-section-wrapper">
        <RiskAssessmentCard />
      </div>

      <div className="form-section qms-section-wrapper">
        <CommitQMSButton />
      </div>
    </div>
  );
}

export default ComplaintForm;
