import { useState } from 'react';

export default function UploadPanel({ 
  label = "Choose Files", 
  accept = "image/*", 
  multiple = true,
  onChange 
}) {
  const [selectedFiles, setSelectedFiles] = useState([]);

  function handleChange(e) {
    const files = Array.from(e.target.files);
    setSelectedFiles(files);
    onChange && onChange(files);
  }

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: '1rem',
      flexWrap: 'wrap'
    }}>
      <input
        type="file"
        multiple={multiple}
        accept={accept}
        onChange={handleChange}
        id={`file-input-${label.replace(/\s/g, '-')}`}
        style={{ display: 'none' }}
      />
      <label 
        htmlFor={`file-input-${label.replace(/\s/g, '-')}`} 
        style={{
          padding: '0.75rem 2rem',
          fontSize: '1rem',
          fontWeight: 600,
          backgroundColor: 'white',
          color: '#000000',
          border: 'none',
          borderRadius: '100px',
          cursor: 'pointer',
          transition: 'all 0.3s ease',
          display: 'inline-block'
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.transform = 'scale(1.05)';
          e.currentTarget.style.boxShadow = '0 10px 30px rgba(255, 255, 255, 0.2)';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.transform = 'scale(1)';
          e.currentTarget.style.boxShadow = 'none';
        }}
      >
        {label}
      </label>
      {selectedFiles.length > 0 && (
        <div style={{
          padding: '0.5rem 1.25rem',
          backgroundColor: 'rgba(82, 39, 255, 0.2)',
          border: '1px solid rgba(82, 39, 255, 0.4)',
          borderRadius: '100px',
          fontSize: '0.9rem',
          color: '#5227FF',
          fontWeight: 500
        }}>
          {selectedFiles.length} file{selectedFiles.length !== 1 ? 's' : ''} selected
        </div>
      )}
    </div>
  );
}