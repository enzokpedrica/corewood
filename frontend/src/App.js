import React, { useState } from 'react';
import FileUpload from './components/FileUpload';
import ConfigForm from './components/ConfigForm';
import { generatePDF } from './services/api';
import './App.css';

function App() {
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
  const [success, setSuccess] = useState(false);

  const handleGeneratePDF = async () => {
    if (!file) {
      setError('Selecione um arquivo MPR primeiro!');
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(false);

    try {
      const pdfBlob = await generatePDF(file, config);
      
      // Criar URL para download
      const url = window.URL.createObjectURL(pdfBlob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${file.name.replace('.mpr', '')}_furacao.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
    } catch (err) {
      console.error('Erro ao gerar PDF:', err);
      setError('Erro ao gerar PDF. Tente novamente.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      {/* Header */}
      <header className="app-header">
        <div className="container">
          <h1>🪵 CoreWood</h1>
          <p>Gerador de Documentação Técnica para Indústria Moveleira</p>
        </div>
      </header>

      {/* Main Content */}
      <main className="app-main">
        <div className="container">
          <div className="content-grid">
            {/* Coluna Esquerda - Upload */}
            <div className="left-column">
              <FileUpload 
                onFileSelect={setFile} 
                selectedFile={file}
              />
              
              {/* Mensagens */}
              {error && (
                <div className="message error">
                  ⚠️ {error}
                </div>
              )}
              
              {success && (
                <div className="message success">
                  ✅ PDF gerado com sucesso!
                </div>
              )}

              {/* Botão de Gerar */}
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

              {/* Info */}
              {file && (
                <div className="info-box">
                  <h4>ℹ️ Informações</h4>
                  <p>• Arquivo: <strong>{file.name}</strong></p>
                  <p>• Tamanho: <strong>{(file.size / 1024).toFixed(2)} KB</strong></p>
                  <p>• Configurações prontas para gerar!</p>
                </div>
              )}
            </div>

            {/* Coluna Direita - Configurações */}
            <div className="right-column">
              <ConfigForm 
                config={config}
                onChange={setConfig}
              />
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
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

export default App;