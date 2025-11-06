import React, { useState } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './contexts/AuthContext';
import PrivateRoute from './components/PrivateRoute';
import Login from './pages/Login';
import FileUpload from './components/FileUpload';
import ConfigForm from './components/ConfigForm';
import { generatePDF } from './services/api';
import { validateMPRFile, validateConfig, formatErrors, formatWarnings } from './utils/validation';
import './App.css';

function MainApp() {
  const [file, setFile] = useState(null);
  const [config, setConfig] = useState({
    angulo_rotacao: 0,
    espelhar_peca: false,
    posicao_borda_comprimento: null,
    posicao_borda_largura: null,
    revisao: '',
    alerta: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [warning, setWarning] = useState(null);
  const [success, setSuccess] = useState(false);

  const { user, logout } = useAuth();

  const handleFileSelect = (selectedFile) => {
    setFile(selectedFile);
    setError(null);
    setWarning(null);
    
    if (selectedFile) {
      const validation = validateMPRFile(selectedFile);
      
      if (!validation.valid) {
        setError(`Erro no arquivo:\n• ${formatErrors(validation.errors)}`);
        setFile(null);
      } else if (validation.warnings.length > 0) {
        setWarning(`Atenção:\n• ${formatWarnings(validation.warnings)}`);
      }
    }
  };

  const handleGeneratePDF = async () => {
    setError(null);
    setWarning(null);
    setSuccess(false);

    if (!file) {
      setError('Selecione um arquivo MPR primeiro!');
      return;
    }

    const fileValidation = validateMPRFile(file);
    if (!fileValidation.valid) {
      setError(`Erro no arquivo:\n• ${formatErrors(fileValidation.errors)}`);
      return;
    }

    const configValidation = validateConfig(config);
    if (!configValidation.valid) {
      setError(`Erro nas configurações:\n• ${formatErrors(configValidation.errors)}`);
      return;
    }

    if (configValidation.warnings.length > 0) {
      setWarning(`Atenção:\n• ${formatWarnings(configValidation.warnings)}`);
    }

    setLoading(true);

    try {
      const pdfBlob = await generatePDF(file, config);
      
      const url = window.URL.createObjectURL(pdfBlob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${file.name.replace('.mpr', '').replace('.MPR', '')}_furacao.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      setSuccess(true);
      setTimeout(() => setSuccess(false), 5000);
    } catch (err) {
      console.error('Erro ao gerar PDF:', err);
      
      let errorMsg = 'Erro ao gerar PDF. ';
      
      if (err.response) {
        errorMsg += `Código: ${err.response.status}. `;
        if (err.response.data?.detail) {
          errorMsg += err.response.data.detail;
        }
      } else if (err.request) {
        errorMsg += 'Não foi possível conectar à API. Verifique sua conexão.';
      } else {
        errorMsg += err.message;
      }
      
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <div className="container">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <h1>🪵 CoreWood</h1>
              <p>Gerador de Documentação Técnica para Indústria Moveleira</p>
            </div>
            <div style={{ textAlign: 'right' }}>
              <p style={{ marginBottom: '0.5rem', color: '#666' }}>
                👤 <strong>{user?.username}</strong>
              </p>
              <button 
                onClick={logout}
                style={{
                  padding: '0.5rem 1rem',
                  background: '#dc3545',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontWeight: '600'
                }}
              >
                Sair
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="app-main">
        <div className="container">
          <div className="content-grid">
            <div className="left-column">
              <FileUpload 
                onFileSelect={handleFileSelect} 
                selectedFile={file}
              />
              
              {error && (
                <div className="message error">
                  <strong>⚠️ Erro</strong>
                  <pre>{error}</pre>
                </div>
              )}
              
              {warning && !error && (
                <div className="message warning">
                  <strong>⚡ Aviso</strong>
                  <pre>{warning}</pre>
                </div>
              )}
              
              {success && (
                <div className="message success">
                  ✅ PDF gerado com sucesso!
                </div>
              )}

              <button 
                className="generate-btn"
                onClick={handleGeneratePDF}
                disabled={!file || loading}
              >
                {loading ? (
                  <>
                    <span className="spinner"></span>
                    Gerando PDF...
                  </>
                ) : (
                  <>
                    📄 Gerar PDF Técnico
                  </>
                )}
              </button>

              {file && !error && (
                <div className="info-box">
                  <h4>ℹ️ Informações</h4>
                  <p>• Arquivo: <strong>{file.name}</strong></p>
                  <p>• Tamanho: <strong>{(file.size / 1024).toFixed(2)} KB</strong></p>
                  <p>• Status: <strong className="status-ok">✓ Válido</strong></p>
                </div>
              )}
            </div>

            <div className="right-column">
              <ConfigForm 
                config={config}
                onChange={setConfig}
              />
            </div>
          </div>
        </div>
      </main>

      <footer className="app-footer">
        <div className="container">
          <p>CoreWood © 2024 - Desenvolvido para Linea Brasil</p>
          <p className="api-status">
            API: <span className="status-dot"></span> Online
          </p>
        </div>
      </footer>
    </div>
  );
}

function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route 
        path="/" 
        element={
          <PrivateRoute>
            <MainApp />
          </PrivateRoute>
        } 
      />
      <Route path="*" element={<Navigate to="/" />} />
    </Routes>
  );
}

export default App;