import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  currentComplaint: null,
  riskAssessment: null,
  completeness: null,
  duplicateDetection: null,
  summary: null,
  status: 'idle', // 'idle' | 'draft' | 'committed'
  qmsReferenceNumber: null,
  updatedFields: [],
  loading: false,
  error: null,

  // Prompt 17.1: Complaint History & Selection State
  complaintList: [],
  complaintListLoading: false,
  complaintListError: null,
  complaintListTotal: 0,
  selectedComplaintId: null,
  detailLoading: false,
  detailError: null,
};

export const complaintSlice = createSlice({
  name: 'complaint',
  initialState,
  reducers: {
    setComplaint: (state, action) => {
      state.currentComplaint = action.payload;
      if (action.payload) {
        state.status = action.payload.status ? action.payload.status.toLowerCase() : 'draft';
        state.qmsReferenceNumber = action.payload.qms_reference_number || null;
        state.selectedComplaintId = action.payload.id || null;
      }
    },
    setRiskAssessment: (state, action) => {
      state.riskAssessment = action.payload;
    },
    setCompleteness: (state, action) => {
      state.completeness = action.payload;
    },
    setDuplicateDetection: (state, action) => {
      state.duplicateDetection = action.payload;
    },
    setSummary: (state, action) => {
      state.summary = action.payload;
    },
    setUpdatedFields: (state, action) => {
      state.updatedFields = action.payload || [];
    },
    setStatus: (state, action) => {
      state.status = action.payload;
    },
    setComplaintLoading: (state, action) => {
      state.loading = action.payload;
    },
    setComplaintError: (state, action) => {
      state.error = action.payload;
    },
    setSelectedComplaintId: (state, action) => {
      state.selectedComplaintId = action.payload;
    },
    setComplaintList: (state, action) => {
      const payload = action.payload;
      if (Array.isArray(payload)) {
        state.complaintList = payload;
        state.complaintListTotal = payload.length;
      } else if (payload && Array.isArray(payload.items)) {
        state.complaintList = payload.items;
        state.complaintListTotal = payload.total ?? payload.items.length;
      } else {
        state.complaintList = [];
        state.complaintListTotal = 0;
      }
    },
    setComplaintListLoading: (state, action) => {
      state.complaintListLoading = action.payload;
    },
    setComplaintListError: (state, action) => {
      state.complaintListError = action.payload;
    },
    setDetailLoading: (state, action) => {
      state.detailLoading = action.payload;
    },
    setDetailError: (state, action) => {
      state.detailError = action.payload;
    },
    resetComplaint: (state) => {
      state.currentComplaint = null;
      state.riskAssessment = null;
      state.completeness = null;
      state.duplicateDetection = null;
      state.summary = null;
      state.status = 'idle';
      state.qmsReferenceNumber = null;
      state.updatedFields = [];
      state.loading = false;
      state.error = null;
      state.selectedComplaintId = null;
      state.detailLoading = false;
      state.detailError = null;
    },
  },
});

export const {
  setComplaint,
  setRiskAssessment,
  setCompleteness,
  setDuplicateDetection,
  setSummary,
  setUpdatedFields,
  setStatus,
  setComplaintLoading,
  setComplaintError,
  setSelectedComplaintId,
  setComplaintList,
  setComplaintListLoading,
  setComplaintListError,
  setDetailLoading,
  setDetailError,
  resetComplaint,
} = complaintSlice.actions;

export default complaintSlice.reducer;
