import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  messages: [],
  isProcessing: false,
  error: null,
};

export const copilotSlice = createSlice({
  name: 'copilot',
  initialState,
  reducers: {
    addMessage: (state, action) => {
      state.messages.push(action.payload);
    },
    setProcessing: (state, action) => {
      state.isProcessing = action.payload;
    },
    setError: (state, action) => {
      state.error = action.payload;
    },
    clearMessages: (state) => {
      state.messages = [];
    },
  },
});

export const { addMessage, setProcessing, setError, clearMessages } = copilotSlice.actions;
export default copilotSlice.reducer;
