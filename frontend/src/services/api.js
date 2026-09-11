const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const handleFetchError = (error, customMessage) => {
  if (error instanceof TypeError && error.message.includes('fetch')) {
    throw new Error('Unable to connect to AIVOA backend. Please make sure the backend server is running.');
  }
  if (customMessage && !error.message) {
    throw new Error(customMessage);
  }
  throw error;
};


export const checkHealth = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/health`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    handleFetchError(error, 'API health check failed');
  }
};

export const sendCopilotMessage = async (message, complaintId = null) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/copilot/message`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message,
        complaint_id: complaintId,
      }),
    });
    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      throw new Error(errData.detail || `HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    handleFetchError(error, 'Copilot API request failed');
  }
};

export const uploadCopilotDocument = async (file, complaintId = null) => {
  try {
    const formData = new FormData();
    formData.append('file', file);
    if (complaintId) {
      formData.append('complaint_id', complaintId);
    }

    const response = await fetch(`${API_BASE_URL}/api/copilot/document`, {
      method: 'POST',
      body: formData,
    });
    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      throw new Error(errData.detail || `HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    handleFetchError(error, 'Document upload API request failed');
  }
};

export const commitComplaint = async (complaintId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/complaints/${complaintId}/commit`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      throw new Error(errData.detail || `HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    handleFetchError(error, 'Commit complaint API request failed');
  }
};

export const getComplaint = async (complaintId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/complaints/${complaintId}`);
    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      throw new Error(errData.detail || `HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    handleFetchError(error, 'Get complaint API request failed');
  }
};

export const updateComplaint = async (complaintId, patchData) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/complaints/${complaintId}`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(patchData),
    });
    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      throw new Error(errData.detail || `HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    handleFetchError(error, 'Update complaint API request failed');
  }
};

export const listComplaints = async (page = 1, pageSize = 20, status = null, search = null) => {
  try {
    const params = new URLSearchParams({
      page: String(page),
      page_size: String(pageSize),
    });
    if (status) {
      params.append('status', status);
    }
    if (search && search.trim()) {
      params.append('search', search.trim());
    }

    const response = await fetch(`${API_BASE_URL}/api/complaints?${params.toString()}`);
    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      throw new Error(errData.detail || `HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    handleFetchError(error, 'List complaints API request failed');
  }
};

export const checkCompleteness = async (complaintId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/complaints/${complaintId}/completeness`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });
    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      throw new Error(errData.detail || `HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    handleFetchError(error, 'Check completeness API request failed');
  }
};

export const detectDuplicates = async (complaintId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/complaints/${complaintId}/duplicates`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });
    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      throw new Error(errData.detail || `HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    handleFetchError(error, 'Detect duplicates API request failed');
  }
};

export const generateSummary = async (complaintId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/complaints/${complaintId}/summary`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });
    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      throw new Error(errData.detail || `HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    handleFetchError(error, 'Generate summary API request failed');
  }
};

export const deleteComplaint = async (complaintId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/complaints/${complaintId}`, {
      method: 'DELETE',
    });
    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      throw new Error(errData.detail || `HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    handleFetchError(error, 'Delete complaint API request failed');
  }
};

export default {
  API_BASE_URL,
  checkHealth,
  sendCopilotMessage,
  uploadCopilotDocument,
  commitComplaint,
  getComplaint,
  updateComplaint,
  deleteComplaint,
  listComplaints,
  checkCompleteness,
  detectDuplicates,
  generateSummary,
};



