import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  currentComplaint: null,
  riskAssessment: null,
  status: 'idle', // 'idle' | 'draft' | 'committed'
  qmsReferenceNumber: null,
  updatedFields: [],
  loading: false,
  error: null,
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
      }
    },
    setRiskAssessment: (state, action) => {
      state.riskAssessment = action.payload;
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
    resetComplaint: () => initialState,
  },
});

export const {
  setComplaint,
  setRiskAssessment,
  setUpdatedFields,
  setStatus,
  setComplaintLoading,
  setComplaintError,
  resetComplaint,
} = complaintSlice.actions;

export default complaintSlice.reducer;
