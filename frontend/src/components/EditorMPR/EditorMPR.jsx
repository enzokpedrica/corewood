import React, { useState } from 'react';
import Canvas from './Canvas';
import './EditorMPR.css';
import { exportarMPR, gerarPDFEditor } from '../../services/api';
import FuroManual from './FuroManual';

function EditorMPR() {
  const [peca, setPeca] = useState({
    nome: '',
    largura: 0,
    comprimento: 0,
    espessura: 15,
    furos: []
  });

  const [selectedTool, setSelectedTool] = useState(null);
  const [selectedFuro, setSelectedFuro] = useState(null);
  const [showFuroConfig, setShowFuroConfig] = useState(false);

  // Atualizar dimensões da peça
  const handleDimensaoChange = (campo, valor) => {
    setPeca({
      ...peca,
      [campo]: parseFloat(valor) || 0
    });
  };

  // Adicionar furo ao clicar no canvas
  const handleAddFuro = (novoFuro) => {
    const furoComId = {
      ...novoFuro,
      id: Date.now()
    };
    
    setPeca({
      ...peca,
      furos: [...peca.furos, furoComId]
    });

    // Abrir painel de configuração
    setSelectedFuro(furoComId);
    setShowFuroConfig(true);
    setSelectedTool(null); // Desativar ferramenta após adicionar
  };

  // Atualizar configuração de furo
  const handleUpdateFuro = (campo, valor) => {
    if (!selectedFuro) return;

    setPeca({
      ...peca,
      furos: peca.furos.map(f => 
        f.id === selectedFuro.id 
          ? { ...f, [campo]: parseFloat(valor) || valor }
          : f
      )
    });

    setSelectedFuro({
      ...selectedFuro,
      [campo]: parseFloat(valor) || valor
    });
  };

  // Remover furo
  const handleRemoveFuro = (furoId) => {
    setPeca({
      ...peca,
      furos: peca.furos.filter(f => f.id !== furoId)
    });
    
    if (selectedFuro?.id === furoId) {
      setSelectedFuro(null);
      setShowFuroConfig(false);
    }
  };

  // Exportar MPR
const handleExportarMPR = async () => {
  if (!peca.nome || !peca.largura || !peca.comprimento) {
    alert('⚠️ Preencha nome e dimensões da peça!');
    return;
  }

  if (peca.furos.length === 0) {
    alert('⚠️ Adicione pelo menos um furo!');
    return;
  }

  try {
    console.log('📤 Exportando MPR:', peca);
    
    const mprBlob = await exportarMPR(peca);
    
    // Download automático
    const url = window.URL.createObjectURL(mprBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${peca.nome}.mpr`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
    
    alert('✅ MPR exportado com sucesso!');
  } catch (error) {
    console.error('Erro ao exportar MPR:', error);
    alert(`❌ Erro ao exportar MPR:\n${error.response?.data?.detail || error.message}`);
  }
};

  // Gerar PDF direto
  const handleGerarPDF = async () => {
    if (!peca.nome || !peca.largura || !peca.comprimento) {
      alert('⚠️ Preencha nome e dimensões da peça!');
      return;
    }

    if (peca.furos.length === 0) {
      alert('⚠️ Adicione pelo menos um furo!');
      return;
    }

    try {
      console.log('📄 Gerando PDF:', peca);
      
      const pdfBlob = await gerarPDFEditor(peca);
      
      // Download automático
      const url = window.URL.createObjectURL(pdfBlob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${peca.nome}_furacao.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      alert('✅ PDF gerado com sucesso!');
    } catch (error) {
      console.error('Erro ao gerar PDF:', error);
      alert(`❌ Erro ao gerar PDF:\n${error.response?.data?.detail || error.message}`);
    }
  };

  // Limpar tudo
  const handleNovaPeca = () => {
    if (peca.furos.length > 0) {
      if (!window.confirm('Descartar peça atual e começar nova?')) {
        return;
      }
    }
    
    setPeca({
      nome: '',
      largura: 0,
      comprimento: 0,
      espessura: 15,
      furos: []
    });
    setSelectedFuro(null);
    setShowFuroConfig(false);
    setSelectedTool(null);
  };

  return (
    <div className="editor-mpr">
      <div className="editor-header">
        <h2>✏️ Editor de Peças MPR</h2>
        <p>Crie peças visualmente e exporte para MPR ou gere PDF direto</p>
      </div>

      <div className="editor-layout">
        {/* SIDEBAR ESQUERDA - Dimensões e Ferramentas */}
        <div className="editor-sidebar left">
          <div className="editor-section">
            <h3>📏 Dimensões da Peça</h3>
            
            <div className="form-group">
              <label>Nome da Peça:</label>
              <input
                type="text"
                value={peca.nome}
                onChange={(e) => setPeca({ ...peca, nome: e.target.value })}
                placeholder="Ex: LATERAL_01"
              />
            </div>

            <div className="form-group">
              <label>Largura (mm):</label>
              <input
                type="number"
                value={peca.largura || ''}
                onChange={(e) => handleDimensaoChange('largura', e.target.value)}
                placeholder="Ex: 300"
                min="10"
                max="3000"
              />
            </div>

            <div className="form-group">
              <label>Comprimento (mm):</label>
              <input
                type="number"
                value={peca.comprimento || ''}
                onChange={(e) => handleDimensaoChange('comprimento', e.target.value)}
                placeholder="Ex: 800"
                min="10"
                max="3000"
              />
            </div>

            <div className="form-group">
              <label>Espessura (mm):</label>
              <input
                type="number"
                value={peca.espessura || 15}
                onChange={(e) => handleDimensaoChange('espessura', e.target.value)}
                min="6"
                max="50"
              />
            </div>
          </div>

          <div className="editor-section">
            <h3>🔧 Ferramentas</h3>
            
            <button
              className={`tool-button ${selectedTool === 'vertical' ? 'active' : ''}`}
              onClick={() => setSelectedTool(selectedTool === 'vertical' ? null : 'vertical')}
              disabled={!peca.largura || !peca.comprimento}
            >
              🔴 Furo Vertical
            </button>

            <button
              className={`tool-button ${selectedTool === 'horizontal' ? 'active' : ''}`}
              onClick={() => setSelectedTool(selectedTool === 'horizontal' ? null : 'horizontal')}
              disabled={!peca.largura || !peca.comprimento}
            >
              🔵 Furo Horizontal
            </button>

            <div className="tool-hint">
              {selectedTool ? (
                <p>✨ Clique na peça para adicionar furo</p>
              ) : (
                <p>💡 Selecione uma ferramenta acima</p>
              )}
            </div>
          </div>

          {/* Adicionar Furo Manual */}
          {peca.largura && peca.comprimento && (
            <div className="editor-section">
              <FuroManual 
                onAddFuro={handleAddFuro}
                pecaDimensoes={{
                  comprimento: peca.comprimento,
                  largura: peca.largura
                }}
              />
            </div>
          )}

          <div className="editor-section">
            <h3>📊 Resumo</h3>
            <div className="resumo">
              <p><strong>Furos verticais:</strong> {peca.furos.filter(f => f.tipo === 'vertical').length}</p>
              <p><strong>Furos horizontais:</strong> {peca.furos.filter(f => f.tipo === 'horizontal').length}</p>
              <p><strong>Total:</strong> {peca.furos.length}</p>
            </div>
          </div>
        </div>

        {/* CENTRO - Canvas */}
        <div className="editor-center">
          <Canvas
            peca={peca}
            onAddFuro={handleAddFuro}
            selectedTool={selectedTool}
          />
        </div>

        {/* SIDEBAR DIREITA - Config de Furo */}
        <div className="editor-sidebar right">
          {showFuroConfig && selectedFuro ? (
            <div className="editor-section">
              <div className="section-header">
                <h3>⚙️ Configurar Furo</h3>
                <button 
                  className="btn-close"
                  onClick={() => {
                    setShowFuroConfig(false);
                    setSelectedFuro(null);
                  }}
                >
                  ✕
                </button>
              </div>

              <div className="furo-info">
                <span className={`furo-badge ${selectedFuro.tipo}`}>
                  {selectedFuro.tipo === 'vertical' ? '🔴 Vertical' : '🔵 Horizontal'}
                </span>
              </div>

              <div className="form-group">
                <label>Posição X (mm):</label>
                <input
                  type="number"
                  value={selectedFuro.x}
                  onChange={(e) => handleUpdateFuro('x', e.target.value)}
                  step="0.1"
                />
              </div>

              <div className="form-group">
                <label>Posição Y (mm):</label>
                <input
                  type="number"
                  value={selectedFuro.y}
                  onChange={(e) => handleUpdateFuro('y', e.target.value)}
                  step="0.1"
                />
              </div>

              <div className="form-group">
                <label>Diâmetro (mm):</label>
                <input
                  type="number"
                  value={selectedFuro.diametro}
                  onChange={(e) => handleUpdateFuro('diametro', e.target.value)}
                  step="0.1"
                  min="1"
                  max="50"
                />
              </div>

              <div className="form-group">
                <label>Profundidade (mm):</label>
                <input
                  type="number"
                  value={selectedFuro.profundidade}
                  onChange={(e) => handleUpdateFuro('profundidade', e.target.value)}
                  step="0.1"
                  min="0"
                />
                <small>0 = passante</small>
              </div>

              {selectedFuro.tipo === 'horizontal' && (
                <div className="form-group">
                  <label>Lado:</label>
                  <select
                    value={selectedFuro.lado}
                    onChange={(e) => handleUpdateFuro('lado', e.target.value)}
                  >
                    <option value="XP">XP (Frente)</option>
                    <option value="XM">XM (Trás)</option>
                    <option value="YP">YP (Direita)</option>
                    <option value="YM">YM (Esquerda)</option>
                  </select>
                </div>
              )}

              <button
                className="btn-danger"
                onClick={() => handleRemoveFuro(selectedFuro.id)}
              >
                🗑️ Remover Furo
              </button>
            </div>
          ) : (
            <div className="editor-section placeholder">
              <p>👈 Adicione um furo para configurar</p>
            </div>
          )}

          {/* Lista de Furos */}
          {peca.furos.length > 0 && (
            <div className="editor-section furos-list">
              <h3>📋 Lista de Furos</h3>
              <div className="furos-scroll">
                {peca.furos.map((furo, index) => (
                  <div
                    key={furo.id}
                    className={`furo-item ${selectedFuro?.id === furo.id ? 'selected' : ''}`}
                    onClick={() => {
                      setSelectedFuro(furo);
                      setShowFuroConfig(true);
                    }}
                  >
                    <span className={`furo-icon ${furo.tipo}`}>
                      {furo.tipo === 'vertical' ? '🔴' : '🔵'}
                    </span>
                    <div className="furo-details">
                      <strong>Furo #{index + 1}</strong>
                      <small>X:{furo.x} Y:{furo.y} Ø{furo.diametro}</small>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* FOOTER - Ações */}
      <div className="editor-footer">
        <button className="btn-secondary" onClick={handleNovaPeca}>
          🆕 Nova Peça
        </button>

        <div className="footer-actions">
          <button
            className="btn-export"
            onClick={handleExportarMPR}
            disabled={!peca.nome || peca.furos.length === 0}
          >
            💾 Exportar MPR
          </button>

          <button
            className="btn-primary"
            onClick={handleGerarPDF}
            disabled={!peca.nome || peca.furos.length === 0}
          >
            📄 Gerar PDF
          </button>
        </div>
      </div>
    </div>
  );
}

export default EditorMPR;