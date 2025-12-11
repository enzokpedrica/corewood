import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import './StepConverter.css';

function StepConverter() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const onDrop = useCallback((acceptedFiles) => {
    if (acceptedFiles && acceptedFiles.length > 0) {
      setSelectedFile(acceptedFiles[0]);
      setResult(null);
      setError(null);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/octet-stream': ['.step', '.STEP', '.stp', '.STP']
    },
    multiple: false
  });

  const convertToMPR = async () => {
    if (!selectedFile) return;

    setLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);

      const token = localStorage.getItem('token');
      const response = await fetch(`${process.env.REACT_APP_API_URL}/step-to-mpr`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      if (!response.ok) {
        throw new Error('Erro ao converter arquivo');
      }

      // Baixar arquivo MPR
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = selectedFile.name.replace(/\.(step|stp)$/i, '.mpr');
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      a.remove();

      setResult({ success: true, message: 'Arquivo convertido com sucesso!' });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const parseStep = async () => {
    if (!selectedFile) return;

    setLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);

      const token = localStorage.getItem('token');
      const response = await fetch(`${process.env.REACT_APP_API_URL}/parse-step`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      if (!response.ok) {
        throw new Error('Erro ao processar arquivo');
      }

      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="step-converter">
      <div className="converter-header">
        <h2>🔄 Conversor STEP → MPR</h2>
        <p>Converta arquivos CAD (.step) para formato de máquina CNC (.mpr)</p>
      </div>

      <div 
        {...getRootProps()} 
        className={`dropzone ${isDragActive ? 'active' : ''} ${selectedFile ? 'has-file' : ''}`}
      >
        <input {...getInputProps()} />
        {selectedFile ? (
          <div className="file-info">
            <span className="file-icon">📐</span>
            <div>
              <p className="file-name">{selectedFile.name}</p>
              <p className="file-size">{(selectedFile.size / 1024).toFixed(2)} KB</p>
            </div>
            <button 
              className="remove-btn"
              onClick={(e) => {
                e.stopPropagation();
                setSelectedFile(null);
                setResult(null);
                setError(null);
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
                : 'Arraste um arquivo .step ou clique para selecionar'}
            </p>
            <p className="upload-hint">Arquivos STEP de qualquer software CAD</p>
          </div>
        )}
      </div>

      {selectedFile && (
        <div className="actions">
          <button 
            className="btn btn-secondary"
            onClick={parseStep}
            disabled={loading}
          >
            {loading ? '⏳ Processando...' : '🔍 Visualizar Dados'}
          </button>
          <button 
            className="btn btn-primary"
            onClick={convertToMPR}
            disabled={loading}
          >
            {loading ? '⏳ Convertendo...' : '⬇️ Baixar MPR'}
          </button>
        </div>
      )}

      {error && (
        <div className="error-message">
          ❌ {error}
        </div>
      )}

      {result && result.success && (
        <div className="success-message">
          ✅ {result.message}
        </div>
      )}

      {result && result.data && (
        <div className="result-panel">
          <h3>📊 Dados Extraídos</h3>
          <div className="result-grid">
            <div className="result-item">
              <span className="label">Nome:</span>
              <span className="value">{result.data.nome}</span>
            </div>
            <div className="result-item">
              <span className="label">Dimensões:</span>
              <span className="value">
                {result.data.dimensoes.largura} x {result.data.dimensoes.comprimento} x {result.data.dimensoes.espessura} mm
              </span>
            </div>
            <div className="result-item">
              <span className="label">Total de Furos:</span>
              <span className="value">{result.data.total_furos}</span>
            </div>
          </div>

          {result.data.furos && result.data.furos.length > 0 && (
            <div className="furos-table">
              <h4>🔩 Furações</h4>
              <table>
                <thead>
                  <tr>
                    <th>#</th>
                    <th>X</th>
                    <th>Y</th>
                    <th>Ø</th>
                    <th>Prof.</th>
                  </tr>
                </thead>
                <tbody>
                  {result.data.furos.map((furo, index) => (
                    <tr key={index}>
                      <td>{furo.id || index + 1}</td>
                      <td>{furo.x} mm</td>
                      <td>{furo.y} mm</td>
                      <td>{furo.diameter} mm</td>
                      <td>{furo.depth} mm</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default StepConverter;