import React from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { selectCurrentComplaint } from '../../store/selectors';
import { clearWorkspaceThunk } from '../../store/thunks';

export function AppHeader() {
  const dispatch = useDispatch();
  const currentComplaint = useSelector(selectCurrentComplaint);

  const handleNewComplaint = () => {
    dispatch(clearWorkspaceThunk());
  };

  return (
    <header className="app-header">
      <div className="header-brand-row">
        <div className="header-brand">
          <h1>AIVOA</h1>
          <span className="version-pill">v1.0 Copilot</span>
        </div>
        {currentComplaint && (
          <button type="button" className="new-complaint-btn" onClick={handleNewComplaint}>
            + New Complaint
          </button>
        )}
      </div>
      <p className="app-subtitle">
        AI-Powered Customer Complaint Management System — Pharmaceutical Manufacturing
      </p>
    </header>
  );
}

export default AppHeader;
