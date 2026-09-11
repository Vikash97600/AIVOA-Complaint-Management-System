import React, { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { Sun, Moon, PlusCircle, Sparkles, History } from 'lucide-react';
import { selectCurrentComplaint, selectComplaintListTotal } from '../../store/selectors';
import { clearWorkspaceThunk } from '../../store/thunks';

export function AppHeader({ onOpenHistory }) {
  const dispatch = useDispatch();
  const currentComplaint = useSelector(selectCurrentComplaint);
  const totalCount = useSelector(selectComplaintListTotal);

  const [theme, setTheme] = useState(() => {
    return localStorage.getItem('aivoa_theme') || 'dark';
  });

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('aivoa_theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'));
  };

  const handleNewComplaint = () => {
    dispatch(clearWorkspaceThunk());
    const url = new URL(window.location);
    url.searchParams.delete('complaintId');
    window.history.replaceState({}, '', url.pathname);
  };

  return (
    <header className="app-header">
      <div className="header-brand-row">
        <div className="header-brand">
          <div className="logo-icon-wrapper">
            <Sparkles className="logo-sparkle-icon" size={22} />
          </div>
          <div className="title-group">
            <h1>AIVOA</h1>
            <span className="version-pill">v1.0 Copilot</span>
          </div>
        </div>

        <div className="header-actions">
          <button
            type="button"
            className="history-nav-btn"
            onClick={onOpenHistory}
            title="Open Complaint History"
          >
            <History size={16} />
            <span>Complaint History</span>
            {totalCount > 0 && <span className="history-count-badge">{totalCount}</span>}
          </button>

          <button
            type="button"
            className="theme-toggle-btn"
            onClick={toggleTheme}
            title={`Switch to ${theme === 'dark' ? 'Light' : 'Dark'} Mode`}
          >
            {theme === 'dark' ? (
              <>
                <Sun size={16} className="theme-icon sun" />
                <span>Light Mode</span>
              </>
            ) : (
              <>
                <Moon size={16} className="theme-icon moon" />
                <span>Dark Mode</span>
              </>
            )}
          </button>

          {currentComplaint && (
            <button type="button" className="new-complaint-btn" onClick={handleNewComplaint}>
              <PlusCircle size={16} />
              <span>New Complaint</span>
            </button>
          )}
        </div>
      </div>
      <p className="app-subtitle">
        AI-Powered Customer Complaint Management System — Pharmaceutical Manufacturing
      </p>
    </header>
  );
}

export default AppHeader;

