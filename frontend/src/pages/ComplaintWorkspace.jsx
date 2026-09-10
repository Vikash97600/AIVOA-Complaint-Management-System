import React from 'react';
import { AppHeader } from '../components/layout/AppHeader';
import { SplitPane } from '../components/layout/SplitPane';
import { ComplaintForm } from '../components/ComplaintForm';
import { CopilotPanel } from '../components/CopilotPanel';

export function ComplaintWorkspace() {
  return (
    <div className="app-container">
      <AppHeader />
      <SplitPane
        leftContent={<ComplaintForm />}
        rightContent={<CopilotPanel />}
      />
    </div>
  );
}

export default ComplaintWorkspace;
