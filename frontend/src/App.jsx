import React from 'react';
import { ComplaintForm } from './components/ComplaintForm';
import { CopilotPanel } from './components/CopilotPanel';
import './App.css';

function App() {
  return (
    <div className="app-container">
      <header className="app-header">
        <div className="header-brand">
          <h1>AIVOA</h1>
          <span className="version-pill">v1.0 Copilot</span>
        </div>
        <p className="app-subtitle">AI-Powered Customer Complaint Management System — Pharmaceutical Manufacturing</p>
      </header>

      <main className="app-layout">
        <section className="left-panel">
          <ComplaintForm />
        </section>

        <section className="right-panel">
          <CopilotPanel />
        </section>
      </main>
    </div>
  );
}

export default App;
