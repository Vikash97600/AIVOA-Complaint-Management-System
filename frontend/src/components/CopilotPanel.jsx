import React, { useState, useRef, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import {
  selectCopilotMessages,
  selectCopilotProcessing,
  selectCurrentComplaint,
} from '../store/selectors';
import { sendCopilotMessageThunk, uploadCopilotDocumentThunk } from '../store/thunks';

export function CopilotPanel() {
  const [inputText, setInputText] = useState('');
  const dispatch = useDispatch();
  const messages = useSelector(selectCopilotMessages);
  const isProcessing = useSelector(selectCopilotProcessing);
  const currentComplaint = useSelector(selectCurrentComplaint);
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

    const activeComplaintId = currentComplaint?.id || null;
    dispatch(sendCopilotMessageThunk({ message: userMsg, complaintId: activeComplaintId }));
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    e.target.value = '';

    const activeComplaintId = currentComplaint?.id || null;
    dispatch(uploadCopilotDocumentThunk({ file, complaintId: activeComplaintId }));
  };

  const isCommitted = currentComplaint?.status === 'COMMITTED';

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

      {isCommitted ? (
        <div className="copilot-committed-footer">
          <p className="committed-footer-text">
            🔒 <strong>Complaint Committed:</strong> This record is immutable in the QMS Ledger. New modifications or document uploads are locked.
          </p>
        </div>
      ) : (
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
            placeholder="Describe complaint or edit details..."
            disabled={isProcessing}
          />
          <button type="submit" disabled={isProcessing || !inputText.trim()}>
            Send
          </button>
        </form>
      )}
    </div>
  );
}

export default CopilotPanel;
