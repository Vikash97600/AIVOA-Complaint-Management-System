import React from 'react';

export function AppHeader() {
  return (
    <header className="app-header">
      <div className="header-brand">
        <h1>AIVOA</h1>
        <span className="version-pill">v1.0 Copilot</span>
      </div>
      <p className="app-subtitle">
        AI-Powered Customer Complaint Management System — Pharmaceutical Manufacturing
      </p>
    </header>
  );
}

export default AppHeader;
