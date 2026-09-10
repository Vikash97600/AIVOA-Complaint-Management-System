import React from 'react';

export function SeverityBadge({ severity }) {
  const sev = (severity || 'MEDIUM').toUpperCase();
  const classMap = {
    LOW: 'severity-low',
    MEDIUM: 'severity-medium',
    HIGH: 'severity-high',
    CRITICAL: 'severity-critical',
  };

  return (
    <span className={`severity-badge ${classMap[sev] || 'severity-medium'}`}>
      {sev}
    </span>
  );
}

export default SeverityBadge;
