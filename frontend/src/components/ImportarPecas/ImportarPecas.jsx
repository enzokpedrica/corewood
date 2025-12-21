import React, { useState } from 'react';
import './ImportarPecas.css';
import api from '../../services/api';  // Adiciona no topo do arquivo

function ImportarPecas() {
  const [codigoProduto, setCodigoProduto] = useState('');
  const [nomeProduto, setNomeProduto] = useState('');
  const [arquivo, setArquivo] = useState(null);
  const [loading, setLoading] = useState(false);
  const [resultado, setResultado] = useState(null);
  const [erro, setErro] = useState(null);

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setArquivo(file);
      setErro(null);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!codigoProduto || !arquivo) {
      setErro('Preencha o código do produto e selecione um arquivo');
      return;
    }

    setLoading(true);
    setErro(null);
    setResultado(null);

    try {
      const formData = new FormData();
      formData.append('codigo_produto', codigoProduto);
      formData.append('nome_produto', nomeProduto || `Produto ${codigoProduto}`);
      formData.append('file', arquivo);

      const response = await api.post('/pecas/importar', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      const data = response.data;

      if (data.success) {
        setResultado(data);
        setCodigoProduto('');
        setNomeProduto('');
        setArquivo(null);
        document.getElementById('file-input').value = '';
      } else {
        setErro(data.detail || 'Erro ao importar peças');
      }
    } catch (error) {
      setErro(error.response?.data?.detail || 'Erro de conexão com o servidor');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="importar-pecas">
      <div className="importar-container">
        <h2>📤 Importar Lista de Peças</h2>
        <p className="subtitulo">Importe o Excel do CargaMaquina</p>

        <form onSubmit={handleSubmit} className="importar-form">
          <div className="form-group">
            <label>Código do Produto *</label>
            <input
              type="text"
              value={codigoProduto}
              onChange={(e) => setCodigoProduto(e.target.value)}
              placeholder="Ex: 8100015098"
              required
            />
          </div>

          <div className="form-group">
            <label>Nome do Produto (opcional)</label>
            <input
              type="text"
              value={nomeProduto}
              onChange={(e) => setNomeProduto(e.target.value)}
              placeholder="Ex: Kit Cozinha Austin 2.20"
            />
          </div>

          <div className="form-group">
            <label>Arquivo Excel *</label>
            <div className="file-input-wrapper">
              <input
                type="file"
                id="file-input"
                accept=".xlsx,.xls,.csv"
                onChange={handleFileChange}
                required
              />
              <label htmlFor="file-input" className="file-label">
                {arquivo ? arquivo.name : '📎 Escolher arquivo Excel'}
              </label>
            </div>
          </div>

          {erro && (
            <div className="alerta erro">
              ❌ {erro}
            </div>
          )}

          {resultado && (
            <div className="alerta sucesso">
              ✅ {resultado.message}
              <br />
              <small>Produto: {resultado.codigo_produto}</small>
            </div>
          )}

          <button 
            type="submit" 
            className="btn-importar"
            disabled={loading}
          >
            {loading ? '⏳ Importando...' : '🚀 Importar Peças'}
          </button>
        </form>

        <div className="dica">
          <strong>💡 Dica:</strong> O arquivo deve conter as colunas: Peça, Material, C, L, Cod. Peça e Família
        </div>
      </div>
    </div>
  );
}

export default ImportarPecas;