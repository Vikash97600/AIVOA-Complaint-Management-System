import React, { useState, useEffect } from 'react';
import { useDispatch } from 'react-redux';
import { AppHeader } from '../components/layout/AppHeader';
import { SplitPane } from '../components/layout/SplitPane';
import { ComplaintForm } from '../components/ComplaintForm';
import { CopilotPanel } from '../components/CopilotPanel';
import { ComplaintHistoryDrawer } from '../components/ComplaintHistory/ComplaintHistoryDrawer';
import { fetchComplaintsThunk, fetchComplaintThunk } from '../store/thunks';

export function ComplaintWorkspace() {
  const dispatch = useDispatch();
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);

  // Hydrate complaints list and active complaint from MySQL on initial mount / refresh
  useEffect(() => {
    // 1. Load latest complaints list from MySQL
    dispatch(fetchComplaintsThunk());

    // 2. Check if complaintId query param exists in URL
    const searchParams = new URLSearchParams(window.location.search);
    const complaintId = searchParams.get('complaintId');

    if (complaintId) {
      dispatch(fetchComplaintThunk(complaintId));
    }
  }, [dispatch]);

  return (
    <div className="app-container">
      <AppHeader onOpenHistory={() => setIsHistoryOpen(true)} />
      <SplitPane
        leftContent={<ComplaintForm onOpenHistory={() => setIsHistoryOpen(true)} />}
        rightContent={<CopilotPanel />}
      />
      <ComplaintHistoryDrawer
        isOpen={isHistoryOpen}
        onClose={() => setIsHistoryOpen(false)}
      />
    </div>
  );
}

export default ComplaintWorkspace;
