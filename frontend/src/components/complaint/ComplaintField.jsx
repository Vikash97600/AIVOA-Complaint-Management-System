import React from 'react';

export function ComplaintField({ label, value, isUpdated, isTextarea = false, placeholder = "Not provided" }) {
  const containerClass = isUpdated ? 'form-field updated-field' : 'form-field';

  return (
    <div className={containerClass}>
      <label>{label}</label>
      {isTextarea ? (
        <textarea rows="3" value={value || ''} readOnly placeholder={placeholder} />
      ) : (
        <input type="text" value={value || ''} readOnly placeholder={placeholder} />
      )}
    </div>
  );
}

export default ComplaintField;
