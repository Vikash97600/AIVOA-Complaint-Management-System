import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  uploadedFile: null,
  extractionStatus: 'idle', // 'idle' | 'uploading' | 'extracted' | 'error'
  error: null,
};

export const documentSlice = createSlice({
  name: 'document',
  initialState,
  reducers: {
    setUploadedFile: (state, action) => {
      state.uploadedFile = action.payload;
    },
    setExtractionStatus: (state, action) => {
      state.extractionStatus = action.payload;
    },
    setDocumentError: (state, action) => {
      state.error = action.payload;
    },
  },
});

export const { setUploadedFile, setExtractionStatus, setDocumentError } = documentSlice.actions;
export default documentSlice.reducer;
