import React, { useState, useEffect } from 'react';
import Canvas from './Canvas';
import './EditorMPR.css';
import { exportarMPR, gerarPDFEditor } from '../../services/api';
import FuroManual from './FuroManual';
import api from '../../services/api';

function EditorMPR({ pecaInicial }) {
  const [peca, setPeca] = useState({
    nome: '',
    largura: 0,
    comprimento: 0,
    espessura: 15,
    furos: [],
    furosHorizontais: []
  });

  const [nomePeca, setNomePeca] = useState('');
  const [codigoPeca, setCodigoPeca] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (pecaInicial) {
      setPeca(prevPeca => ({
        ...prevPeca,
        nome: pecaInicial.nome || '',
        largura: parseFloat(pecaInicial.largura) || 0,
        comprimento: parseFloat(pecaInicial.comprimento) || 0,
        espessura: parseFloat(pecaInicial.espessura) || 0,
        furos: pecaInicial.furos?.verticais || [],
        furosHorizontais: pecaInicial.furos?.horizontais || []
      }));
      
      setNomePeca(pecaInicial.nome || '');
      setCodigoPeca(pecaInicial.codigo || '');
    }
  }, [pecaInicial]);
  

  const [selectedTool, setSelectedTool] = useState(null);
  const [selectedFuro, setSelectedFuro] = useState(null);
  const [showFuroConfig, setShowFuroConfig] = useState(false);
  const [transformacao, setTransformacao] = useState({rotacao: 0,espelhado: false});
  const [pecaOriginal, setPecaOriginal] = useState(null);

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

    const novosFuros = [...peca.furos, furoComId];
    
    setPeca({
      ...peca,
      furos: novosFuros
    });

    // Salvar estado original na primeira vez
    if (!pecaOriginal && novosFuros.length === 1) {
      setPecaOriginal({
        comprimento: peca.comprimento,
        largura: peca.largura,
        furos: novosFuros
      });
    }

    // Abrir painel de configuração
    setSelectedFuro(furoComId);
    setShowFuroConfig(true);
    setSelectedTool(null); // Desativar ferramenta após adicionar
  };

  // Aplicar transformação nos furos
  const aplicarTransformacao = (novaTransformacao) => {
    if (!pecaOriginal) {
      setTransformacao(novaTransformacao);
      return;
    }
    
    const rotacao = novaTransformacao.rotacao;
    const espelhado = novaTransformacao.espelhado;
    
    let novoComprimento = pecaOriginal.comprimento;
    let novaLargura = pecaOriginal.largura;
    
    // Trocar dimensões se 90° ou 270°
    if (rotacao === 90 || rotacao === 270) {
      novoComprimento = pecaOriginal.largura;
      novaLargura = pecaOriginal.comprimento;
    }
    
    const furosTransformados = pecaOriginal.furos.map(furoOrig => {
      // Coordenadas originais (origem embaixo)
      let x = furoOrig.x;
      let y = furoOrig.y;
      
      // Aplicar espelhamento
      if (espelhado) {
        x = pecaOriginal.comprimento - x;
      }
      
      // Aplicar rotação
      if (rotacao === 90) {
        // 90° horário
        const temp = x;
        x = pecaOriginal.largura - y;  // ← Ajustado!
        y = temp;
      } else if (rotacao === 180) {
        // 180°
        x = pecaOriginal.comprimento - x;
        y = pecaOriginal.largura - y;
      } else if (rotacao === 270) {
        // 270° horário
        const temp = x;
        x = y;
        y = pecaOriginal.comprimento - temp;  // ← Ajustado!
      }
      
      return {
        ...furoOrig,
        x: Math.round(x * 10) / 10,
        y: Math.round(y * 10) / 10
      };
    });
    
    setPeca({
      ...peca,
      comprimento: novoComprimento,
      largura: novaLargura,
      furos: furosTransformados
    });
    
    setTransformacao(novaTransformacao);
    
    console.log('🔄 Transformação (origem embaixo):', {
      rotacao: `${rotacao}°`,
      dimensoes: `${novoComprimento}x${novaLargura}mm`,
      furoExemplo: furosTransformados[0] ? `X:${furosTransformados[0].x} Y:${furosTransformados[0].y}` : 'nenhum'
    });
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

    if (peca.furos.length === 0 && (!peca.furosHorizontais || peca.furosHorizontais.length === 0)) {
      alert('⚠️ Adicione pelo menos um furo!');
      return;
    }

    try {
      // Juntar furos verticais e horizontais
      const todosFuros = [
        ...peca.furos,
        ...(peca.furosHorizontais || [])
      ];

      const pecaExportar = {
        ...peca,
        furos: todosFuros
      };

      console.log('📦 Dados sendo enviados:', JSON.stringify(pecaExportar, null, 2));
      console.log('📤 Exportando MPR:', pecaExportar);
      
      const mprBlob = await exportarMPR(pecaExportar);
      
      // Download automático
      const url = window.URL.createObjectURL(mprBlob);
      const link = document.createElement('a');
      link.href = url;

      // Usar código da peça se existir, senão usa nome
      const nomeArquivo = codigoPeca || peca.nome || 'peca';
      link.download = `${nomeArquivo}.mpr`;
      
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
      // DEBUG - ADICIONA AQUI
      console.log('🔍 DEBUG - pecaInicial:', pecaInicial);
      console.log('🔍 DEBUG - pecaInicial?.id:', pecaInicial?.id);
      
      console.log('📄 Gerando PDF:', peca);
      
      // NOVO: Adicionar peca_id se existir
      const pecaComId = {
        ...peca,
        peca_id: pecaInicial?.id || null
      };
      
      // DEBUG - ADICIONA AQUI
      console.log('🔍 DEBUG - pecaComId:', pecaComId);
      console.log('🔍 DEBUG - peca_id enviado:', pecaComId.peca_id);
      
      const pdfBlob = await gerarPDFEditor(pecaComId);
      
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
    
    // Extrair dimensões
    const bsxMatch = text.match(/_BSX=([\d.]+)/);
    const bsyMatch = text.match(/_BSY=([\d.]+)/);
    const bszMatch = text.match(/_BSZ=([\d.]+)/);
    
    const comprimento = bsxMatch ? parseFloat(bsxMatch[1]) : 0;
    const largura = bsyMatch ? parseFloat(bsyMatch[1]) : 0;
    const espessura = bszMatch ? parseFloat(bszMatch[1]) : 15;
    
    // Dividir por blocos de operação
    const blocos = text.split(/(?=<\d{3}\s)/);
    
    const furosVerticais = [];
    const furosHorizontais = [];
    
    for (const bloco of blocos) {
      // ===== FURO VERTICAL (102) =====
      if (bloco.includes('<102') && bloco.includes('BohrVert')) {
        const xa = bloco.match(/XA="([\d.]+)"/);
        const ya = bloco.match(/YA="([\d.]+)"/);
        const du = bloco.match(/DU="([\d.]+)"/);
        const ti = bloco.match(/TI="([\d.]+)"/);
        const an = bloco.match(/AN="(\d+)"/);
        const ab = bloco.match(/AB="([\d.]+)"/);
        const wi = bloco.match(/WI="(\d+)"/);
        const bm = bloco.match(/BM="([^"]+)"/);
        
        if (xa && ya && du) {
          const x = parseFloat(xa[1]);
          const y = parseFloat(ya[1]);
          const diametro = parseFloat(du[1]);
          const profundidade = ti ? parseFloat(ti[1]) : 0;
          const quantidade = an ? parseInt(an[1]) : 1;
          const distancia = ab ? parseFloat(ab[1]) : 0;
          const angulo = wi ? parseInt(wi[1]) : 0;
          const lado = bm ? bm[1] : 'LS';
          
          // Expandir furos replicados
          for (let i = 0; i < quantidade; i++) {
            furosVerticais.push({
              id: Date.now() + Math.random(),
              tipo: 'vertical',
              x: angulo === 0 ? x + (distancia * i) : x,
              y: angulo === 90 ? y + (distancia * i) : y,
              diametro,
              profundidade,
              lado
            });
          }
        }
      }
      
      // ===== FURO HORIZONTAL (103) =====
      if (bloco.includes('<103') && bloco.includes('BohrHoriz')) {
        const xa = bloco.match(/XA="([^"]+)"/);
        const ya = bloco.match(/YA="([\d.]+)"/);
        const za = bloco.match(/ZA="([\d.]+)"/);
        const du = bloco.match(/DU="([\d.]+)"/);
        const ti = bloco.match(/TI="([\d.]+)"/);
        const an = bloco.match(/AN="(\d+)"/);
        const ab = bloco.match(/AB="([\d.]+)"/);
        const wi = bloco.match(/WI="(\d+)"/);
        const bm = bloco.match(/BM="([^"]+)"/);
        
        if (ya && za && du) {
          const xVal = xa ? xa[1] : '0';
          const x = xVal === 'x' ? 'x' : parseFloat(xVal);
          const y = parseFloat(ya[1]);
          const z = parseFloat(za[1]);
          const diametro = parseFloat(du[1]);
          const profundidade = ti ? parseFloat(ti[1]) : 0;
          const quantidade = an ? parseInt(an[1]) : 1;
          const distancia = ab ? parseFloat(ab[1]) : 0;
          const angulo = wi ? parseInt(wi[1]) : 90;
          const lado = bm ? bm[1] : 'XP';
          
          // Expandir furos replicados
          for (let i = 0; i < quantidade; i++) {
            furosHorizontais.push({
              id: Date.now() + Math.random(),
              tipo: 'horizontal',
              x: xVal === 'x' ? 'x' : (angulo === 0 ? x + (distancia * i) : x),
              y: angulo === 90 ? y + (distancia * i) : y,
              z,
              diametro,
              profundidade,
              lado
            });
          }
        }
      }
    }

    setPeca({
      nome: file.name.replace('.mpr', '').replace('.MPR', ''),
      largura,
      comprimento,
      espessura,
      furos: furosVerticais,
      furosHorizontais: furosHorizontais
    });
    
    alert(`✅ MPR importado!\n${furosVerticais.length} furos verticais\n${furosHorizontais.length} furos horizontais`);
    
  } catch (error) {
    console.error('Erro:', error);
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

  const handleSalvarPeca = async () => {
  if (!pecaInicial?.id) {
    alert('⚠️ Peça não identificada para salvar');
    return;
  }

  setLoading(true);

  try {
    const formData = new FormData();
    formData.append('largura', peca.largura);
    formData.append('comprimento', peca.comprimento);
    formData.append('espessura', peca.espessura);
    formData.append('furos', JSON.stringify({
      verticais: peca.furos || [],
      horizontais: peca.furosHorizontais || []
    }));

    const response = await api.put(
      `/pecas/${pecaInicial.id}/salvar`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      }
    );

    if (response.status === 200) {
      alert('✅ Peça salva com sucesso!');
    } else {
      alert('❌ Erro ao salvar peça');
    }
  } catch (error) {
    console.error(error);
    alert('❌ Erro ao salvar: ' + (error.response?.data?.detail || error.message));
  } finally {
    setLoading(false);
  }
};
  return (
    <div className="editor-mpr">
      {/* HEADER */}
      <div className="editor-header">
        <h2>✏️ Editor MPR</h2>
      </div>

      {/* CANVAS - TOPO */}
      <div className="editor-canvas-area">
        <Canvas
          peca={peca}
          onAddFuro={handleAddFuro}
          selectedTool={selectedTool}
        />
      </div>

      {/* PAINEL INFERIOR - 3 COLUNAS */}
      <div className="editor-panel">
        {/* COLUNA 1 - Informações da Peça */}
        <div className="panel-section">
          <h3>📋 Informações da Peça</h3>
          
          <div className="form-row">
            <div className="form-group">
              <label>Código</label>
              <input
                type="text"
                value={codigoPeca}
                onChange={(e) => setCodigoPeca(e.target.value)}
                placeholder="510536001"
              />
            </div>
            <div className="form-group">
              <label>Nome</label>
              <input
                type="text"
                value={peca.nome}
                onChange={(e) => setPeca({ ...peca, nome: e.target.value })}
                placeholder="Lateral Direita"
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Comprimento X</label>
              <input
                type="number"
                value={peca.comprimento || ''}
                onChange={(e) => handleDimensaoChange('comprimento', e.target.value)}
                placeholder="800"
              />
            </div>
            <div className="form-group">
              <label>Largura Y</label>
              <input
                type="number"
                value={peca.largura || ''}
                onChange={(e) => handleDimensaoChange('largura', e.target.value)}
                placeholder="300"
              />
            </div>
            <div className="form-group">
              <label>Espessura</label>
              <input
                type="number"
                value={peca.espessura || 15}
                onChange={(e) => handleDimensaoChange('espessura', e.target.value)}
              />
            </div>
          </div>

          <div className="transform-section">
            <label>🔄 Transformar</label>
            <div className="transform-buttons">
              <button
                className="transform-btn"
                onClick={() => aplicarTransformacao({ 
                  ...transformacao, 
                  rotacao: (transformacao.rotacao + 90) % 360 
                })}
                title="Rotacionar 90°"
              >
                ↻ 90°
              </button>
              <button
                className="transform-btn"
                onClick={() => aplicarTransformacao({ 
                  ...transformacao, 
                  rotacao: (transformacao.rotacao + 180) % 360 
                })}
                title="Rotacionar 180°"
              >
                ↕ 180°
              </button>
              <button
                className="transform-btn"
                onClick={() => aplicarTransformacao({ 
                  ...transformacao, 
                  espelhado: !transformacao.espelhado 
                })}
                title="Espelhar"
              >
                ⇄ Espelhar
              </button>
            </div>
            <small>Rotação: {transformacao.rotacao}° | Espelhado: {transformacao.espelhado ? 'Sim' : 'Não'}</small>
          </div>
        </div>

        {/* COLUNA 2 - Adicionar Furação */}
        <div className="panel-section">
          <h3>➕ Adicionar Furação</h3>
          
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
              <p>Defina as dimensões primeiro</p>
            </div>
          )}

          {/* Lista de Furos */}
          <div className="furos-lista">
            <label>Lista de Furos ({peca.furos.length + (peca.furosHorizontais?.length || 0)})</label>
            <div className="furos-scroll">
              {[...peca.furos, ...(peca.furosHorizontais || [])].map((furo, index) => (
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
                  <span className="furo-info">
                    {furo.tipo === 'vertical' ? 'V' : 'H'}#{index + 1} 
                    {furo.tipo === 'vertical' 
                      ? ` X:${furo.x} Y:${furo.y} Ø${furo.diametro}`
                      : ` Y:${furo.y} Z:${furo.z} Ø${furo.diametro}`
                    }
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* COLUNA 3 - Configurar Furo */}
        <div className="panel-section">
          <h3>⚙️ Configurar Furo</h3>
          
          {showFuroConfig && selectedFuro ? (
            <div className="furo-config">
              <div className="furo-badge">
                {selectedFuro.tipo === 'vertical' ? '🔴 Vertical' : '🔵 Horizontal'}
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>X</label>
                  <input
                    type="number"
                    value={selectedFuro.x}
                    onChange={(e) => handleUpdateFuro('x', e.target.value)}
                    step="0.1"
                  />
                </div>
                <div className="form-group">
                  <label>Y</label>
                  <input
                    type="number"
                    value={selectedFuro.y}
                    onChange={(e) => handleUpdateFuro('y', e.target.value)}
                    step="0.1"
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Diâmetro</label>
                  <input
                    type="number"
                    value={selectedFuro.diametro}
                    onChange={(e) => handleUpdateFuro('diametro', e.target.value)}
                    step="0.1"
                  />
                </div>
                <div className="form-group">
                  <label>Profundidade</label>
                  <input
                    type="number"
                    value={selectedFuro.profundidade}
                    onChange={(e) => handleUpdateFuro('profundidade', e.target.value)}
                    step="0.1"
                  />
                </div>
              </div>

              {selectedFuro.tipo === 'horizontal' && (
                <div className="form-group">
                  <label>Lado</label>
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

              {/* Replicação */}
              <div className="replicacao-section">
                <label>🔁 Replicar</label>
                <div className="form-row">
                  <input
                    type="number"
                    placeholder="Qtd"
                    min="2"
                    max="20"
                    id="replicar-qtd"
                  />
                  <input
                    type="number"
                    placeholder="Dist"
                    step="0.1"
                    id="replicar-dist"
                  />
                  <select id="replicar-dir">
                    <option value="x">X</option>
                    <option value="y">Y</option>
                  </select>
                </div>
                <button
                  className="btn-replicar"
                  onClick={() => {
                    const qtd = parseInt(document.getElementById('replicar-qtd').value);
                    const dist = parseFloat(document.getElementById('replicar-dist').value);
                    const dir = document.getElementById('replicar-dir').value;
                    
                    if (!qtd || !dist) {
                      alert('⚠️ Preencha quantidade e distância!');
                      return;
                    }
                    
                    const novosFuros = [];
                    for (let i = 1; i < qtd; i++) {
                      novosFuros.push({
                        ...selectedFuro,
                        id: Date.now() + i,
                        x: selectedFuro.x + (dir === 'x' ? dist * i : 0),
                        y: selectedFuro.y + (dir === 'y' ? dist * i : 0)
                      });
                    }

                    setPeca({ ...peca, furos: [...peca.furos, ...novosFuros] });
                    alert(`✅ ${qtd-1} furos replicados!`);
                  }}
                >
                  🔁 Aplicar
                </button>
              </div>

              <button
                className="btn-danger"
                onClick={() => handleRemoveFuro(selectedFuro.id)}
              >
                🗑️ Remover Furo
              </button>
            </div>
          ) : (
            <div className="placeholder">
              <p>Selecione um furo na lista</p>
            </div>
          )}
        </div>
      </div>

      {/* FOOTER - Ações */}
      <div className="editor-footer">
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

        {pecaInicial && (
          <button
            className="btn-secondary"
            onClick={handleSalvarPeca}
            disabled={loading}
          >
            💾 Salvar
          </button>
        )}

        <button
          className="btn-export"
          onClick={handleExportarMPR}
          disabled={!peca.nome || (peca.furos.length === 0 && (!peca.furosHorizontais || peca.furosHorizontais.length === 0))}
        >
          📤 Exportar MPR
        </button>

        <button
          className="btn-primary"
          onClick={handleGerarPDF}
          disabled={!peca.nome && !nomePeca}
        >
          📄 Gerar PDF
        </button>
      </div>
    </div>
  );
}

export default EditorMPR;