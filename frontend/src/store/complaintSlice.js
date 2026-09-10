import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  currentComplaint: null,
  riskAssessment: null,
  status: 'idle', // 'idle' | 'draft' | 'committed'
  qmsReferenceNumber: null,
  updatedFields: [],
};

export const complaintSlice = createSlice({
  name: 'complaint',
  initialState,
  reducers: {
    setComplaint: (state, action) => {
      state.currentComplaint = action.payload;
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
    resetComplaint: () => initialState,
  },
});

export const { setComplaint, setRiskAssessment, setUpdatedFields, setStatus, resetComplaint } = complaintSlice.actions;
export default complaintSlice.reducer;
