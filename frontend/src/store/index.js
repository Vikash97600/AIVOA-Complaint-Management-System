import { configureStore } from '@reduxjs/toolkit';
import complaintReducer from './complaintSlice';
import copilotReducer from './copilotSlice';
import documentReducer from './documentSlice';

export const store = configureStore({
  reducer: {
    complaint: complaintReducer,
    copilot: copilotReducer,
    document: documentReducer,
  },
});
