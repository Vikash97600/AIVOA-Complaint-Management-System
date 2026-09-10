import { createAsyncThunk } from '@reduxjs/toolkit';
import { setComplaint, setRiskAssessment, setUpdatedFields, resetComplaint } from './complaintSlice';
import { addMessage, setProcessing, setError, clearMessages } from './copilotSlice';
import { setUploadedFile, setExtractionStatus, setDocumentError, resetDocumentState } from './documentSlice';
import { sendCopilotMessage, uploadCopilotDocument, commitComplaint } from '../services/api';

export const sendCopilotMessageThunk = createAsyncThunk(
  'copilot/sendMessage',
  async ({ message, complaintId }, { dispatch }) => {
    dispatch(addMessage({ sender: 'user', content: message }));
    dispatch(setProcessing(true));
    dispatch(setError(null));

    try {
      const response = await sendCopilotMessage(message, complaintId);

      dispatch(
        addMessage({
          sender: 'assistant',
          content: response.message,
          intent: response.intent,
        })
      );

      if (response.complaint) {
        dispatch(setComplaint(response.complaint));
      }
      if (response.risk_assessment !== undefined) {
        dispatch(setRiskAssessment(response.risk_assessment));
      }
      if (response.updated_fields) {
        dispatch(setUpdatedFields(response.updated_fields));
      }

      return response;
    } catch (err) {
      console.error('Failed in sendCopilotMessageThunk:', err);
      dispatch(setError(err.message || 'Failed to reach AIVOA Copilot API.'));
      dispatch(
        addMessage({
          sender: 'assistant',
          content: `Sorry, I ran into an issue processing your request: ${err.message}`,
          isError: true,
        })
      );
      throw err;
    } finally {
      dispatch(setProcessing(false));
    }
  }
);

export const uploadCopilotDocumentThunk = createAsyncThunk(
  'document/upload',
  async ({ file, complaintId }, { dispatch }) => {
    dispatch(addMessage({ sender: 'user', content: `Uploaded document: ${file.name}` }));
    dispatch(setProcessing(true));
    dispatch(setError(null));
    dispatch(setExtractionStatus('uploading'));
    dispatch(setDocumentError(null));

    try {
      const response = await uploadCopilotDocument(file, complaintId);

      if (!response.success) {
        dispatch(setExtractionStatus('error'));
        dispatch(setDocumentError(response.error || response.message));
        dispatch(
          addMessage({
            sender: 'assistant',
            content: response.message || 'Failed to extract text from document.',
            isError: true,
          })
        );
        return response;
      }

      dispatch(
        addMessage({
          sender: 'assistant',
          content: response.message,
          intent: response.intent,
        })
      );

      if (response.complaint) {
        dispatch(setComplaint(response.complaint));
      }
      if (response.risk_assessment !== undefined) {
        dispatch(setRiskAssessment(response.risk_assessment));
      }
      if (response.document) {
        dispatch(setUploadedFile(response.document));
      }
      if (response.updated_fields) {
        dispatch(setUpdatedFields(response.updated_fields));
      }

      dispatch(setExtractionStatus('extracted'));
      return response;
    } catch (err) {
      console.error('Failed in uploadCopilotDocumentThunk:', err);
      dispatch(setExtractionStatus('error'));
      dispatch(setDocumentError(err.message || 'Document upload failed.'));
      dispatch(
        addMessage({
          sender: 'assistant',
          content: `Document processing failed: ${err.message || 'Unable to process file.'}`,
          isError: true,
        })
      );
      throw err;
    } finally {
      dispatch(setProcessing(false));
    }
  }
);

export const commitComplaintThunk = createAsyncThunk(
  'complaint/commit',
  async (complaintId, { dispatch }) => {
    dispatch(setProcessing(true));
    try {
      const updatedComplaint = await commitComplaint(complaintId);
      dispatch(setComplaint(updatedComplaint));

      dispatch(
        addMessage({
          sender: 'assistant',
          content: `Complaint formally committed to the QMS Ledger! Assigned Reference Number: ${updatedComplaint.qms_reference_number || 'QMS-2026-001'}.`,
          intent: 'QMS_COMMIT',
        })
      );
      return updatedComplaint;
    } catch (err) {
      console.error('Failed in commitComplaintThunk:', err);
      dispatch(
        addMessage({
          sender: 'assistant',
          content: `Failed to commit complaint to QMS Ledger: ${err.message}`,
          isError: true,
        })
      );
      throw err;
    } finally {
      dispatch(setProcessing(false));
    }
  }
);

export const clearWorkspaceThunk = createAsyncThunk(
  'workspace/clear',
  async (_, { dispatch }) => {
    dispatch(resetComplaint());
    dispatch(clearMessages());
    dispatch(resetDocumentState());
  }
);
