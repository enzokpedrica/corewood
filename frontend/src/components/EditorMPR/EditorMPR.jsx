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

  const handleImportarMPR = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    try {
      const text = await file.text();
      
      // Parse básico do MPR
      const lines = text.split('\n');
      
      // Extrair dimensões
      const bsxMatch = text.match(/_BSX=([\d.]+)/);
      const bsyMatch = text.match(/_BSY=([\d.]+)/);
      const bszMatch = text.match(/_BSZ=([\d.]+)/);
      
      const comprimento = bsxMatch ? parseFloat(bsxMatch[1]) : 0;
      const largura = bsyMatch ? parseFloat(bsyMatch[1]) : 0;
      const espessura = bszMatch ? parseFloat(bszMatch[1]) : 15;
      
      // Extrair furos verticais (102)
      const furosImportados = [];
      const furoMatches = text.matchAll(/<102[^<]*XA="([\d.]+)"[^<]*YA="([\d.]+)"[^<]*DU="([\d.]+)"(?:[^<]*TI="([\d.]+)")?/g);
      
      for (const match of furoMatches) {
        furosImportados.push({
          id: Date.now() + Math.random(),
          tipo: 'vertical',
          x: parseFloat(match[1]),
          y: parseFloat(match[2]),
          diametro: parseFloat(match[3]),
          profundidade: match[4] ? parseFloat(match[4]) : 0
        });
      }
      
      setPeca({
        nome: file.name.replace('.mpr', '').replace('.MPR', ''),
        largura,
        comprimento,
        espessura,
        furos: furosImportados
      });
      
      alert(`✅ MPR importado!\n${furosImportados.length} furos carregados.`);
      
    } catch (error) {
      alert('❌ Erro ao importar MPR: ' + error.message);
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
              <label>Comprimento X (mm):</label>
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
              <label>Largura Y (mm):</label>
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
        </div>

        {/* CENTRO - Canvas Grande */}
        <div className="editor-center">
          <Canvas
            peca={peca}
            onAddFuro={handleAddFuro}
            selectedTool={selectedTool}
          />
        </div>

        {/* ÁREA INFERIOR - Adicionar Furos + Lista */}
        <div className="editor-bottom">
          {/* Adicionar Furo Manual */}
          <div className="editor-section">
            {peca.largura && peca.comprimento ? (
              <FuroManual 
                onAddFuro={handleAddFuro}
                pecaDimensoes={{
                  comprimento: peca.comprimento,
                  largura: peca.largura
                }}
              />
            ) : (
              <div className="placeholder">
                <p>👈 Defina as dimensões da peça primeiro</p>
              </div>
            )}
          </div>

          {/* Lista de Furos + Config */}
          <div className="editor-section">
            {showFuroConfig && selectedFuro ? (
              <div>
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
              <div>
                <h3>📋 Lista de Furos ({peca.furos.length})</h3>
                {peca.furos.length > 0 ? (
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
                ) : (
                  <div className="placeholder">
                    <p>Nenhum furo adicionado ainda</p>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* FOOTER - Ações */}
      <div className="editor-footer">
        {/* Botão Importar MPR */}
        <input
          type="file"
          accept=".mpr,.MPR"
          onChange={handleImportarMPR}
          style={{ display: 'none' }}
          id="import-mpr"
        />
        <label htmlFor="import-mpr" className="btn-secondary">
          📂 Importar MPR
        </label>

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