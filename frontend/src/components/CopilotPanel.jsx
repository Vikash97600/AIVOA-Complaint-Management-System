import React, { useState, useRef, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { addMessage, setProcessing, setError } from '../store/copilotSlice';
import { setComplaint, setRiskAssessment, setUpdatedFields } from '../store/complaintSlice';
import { setUploadedFile, setExtractionStatus, setDocumentError } from '../store/documentSlice';
import { sendCopilotMessage, uploadCopilotDocument } from '../services/api';

export function CopilotPanel() {
  const [inputText, setInputText] = useState('');
  const dispatch = useDispatch();
  const messages = useSelector((state) => state.copilot.messages);
  const isProcessing = useSelector((state) => state.copilot.isProcessing);
  const currentComplaint = useSelector((state) => state.complaint.currentComplaint);
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isProcessing]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!inputText.trim() || isProcessing) return;

    const userMsg = inputText.trim();
    setInputText('');

    dispatch(addMessage({ sender: 'user', content: userMsg }));
    dispatch(setProcessing(true));
    dispatch(setError(null));

    try {
      const activeComplaintId = currentComplaint?.id || null;
      const response = await sendCopilotMessage(userMsg, activeComplaintId);

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
      if (response.risk_assessment) {
        dispatch(setRiskAssessment(response.risk_assessment));
      }
      if (response.updated_fields) {
        dispatch(setUpdatedFields(response.updated_fields));
      }
    } catch (err) {
      console.error('Failed to communicate with Copilot API:', err);
      dispatch(setError('Failed to reach AIVOA Copilot API.'));
      dispatch(
        addMessage({
          sender: 'assistant',
          content: 'Sorry, I ran into a network or server issue trying to process your complaint request.',
          isError: true,
        })
      );
    } finally {
      dispatch(setProcessing(false));
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // Reset file input value so user can upload same file again if desired
    e.target.value = '';

    dispatch(addMessage({ sender: 'user', content: `Uploaded document: ${file.name}` }));
    dispatch(setProcessing(true));
    dispatch(setError(null));
    dispatch(setExtractionStatus('uploading'));
    dispatch(setDocumentError(null));

    try {
      const activeComplaintId = currentComplaint?.id || null;
      const response = await uploadCopilotDocument(file, activeComplaintId);

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
        return;
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
      if (response.risk_assessment) {
        dispatch(setRiskAssessment(response.risk_assessment));
      }
      if (response.document) {
        dispatch(setUploadedFile(response.document));
      }
      if (response.updated_fields) {
        dispatch(setUpdatedFields(response.updated_fields));
      }

      dispatch(setExtractionStatus('extracted'));
    } catch (err) {
      console.error('Failed to process document upload:', err);
      dispatch(setExtractionStatus('error'));
      dispatch(setDocumentError(err.message || 'Document upload failed.'));
      dispatch(
        addMessage({
          sender: 'assistant',
          content: `Document processing failed: ${err.message || 'Unable to process file.'}`,
          isError: true,
        })
      );
    } finally {
      dispatch(setProcessing(false));
    }
  };

  return (
    <div className="copilot-panel-container">
      <div className="copilot-header">
        <h3>AIVOA Copilot</h3>
        <span className="ai-badge">Groq / gemma2-9b-it</span>
      </div>

      <div className="messages-list">
        {messages.length === 0 ? (
          <div className="welcome-chat">
            <p className="welcome-title">Welcome to AIVOA AI Copilot</p>
            <p className="welcome-desc">
              Describe a complaint in plain text or upload a complaint document (PDF, EML, TXT) to populate details automatically.
            </p>
            <div className="sample-prompts">
              <button
                type="button"
                onClick={() =>
                  setInputText(
                    'Apollo Pharmacy reported discolored capsules in Amoxicillin Capsules 500 mg. Batch AMX240602, 12 capsules, manufacturing March 2026, expiry February 2028.'
                  )
                }
              >
                "Apollo Pharmacy reported discolored capsules..."
              </button>
            </div>
          </div>
        ) : (
          messages.map((msg, index) => (
            <div
              key={index}
              className={`chat-bubble ${msg.sender === 'user' ? 'user-bubble' : 'assistant-bubble'} ${
                msg.isError ? 'error-bubble' : ''
              }`}
            >
              <div className="bubble-header">
                <span className="sender-name">{msg.sender === 'user' ? 'User' : 'AIVOA Copilot'}</span>
                {msg.intent && <span className="intent-tag">{msg.intent}</span>}
              </div>
              <div className="bubble-body">{msg.content}</div>
            </div>
          ))
        )}

        {isProcessing && (
          <div className="chat-bubble assistant-bubble loading-bubble">
            <span className="loading-dots">AIVOA Copilot is processing complaint details...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSubmit} className="copilot-input-form">
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileUpload}
          accept=".pdf,.txt,.eml"
          style={{ display: 'none' }}
        />
        <button
          type="button"
          className="doc-upload-btn"
          onClick={() => fileInputRef.current?.click()}
          disabled={isProcessing}
          title="Upload Complaint Document (PDF, EML, TXT)"
        >
          📎 Document
        </button>
        <input
          type="text"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          placeholder="Describe complaint or upload document..."
          disabled={isProcessing}
        />
        <button type="submit" disabled={isProcessing || !inputText.trim()}>
          Send
        </button>
      </form>
    </div>
  );
}

export default CopilotPanel;
