import React, { useState } from 'react';
import { useDropzone } from 'react-dropzone';
import PecaCard from './PecaCard';
import { generatePDFBatch } from '../services/api';
import './LoteUpload.css';

function LoteUpload() {
  const [arquivos, setArquivos] = useState([]);
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState({ current: 0, total: 0 });
  const [error, setError] = useState(null);

  // Configuração padrão para novos arquivos
  const configPadrao = {
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
  };

  // Dropzone para múltiplos arquivos
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: {
      'application/octet-stream': ['.mpr', '.MPR']
    },
    multiple: true,
    onDrop: (acceptedFiles) => {
      const novosArquivos = acceptedFiles.map((file, index) => ({
        id: Date.now() + index,
        file: file,
        nome: file.name,
        config: { ...configPadrao }
      }));
      
      setArquivos([...arquivos, ...novosArquivos]);
      setError(null);
    }
  });

  // Atualizar configuração de um arquivo
  const handleUpdateConfig = (id, novoConfig) => {
    setArquivos(arquivos.map(arq => 
      arq.id === id ? { ...arq, config: novoConfig } : arq
    ));
  };

  // Remover arquivo
  const handleRemove = (id) => {
    setArquivos(arquivos.filter(arq => arq.id !== id));
  };

  // Aplicar configuração da primeira peça em todas
  const handleAplicarATodas = () => {
    if (arquivos.length === 0) return;
    
    const primeiraConfig = arquivos[0].config;
    setArquivos(arquivos.map(arq => ({
      ...arq,
      config: { ...primeiraConfig }
    })));
  };

  // Limpar tudo
  const handleLimparTudo = () => {
    if (window.confirm(`Remover todos os ${arquivos.length} arquivos?`)) {
      setArquivos([]);
      setError(null);
    }
  };

  // Validar antes de processar
  const validarArquivos = () => {
    const erros = [];
    
    arquivos.forEach((arq, index) => {
      if (!arq.config.revisao || arq.config.revisao.trim() === '') {
        erros.push(`${arq.nome}: Revisão é obrigatória`);
      }
    });
    
    return erros;
  };

  // Processar todos os arquivos
  const handleProcessarLote = async () => {
    setError(null);
    
    // Validar
    const erros = validarArquivos();
    if (erros.length > 0) {
      setError(`Erros encontrados:\n• ${erros.join('\n• ')}`);
      return;
    }

    setLoading(true);
    setProgress({ current: 0, total: arquivos.length });

    try {
      const zipBlob = await generatePDFBatch(arquivos, (current, total) => {
        setProgress({ current, total });
      });

      // Download do ZIP
      const url = window.URL.createObjectURL(zipBlob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `documentos_tecnicos_${new Date().getTime()}.zip`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      // Limpar após sucesso
      setArquivos([]);
      alert(`✅ ${arquivos.length} PDFs gerados com sucesso!`);
      
    } catch (err) {
      console.error('Erro ao processar lote:', err);
      setError(`Erro ao processar arquivos: ${err.message}`);
    } finally {
      setLoading(false);
      setProgress({ current: 0, total: 0 });
    }
  };

  return (
    <div className="lote-upload">
      <div className="lote-header">
        <h2>📦 Processamento em Lote</h2>
        <p>Faça upload de múltiplos arquivos MPR e configure individualmente</p>
      </div>

      {/* Dropzone */}
      <div 
        {...getRootProps()} 
        className={`dropzone ${isDragActive ? 'dropzone-active' : ''}`}
      >
        <input {...getInputProps()} />
        {isDragActive ? (
          <p className="dropzone-text">📥 Solte os arquivos aqui...</p>
        ) : (
          <div className="dropzone-content">
            <span className="dropzone-icon">📁</span>
            <p className="dropzone-text">
              Arraste múltiplos arquivos .MPR aqui
            </p>
            <p className="dropzone-hint">ou clique para selecionar</p>
          </div>
        )}
      </div>

      {/* Mensagens de erro */}
      {error && (
        <div className="lote-error">
          <strong>⚠️ Erro</strong>
          <pre>{error}</pre>
        </div>
      )}

      {/* Lista de arquivos */}
      {arquivos.length > 0 && (
        <>
          <div className="lote-actions">
            <div className="lote-info">
              <strong>{arquivos.length}</strong> arquivo{arquivos.length !== 1 ? 's' : ''} carregado{arquivos.length !== 1 ? 's' : ''}
            </div>
            <div className="lote-buttons">
              <button 
                className="btn-secondary"
                onClick={handleAplicarATodas}
                disabled={arquivos.length < 2}
              >
                🔄 Aplicar config da 1ª em todas
              </button>
              <button 
                className="btn-secondary btn-danger"
                onClick={handleLimparTudo}
              >
                🗑️ Limpar tudo
              </button>
            </div>
          </div>

          {/* Cards das peças */}
          <div className="pecas-list">
            {arquivos.map(arq => (
              <PecaCard
                key={arq.id}
                peca={arq}
                onUpdate={handleUpdateConfig}
                onRemove={handleRemove}
              />
            ))}
          </div>

          {/* Botão processar */}
          <div className="lote-footer">
            <button
              className="btn-processar"
              onClick={handleProcessarLote}
              disabled={loading || arquivos.length === 0}
            >
              {loading ? (
                <>
                  <span className="spinner"></span>
                  Processando... {progress.current}/{progress.total}
                </>
              ) : (
                <>
                  📦 Gerar {arquivos.length} PDF{arquivos.length !== 1 ? 's' : ''} e baixar ZIP
                </>
              )}
            </button>

            {loading && (
              <div className="progress-bar">
                <div 
                  className="progress-fill"
                  style={{ width: `${(progress.current / progress.total) * 100}%` }}
                ></div>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}

export default LoteUpload;