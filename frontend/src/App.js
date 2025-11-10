import React, { useState } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './contexts/AuthContext';
import PrivateRoute from './components/PrivateRoute';
import Login from './pages/Login';
import Register from './pages/Register';
import FileUpload from './components/FileUpload';
import ConfigForm from './components/ConfigForm';
import { generatePDF } from './services/api';
import { validateMPRFile, validateConfig, formatErrors, formatWarnings } from './utils/validation';
import './App.css';
import LoteUpload from './components/LoteUpload';

function MainApp() {
  const [modoLote, setModoLote] = useState(false);
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
              {/* Toggle modo lote */}
              <button
                onClick={() => setModoLote(!modoLote)}
                style={{
                  padding: '0.75rem 1.5rem',
                  background: modoLote ? '#667eea' : 'white',
                  color: modoLote ? 'white' : '#667eea',
                  border: '2px solid #667eea',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  fontWeight: '600',
                  transition: 'all 0.3s'
                }}
              >
                {modoLote ? '📄 Modo Individual' : '📦 Modo Lote'}
              </button>
              
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
          {modoLote ? (
            // MODO LOTE
            <LoteUpload />
          ) : (
            // MODO INDIVIDUAL (código existente)
            <div className="content-grid">
              <div className="left-column">
                <FileUpload 
                  onFileSelect={handleFileSelect} 
                  selectedFile={file}
                />
                
                {/* ... resto do código existente ... */}
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