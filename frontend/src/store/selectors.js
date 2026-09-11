export const selectCurrentComplaint = (state) => state.complaint.currentComplaint;
export const selectComplaintId = (state) => state.complaint.currentComplaint?.id || state.complaint.selectedComplaintId || null;
export const selectComplaintStatus = (state) => state.complaint.status;
export const selectRiskAssessment = (state) => state.complaint.riskAssessment;
export const selectCompleteness = (state) => state.complaint.completeness;
export const selectDuplicateDetection = (state) => state.complaint.duplicateDetection;
export const selectSummary = (state) => state.complaint.summary;
export const selectUpdatedFields = (state) => state.complaint.updatedFields || [];
export const selectQmsReferenceNumber = (state) => state.complaint.qmsReferenceNumber;

// Complaint History & Selection Selectors
export const selectComplaintList = (state) => state.complaint.complaintList || [];
export const selectComplaintListLoading = (state) => state.complaint.complaintListLoading;
export const selectComplaintListError = (state) => state.complaint.complaintListError;
export const selectComplaintListTotal = (state) => state.complaint.complaintListTotal || 0;
export const selectSelectedComplaintId = (state) => state.complaint.selectedComplaintId;
export const selectDetailLoading = (state) => state.complaint.detailLoading;
export const selectDetailError = (state) => state.complaint.detailError;

export const selectCopilotMessages = (state) => state.copilot.messages;
export const selectCopilotProcessing = (state) => state.copilot.isProcessing;
export const selectCopilotError = (state) => state.copilot.error;

export const selectUploadedFile = (state) => state.document.uploadedFile;
export const selectExtractionStatus = (state) => state.document.extractionStatus;
export const selectDocumentError = (state) => state.document.error;
