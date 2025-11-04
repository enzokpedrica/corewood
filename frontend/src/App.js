import React, { useState } from 'react';
import FileUpload from './components/FileUpload';
import ConfigForm from './components/ConfigForm';
import PecaPreview from './components/PecaPreview';
import { generatePDF, parseMPR } from './services/api';
import { validateMPRFile, validateConfig, formatErrors, formatWarnings } from './utils/validation';
import './App.css';

function App() {
  const [file, setFile] = useState(null);
  const [pecaData, setPecaData] = useState(null);
  const [loadingPreview, setLoadingPreview] = useState(false);
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

  // Validar arquivo quando selecionar
const handleFileSelect = async (selectedFile) => {
  setFile(selectedFile);
  setError(null);
  setWarning(null);
  setPecaData(null);

  if (selectedFile) {
    const validation = validateMPRFile(selectedFile);

    if (!validation.valid) {
      setError(`Erro no arquivo:\n• ${formatErrors(validation.errors)}`);
      setFile(null);
    } else {
      setLoadingPreview(true);
      try {
        const parseResult = await parseMPR(selectedFile); // ← aqui o await funciona
        setPecaData(parseResult.data);

        if (validation.warnings.length > 0) {
          setWarning(`Atenção:\n• ${formatWarnings(validation.warnings)}`);
        }
      } catch (err) {
        console.error('Erro ao fazer preview:', err);
        setWarning('Não foi possível carregar preview do arquivo');
      } finally {
        setLoadingPreview(false);
      }
    }
  }
};


  const handleGeneratePDF = async () => {
    // Limpar mensagens anteriores
    setError(null);
    setWarning(null);
    setSuccess(false);

    // Validar arquivo
    if (!file) {
      setError('Selecione um arquivo MPR primeiro!');
      return;
    }

    const fileValidation = validateMPRFile(file);
    if (!fileValidation.valid) {
      setError(`Erro no arquivo:\n• ${formatErrors(fileValidation.errors)}`);
      return;
    }

    // Validar configurações
    const configValidation = validateConfig(config);
    if (!configValidation.valid) {
      setError(`Erro nas configurações:\n• ${formatErrors(configValidation.errors)}`);
      return;
    }

    // Mostrar warnings (mas permite continuar)
    if (configValidation.warnings.length > 0) {
      setWarning(`Atenção:\n• ${formatWarnings(configValidation.warnings)}`);
    }

    // Gerar PDF
    setLoading(true);

    try {
      const pdfBlob = await generatePDF(file, config);
      
      // Download
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
      
      // Mensagem de erro mais detalhada
      let errorMsg = 'Erro ao gerar PDF. ';
      
      if (err.response) {
        // Erro da API
        errorMsg += `Código: ${err.response.status}. `;
        if (err.response.data?.detail) {
          errorMsg += err.response.data.detail;
        }
      } else if (err.request) {
        // Sem resposta da API
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
                onFileSelect={handleFileSelect} 
                selectedFile={file}
              />

              <PecaPreview 
                pecaData={pecaData}
                loading={loadingPreview}
              />
              
              {/* Mensagens */}
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
              {file && !error && (
                <div className="info-box">
                  <h4>ℹ️ Informações</h4>
                  <p>• Arquivo: <strong>{file.name}</strong></p>
                  <p>• Tamanho: <strong>{(file.size / 1024).toFixed(2)} KB</strong></p>
                  <p>• Status: <strong className="status-ok">✓ Válido</strong></p>
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