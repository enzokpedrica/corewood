import React, { useState } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './contexts/AuthContext';
import PrivateRoute from './components/PrivateRoute';
import Login from './pages/Login';
import Register from './pages/Register';
import FileUpload from './components/FileUpload';
import ConfigForm from './components/ConfigForm';
import LoteUpload from './components/LoteUpload';
import { generatePDF } from './services/api';
import { validateMPRFile, validateConfig, formatErrors, formatWarnings } from './utils/validation';
import './App.css';
import EditorMPR from './components/EditorMPR/EditorMPR';
import ImportarPecas from './components/ImportarPecas/ImportarPecas';

function MainApp() {
  const [modoLote, setModoLote] = useState('individual');
  const [file, setFile] = useState(null);
  const [config, setConfig] = useState({
    angulo_rotacao: 0,
    espelhar_peca: false,
    bordas: {
      top: null,
      bottom: null,
      left: null,
      right: null
    },
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
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
              {/* Toggle entre 3 modos */}
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <button
                  onClick={() => setModoLote('individual')}
                  style={{
                    padding: '0.75rem 1.5rem',
                    background: modoLote === 'individual' ? '#667eea' : 'white',
                    color: modoLote === 'individual' ? 'white' : '#667eea',
                    border: '2px solid #667eea',
                    borderRadius: '8px',
                    cursor: 'pointer',
                    fontWeight: '600',
                    transition: 'all 0.3s'
                  }}
                >
                  📄 Individual
                </button>

                <button
                  onClick={() => setModoLote('lote')}
                  style={{
                    padding: '0.75rem 1.5rem',
                    background: modoLote === 'lote' ? '#667eea' : 'white',
                    color: modoLote === 'lote' ? 'white' : '#667eea',
                    border: '2px solid #667eea',
                    borderRadius: '8px',
                    cursor: 'pointer',
                    fontWeight: '600',
                    transition: 'all 0.3s'
                  }}
                >
                  📦 Lote
                </button>

                <button
                  onClick={() => setModoLote('importar')}
                  style={{
                    padding: '0.5rem 1rem',
                    background: modoLote === 'importar' ? '#8b5cf6' : '#2d2d2d',
                    color: 'white',
                    border: modoLote === 'importar' ? 'none' : '2px solid #8b5cf6',
                    borderRadius: '6px',
                    cursor: 'pointer',
                    fontWeight: '600',
                    fontSize: '0.85rem',
                    transition: 'all 0.2s'
                  }}
                >
                  📤 Importar
                </button>

                <button
                  onClick={() => setModoLote('editor')}
                  style={{
                    padding: '0.75rem 1.5rem',
                    background: modoLote === 'editor' ? '#667eea' : 'white',
                    color: modoLote === 'editor' ? 'white' : '#667eea',
                    border: '2px solid #667eea',
                    borderRadius: '8px',
                    cursor: 'pointer',
                    fontWeight: '600',
                    transition: 'all 0.3s'
                  }}
                >
                  ✏️ Editor
                </button>
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
        </div>
      </header>

      <main className="app-main">
        <div className="container">
          {modoLote === 'lote' ? (
            // MODO LOTE
            <LoteUpload />
          ) : modoLote === 'editor' ? (
            // MODO EDITOR
            <EditorMPR />
          ) : modoLote === 'importar' ? (
            // MODO IMPORTAR
            <ImportarPecas />
          ) : (
            // MODO INDIVIDUAL
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
          )}
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
      <Route path="/register" element={<Register />} />
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