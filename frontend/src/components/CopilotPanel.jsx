import React, { useState, useRef, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { addMessage, setProcessing, setError } from '../store/copilotSlice';
import { setComplaint, setRiskAssessment, setUpdatedFields } from '../store/complaintSlice';
import { sendCopilotMessage } from '../services/api';

export function CopilotPanel() {
  const [inputText, setInputText] = useState('');
  const dispatch = useDispatch();
  const messages = useSelector((state) => state.copilot.messages);
  const isProcessing = useSelector((state) => state.copilot.isProcessing);
  const currentComplaint = useSelector((state) => state.complaint.currentComplaint);
  const messagesEndRef = useRef(null);

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

    // Add user message to chat state
    dispatch(addMessage({ sender: 'user', content: userMsg }));
    dispatch(setProcessing(true));
    dispatch(setError(null));

    try {
      const activeComplaintId = currentComplaint?.id || null;
      const response = await sendCopilotMessage(userMsg, activeComplaintId);

      // Add assistant response message to chat state
      dispatch(
        addMessage({
          sender: 'assistant',
          content: response.message,
          intent: response.intent,
        })
      );

      // If backend returned a structured complaint payload, update Redux complaint form state!
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
              Describe a customer complaint in plain text to log it automatically.
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
          type="text"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          placeholder="Describe complaint (e.g. Apollo Pharmacy reported discolored capsules...)"
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
