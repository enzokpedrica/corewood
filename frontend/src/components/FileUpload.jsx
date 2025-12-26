import React, { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import './FileUpload.css';

function FileUpload({ onFileSelect, selectedFile }) {
  const onDrop = useCallback((acceptedFiles) => {
    if (acceptedFiles && acceptedFiles.length > 0) {
      onFileSelect(acceptedFiles[0]);
    }
  }, [onFileSelect]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/octet-stream': ['.mpr', '.MPR']
    },
    multiple: false
  });

  return (
    <div className="file-upload">
      <div 
        {...getRootProps()} 
        className={`dropzone ${isDragActive ? 'active' : ''} ${selectedFile ? 'has-file' : ''}`}
      >
        <input {...getInputProps()} />
        {selectedFile ? (
          <div className="file-info">
            <span className="file-icon">📄</span>
            <div>
              <p className="file-name">{selectedFile.name}</p>
              <p className="file-size">{(selectedFile.size / 1024).toFixed(2)} KB</p>
            </div>
            <button 
              className="remove-btn"
              onClick={(e) => {
                e.stopPropagation();
                onFileSelect(null);
              }}
            >
              ✕
            </button>
          </div>
        ) : (
          <div className="dropzone-content">
            <span className="upload-icon">📁</span>
            <p className="upload-text">
              {isDragActive 
                ? 'Solte o arquivo aqui...' 
                : 'Arraste um arquivo .mpr ou clique para selecionar'}
            </p>
            <p className="upload-hint">Apenas arquivos .mpr</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default FileUpload;