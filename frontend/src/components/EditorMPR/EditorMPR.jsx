import React, { useState, useEffect, useCallback } from 'react';
import Canvas3D from './Canvas3D';
import FurosList from './FurosList';
import FuroManual from './FuroManual';
import './EditorMPR.css';
import { exportarMPR, gerarPDFEditor } from '../../services/api';
import api from '../../services/api';

function EditorMPR({ pecaInicial, onVoltar }) {
  // ========================================
  // ESTADOS
  // ========================================
  const [peca, setPeca] = useState({
    nome: '',
    largura: 0,
    comprimento: 0,
    espessura: 15,
    furos: [],
    furosHorizontais: []
  });

  const [bordas, setBordas] = useState({
    topo: 'nenhum',
    baixo: 'nenhum',
    esquerda: 'nenhum',
    direita: 'nenhum'
  });

  const [codigoPeca, setCodigoPeca] = useState('');
  const [loading, setLoading] = useState(false);
  const [alerta, setAlerta] = useState(false);
  const [observacoes, setObservacoes] = useState('');
  const [selectedFuro, setSelectedFuro] = useState(null);
  const [transformacao, setTransformacao] = useState({ rotacao: 0, espelhado: false });
  const [pecaOriginal, setPecaOriginal] = useState(null);

  // Larguras dos painéis (para resize)
  const [sidebarWidth, setSidebarWidth] = useState(260);
  const [panelHeight, setPanelHeight] = useState(280);

  // ========================================
  // CARREGAR PEÇA INICIAL
  // ========================================
  useEffect(() => {
    if (pecaInicial) {
      setPeca(prevPeca => ({
        ...prevPeca,
        nome: pecaInicial.nome || '',
        largura: parseFloat(pecaInicial.largura) || 0,
        comprimento: parseFloat(pecaInicial.comprimento) || 0,
        espessura: parseFloat(pecaInicial.espessura) || 15,
        furos: pecaInicial.furos?.verticais || [],
        furosHorizontais: pecaInicial.furos?.horizontais || []
      }));

      setCodigoPeca(pecaInicial.codigo || '');
      setAlerta(pecaInicial.alerta || false);
      setObservacoes(pecaInicial.observacoes || '');

      if (pecaInicial.bordas) {
        setBordas({
          topo: pecaInicial.bordas.topo || 'nenhum',
          baixo: pecaInicial.bordas.baixo || 'nenhum',
          esquerda: pecaInicial.bordas.esquerda || 'nenhum',
          direita: pecaInicial.bordas.direita || 'nenhum'
        });
      }

      if (pecaInicial.transformacao) {
        setTransformacao({
          rotacao: pecaInicial.transformacao.rotacao || 0,
          espelhado: pecaInicial.transformacao.espelhado || false
        });
      }
    }
  }, [pecaInicial]);

  // ========================================
  // HANDLERS DE DIMENSÕES
  // ========================================
  const handleDimensaoChange = (campo, valor) => {
    setPeca({
      ...peca,
      [campo]: parseFloat(valor) || 0
    });
  };

  // ========================================
  // HANDLERS DE FUROS
  // ========================================
  const handleAddFuro = (novoFuro) => {
    const furoComId = {
      ...novoFuro,
      id: Date.now()
    };

    if (novoFuro.tipo === 'horizontal') {
      const novosFuros = [...(peca.furosHorizontais || []), furoComId];
      setPeca({
        ...peca,
        furosHorizontais: novosFuros
      });
    } else {
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
    }

    // Selecionar o furo recém-adicionado
    setSelectedFuro({
      tipo: novoFuro.tipo || 'vertical',
      index: novoFuro.tipo === 'horizontal' 
        ? (peca.furosHorizontais?.length || 0) 
        : peca.furos.length,
      furo: furoComId
    });
  };

  const handleSelectFuro = useCallback((furoData) => {
    setSelectedFuro(furoData);
  }, []);

  const handleDeleteFuro = useCallback((tipo, index) => {
    if (tipo === 'vertical') {
      setPeca(prev => ({
        ...prev,
        furos: prev.furos.filter((_, i) => i !== index)
      }));
    } else {
      setPeca(prev => ({
        ...prev,
        furosHorizontais: prev.furosHorizontais.filter((_, i) => i !== index)
      }));
    }
    setSelectedFuro(null);
  }, []);

  const handleUpdateFuro = (campo, valor) => {
    if (!selectedFuro) return;

    const novoValor = campo === 'x' && valor === 'x' ? 'x' : (parseFloat(valor) || valor);

    if (selectedFuro.tipo === 'horizontal') {
      const novosFuros = [...(peca.furosHorizontais || [])];
      novosFuros[selectedFuro.index] = {
        ...novosFuros[selectedFuro.index],
        [campo]: novoValor
      };
      setPeca({ ...peca, furosHorizontais: novosFuros });
      setSelectedFuro({
        ...selectedFuro,
        furo: { ...selectedFuro.furo, [campo]: novoValor }
      });
    } else {
      const novosFuros = [...peca.furos];
      novosFuros[selectedFuro.index] = {
        ...novosFuros[selectedFuro.index],
        [campo]: novoValor
      };
      setPeca({ ...peca, furos: novosFuros });
      setSelectedFuro({
        ...selectedFuro,
        furo: { ...selectedFuro.furo, [campo]: novoValor }
      });
    }
  };

  // Replicar furo
  const handleReplicarFuro = (qtd, dist, dir) => {
    if (!selectedFuro || !qtd || !dist) {
      alert('⚠️ Selecione um furo e preencha quantidade e distância!');
      return;
    }

    const novosFuros = [];
    for (let i = 1; i < qtd; i++) {
      novosFuros.push({
        ...selectedFuro.furo,
        id: Date.now() + i,
        x: selectedFuro.furo.x === 'x' ? 'x' : selectedFuro.furo.x + (dir === 'x' ? dist * i : 0),
        y: selectedFuro.furo.y + (dir === 'y' ? dist * i : 0)
      });
    }

    if (selectedFuro.tipo === 'horizontal') {
      setPeca({ ...peca, furosHorizontais: [...(peca.furosHorizontais || []), ...novosFuros] });
    } else {
      setPeca({ ...peca, furos: [...peca.furos, ...novosFuros] });
    }
    
    alert(`✅ ${qtd - 1} furos replicados!`);
  };

  // ========================================
  // TRANSFORMAÇÕES
  // ========================================
  const aplicarTransformacao = (novaTransformacao) => {
    if (!pecaOriginal) {
      setTransformacao(novaTransformacao);
      return;
    }

    const rotacao = novaTransformacao.rotacao;
    const espelhado = novaTransformacao.espelhado;

    let novoComprimento = pecaOriginal.comprimento;
    let novaLargura = pecaOriginal.largura;

    if (rotacao === 90 || rotacao === 270) {
      novoComprimento = pecaOriginal.largura;
      novaLargura = pecaOriginal.comprimento;
    }

    const furosTransformados = pecaOriginal.furos.map(furoOrig => {
      let x = furoOrig.x;
      let y = furoOrig.y;

      if (espelhado) {
        x = pecaOriginal.comprimento - x;
      }

      if (rotacao === 90) {
        const temp = x;
        x = pecaOriginal.largura - y;
        y = temp;
      } else if (rotacao === 180) {
        x = pecaOriginal.comprimento - x;
        y = pecaOriginal.largura - y;
      } else if (rotacao === 270) {
        const temp = x;
        x = y;
        y = pecaOriginal.comprimento - temp;
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
  };

  // ========================================
  // IMPORTAR MPR
  // ========================================
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
        // FURO VERTICAL (102)
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

        // FURO HORIZONTAL (103)
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

      // Salvar estado original para transformações
      setPecaOriginal({
        comprimento,
        largura,
        furos: furosVerticais
      });

      setSelectedFuro(null);
      alert(`✅ MPR importado!\n${furosVerticais.length} furos verticais\n${furosHorizontais.length} furos horizontais`);

    } catch (error) {
      console.error('Erro:', error);
      alert('❌ Erro ao importar MPR: ' + error.message);
    }

    e.target.value = '';
  };

  // ========================================
  // EXPORTAR MPR
  // ========================================
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
      const todosFuros = [
        ...peca.furos,
        ...(peca.furosHorizontais || [])
      ];

      const pecaExportar = {
        ...peca,
        furos: todosFuros
      };

      const mprBlob = await exportarMPR(pecaExportar);

      const url = window.URL.createObjectURL(mprBlob);
      const link = document.createElement('a');
      link.href = url;
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

  // ========================================
  // GERAR PDF
  // ========================================
  const handleGerarPDF = async () => {
    if (!peca.nome || !peca.largura || !peca.comprimento) {
      alert('⚠️ Preencha nome e dimensões da peça!');
      return;
    }

    if (peca.furos.length === 0 && (!peca.furosHorizontais || peca.furosHorizontais.length === 0)) {
      alert('⚠️ Adicione pelo menos um furo!');
      return;
    }

    try {
      const pecaComId = {
        ...peca,
        peca_id: pecaInicial?.id || null,
        bordas: bordas,
        transformacao: transformacao,
        alerta: alerta,
        observacoes: observacoes
      };

      const pdfBlob = await gerarPDFEditor(pecaComId);

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

  // ========================================
  // SALVAR PEÇA
  // ========================================
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
      formData.append('bordas', JSON.stringify(bordas));
      formData.append('transformacao', JSON.stringify(transformacao));
      formData.append('alerta', alerta ? 'true' : 'false');
      formData.append('observacoes', observacoes || '');

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

  // ========================================
  // NOVA PEÇA
  // ========================================
  const handleNovaPeca = () => {
    if (peca.furos.length > 0 || (peca.furosHorizontais && peca.furosHorizontais.length > 0)) {
      if (!window.confirm('Descartar peça atual e começar nova?')) {
        return;
      }
    }

    setPeca({
      nome: '',
      largura: 0,
      comprimento: 0,
      espessura: 15,
      furos: [],
      furosHorizontais: []
    });
    setBordas({
      topo: 'nenhum',
      baixo: 'nenhum',
      esquerda: 'nenhum',
      direita: 'nenhum'
    });
    setCodigoPeca('');
    setAlerta(false);
    setObservacoes('');
    setSelectedFuro(null);
    setTransformacao({ rotacao: 0, espelhado: false });
    setPecaOriginal(null);
  };

  // ========================================
  // RESIZE HANDLERS
  // ========================================
  const handleSidebarResize = useCallback((e) => {
    const startX = e.clientX;
    const startWidth = sidebarWidth;

    const onMouseMove = (moveEvent) => {
      const delta = moveEvent.clientX - startX;
      const newWidth = Math.max(200, Math.min(400, startWidth + delta));
      setSidebarWidth(newWidth);
    };

    const onMouseUp = () => {
      document.removeEventListener('mousemove', onMouseMove);
      document.removeEventListener('mouseup', onMouseUp);
    };

    document.addEventListener('mousemove', onMouseMove);
    document.addEventListener('mouseup', onMouseUp);
  }, [sidebarWidth]);

  const handlePanelResize = useCallback((e) => {
    const startY = e.clientY;
    const startHeight = panelHeight;

    const onMouseMove = (moveEvent) => {
      const delta = startY - moveEvent.clientY;
      const newHeight = Math.max(200, Math.min(500, startHeight + delta));
      setPanelHeight(newHeight);
    };

    const onMouseUp = () => {
      document.removeEventListener('mousemove', onMouseMove);
      document.removeEventListener('mouseup', onMouseUp);
    };

    document.addEventListener('mousemove', onMouseMove);
    document.addEventListener('mouseup', onMouseUp);
  }, [panelHeight]);

  // ========================================
  // RENDER
  // ========================================
  return (
    <div className="editor-mpr-container">
      {/* ==================== HEADER ==================== */}
      <header className="editor-header">
        <div className="header-left">
          {onVoltar && (
            <button className="btn-back" onClick={onVoltar}>
              ← Voltar
            </button>
          )}
          <div className="header-title">
            <input
              type="text"
              className="input-code"
              placeholder="Código"
              value={codigoPeca}
              onChange={(e) => setCodigoPeca(e.target.value)}
            />
            <input
              type="text"
              className="input-title"
              placeholder="Nome da peça"
              value={peca.nome}
              onChange={(e) => setPeca({ ...peca, nome: e.target.value })}
            />
          </div>
        </div>
        <div className="header-actions">
          <input
            type="file"
            accept=".mpr,.MPR"
            onChange={handleImportarMPR}
            style={{ display: 'none' }}
            id="import-mpr"
          />
          <label htmlFor="import-mpr" className="btn btn-secondary">
            📂 Importar MPR
          </label>
          <button className="btn btn-secondary" onClick={handleNovaPeca}>
            🆕 Nova
          </button>
          {pecaInicial && (
            <button
              className="btn btn-secondary"
              onClick={handleSalvarPeca}
              disabled={loading}
            >
              {loading ? '...' : '💾 Salvar'}
            </button>
          )}
          <button
            className="btn btn-warning"
            onClick={handleExportarMPR}
            disabled={!peca.nome || (peca.furos.length === 0 && (!peca.furosHorizontais || peca.furosHorizontais.length === 0))}
          >
            📤 Exportar MPR
          </button>
          <button
            className="btn btn-primary"
            onClick={handleGerarPDF}
            disabled={!peca.nome || (peca.furos.length === 0 && (!peca.furosHorizontais || peca.furosHorizontais.length === 0))}
          >
            📄 Gerar PDF
          </button>
        </div>
      </header>

      {/* ==================== MAIN CONTENT ==================== */}
      <div className="editor-main">
        {/* Sidebar - Lista de Furos */}
        <aside className="editor-sidebar" style={{ width: sidebarWidth }}>
          <FurosList
            furosVerticais={peca.furos}
            furosHorizontais={peca.furosHorizontais}
            selectedFuro={selectedFuro}
            onSelectFuro={handleSelectFuro}
            onDeleteFuro={handleDeleteFuro}
          />
          <div className="resize-handle-h" onMouseDown={handleSidebarResize} />
        </aside>

        {/* Canvas 3D */}
        <div className="editor-canvas-wrapper">
          <Canvas3D
            peca={peca}
            bordas={bordas}
            transformacao={transformacao}
            selectedFuro={selectedFuro}
            onSelectFuro={handleSelectFuro}
          />
        </div>
      </div>

      {/* Resize handle vertical */}
      <div className="resize-handle-v" onMouseDown={handlePanelResize} />

      {/* ==================== BOTTOM PANEL ==================== */}
      <div className="editor-panel" style={{ height: panelHeight }}>
        {/* Dimensões + Transformações + Bordas */}
        <div className="panel-card">
          <h4>📐 Dimensões</h4>
          <div className="form-grid">
            <div className="form-field">
              <label>X (Comp.)</label>
              <div className="input-with-unit">
                <input
                  type="number"
                  value={peca.comprimento || ''}
                  onChange={(e) => handleDimensaoChange('comprimento', e.target.value)}
                  placeholder="0"
                />
                <span>mm</span>
              </div>
            </div>
            <div className="form-field">
              <label>Y (Larg.)</label>
              <div className="input-with-unit">
                <input
                  type="number"
                  value={peca.largura || ''}
                  onChange={(e) => handleDimensaoChange('largura', e.target.value)}
                  placeholder="0"
                />
                <span>mm</span>
              </div>
            </div>
            <div className="form-field">
              <label>Z (Esp.)</label>
              <div className="input-with-unit">
                <input
                  type="number"
                  value={peca.espessura || ''}
                  onChange={(e) => handleDimensaoChange('espessura', e.target.value)}
                  placeholder="15"
                />
                <span>mm</span>
              </div>
            </div>
          </div>
          
          {/* Transformações inline */}
          <div className="section-divider"></div>
          <div className="transform-row">
            <span className="mini-label">🔄</span>
            <button
              className={`transform-btn-sm ${transformacao.rotacao !== 0 ? 'active' : ''}`}
              onClick={() => aplicarTransformacao({
                ...transformacao,
                rotacao: (transformacao.rotacao + 90) % 360
              })}
            >
              ↻ {transformacao.rotacao}°
            </button>
            <button
              className={`transform-btn-sm ${transformacao.espelhado ? 'active' : ''}`}
              onClick={() => aplicarTransformacao({
                ...transformacao,
                espelhado: !transformacao.espelhado
              })}
            >
              ⇄ Esp.
            </button>
          </div>

          {/* Bordas em formato retângulo */}
          <div className="section-divider"></div>
          <div className="bordas-retangulo">
            <div className="borda-topo">
              <select
                value={bordas.topo}
                onChange={(e) => setBordas({ ...bordas, topo: e.target.value })}
                className={`borda-select-sm ${bordas.topo}`}
              >
                <option value="nenhum">-</option>
                <option value="cor">Cor</option>
                <option value="pardo">Pardo</option>
              </select>
            </div>
            <div className="borda-meio">
              <select
                value={bordas.esquerda}
                onChange={(e) => setBordas({ ...bordas, esquerda: e.target.value })}
                className={`borda-select-sm ${bordas.esquerda}`}
              >
                <option value="nenhum">-</option>
                <option value="cor">Cor</option>
                <option value="pardo">Pardo</option>
              </select>
              <div className="borda-peca-icon">▭</div>
              <select
                value={bordas.direita}
                onChange={(e) => setBordas({ ...bordas, direita: e.target.value })}
                className={`borda-select-sm ${bordas.direita}`}
              >
                <option value="nenhum">-</option>
                <option value="cor">Cor</option>
                <option value="pardo">Pardo</option>
              </select>
            </div>
            <div className="borda-baixo">
              <select
                value={bordas.baixo}
                onChange={(e) => setBordas({ ...bordas, baixo: e.target.value })}
                className={`borda-select-sm ${bordas.baixo}`}
              >
                <option value="nenhum">-</option>
                <option value="cor">Cor</option>
                <option value="pardo">Pardo</option>
              </select>
            </div>
          </div>
        </div>

        {/* Alerta e Observações */}
        <div className="panel-card">
          <h4>⚠️ Alerta</h4>
          <div className="alert-section">
            <label className="checkbox-field">
              <input
                type="checkbox"
                checked={alerta}
                onChange={(e) => setAlerta(e.target.checked)}
              />
              <span className="checkbox-label">Triângulo no PDF</span>
            </label>
            <textarea
              className="observacoes-input"
              placeholder="Observações..."
              value={observacoes}
              onChange={(e) => setObservacoes(e.target.value)}
              rows={2}
            />
          </div>
        </div>

        {/* Adicionar Furo Manual */}
        <div className="panel-card">
          <h4>➕ Adicionar Furo</h4>
          {peca.largura && peca.comprimento ? (
            <FuroManual
              onAddFuro={handleAddFuro}
              pecaDimensoes={{
                comprimento: peca.comprimento,
                largura: peca.largura,
                espessura: peca.espessura
              }}
            />
          ) : (
            <div className="placeholder">
              <p>Defina as dimensões primeiro</p>
            </div>
          )}
        </div>

        {/* Configurar Furo Selecionado */}
        {selectedFuro && (
          <div className="panel-card highlight">
            <h4>
              {selectedFuro.tipo === 'vertical' ? '⬇️' : '➡️'}
              {' '}Furo {selectedFuro.tipo === 'vertical' ? 'V' : 'H'}{selectedFuro.index + 1}
            </h4>
            <div className="furo-config">
              <div className="form-row-inline">
                <div className="form-field-sm">
                  <label>X</label>
                  <input
                    type="text"
                    value={selectedFuro.furo.x}
                    onChange={(e) => handleUpdateFuro('x', e.target.value)}
                  />
                </div>
                <div className="form-field-sm">
                  <label>Y</label>
                  <input
                    type="number"
                    value={selectedFuro.furo.y}
                    onChange={(e) => handleUpdateFuro('y', e.target.value)}
                  />
                </div>
                {selectedFuro.tipo === 'horizontal' && (
                  <div className="form-field-sm">
                    <label>Z</label>
                    <input
                      type="number"
                      value={selectedFuro.furo.z || peca.espessura / 2}
                      onChange={(e) => handleUpdateFuro('z', e.target.value)}
                    />
                  </div>
                )}
              </div>
              <div className="form-row-inline">
                <div className="form-field-sm">
                  <label>Ø</label>
                  <input
                    type="number"
                    value={selectedFuro.furo.diametro}
                    onChange={(e) => handleUpdateFuro('diametro', e.target.value)}
                  />
                </div>
                <div className="form-field-sm">
                  <label>Prof.</label>
                  <input
                    type="number"
                    value={selectedFuro.furo.profundidade}
                    onChange={(e) => handleUpdateFuro('profundidade', e.target.value)}
                  />
                </div>
                {selectedFuro.tipo === 'horizontal' && (
                  <div className="form-field-sm">
                    <label>Lado</label>
                    <select
                      value={selectedFuro.furo.lado}
                      onChange={(e) => handleUpdateFuro('lado', e.target.value)}
                    >
                      <option value="XP">XP</option>
                      <option value="XM">XM</option>
                      <option value="YP">YP</option>
                      <option value="YM">YM</option>
                    </select>
                  </div>
                )}
                {selectedFuro.tipo === 'vertical' && (
                  <div className="form-field-sm">
                    <label>Lado</label>
                    <select
                      value={selectedFuro.furo.lado || 'LS'}
                      onChange={(e) => handleUpdateFuro('lado', e.target.value)}
                    >
                      <option value="LS">Superior</option>
                      <option value="LI">Inferior</option>
                    </select>
                  </div>
                )}
              </div>

              {/* Replicação */}
              <div className="replicacao-row">
                <input
                  type="number"
                  placeholder="Qtd"
                  min="2"
                  max="20"
                  id="replicar-qtd"
                  className="input-sm"
                />
                <input
                  type="number"
                  placeholder="Dist"
                  step="0.1"
                  id="replicar-dist"
                  className="input-sm"
                />
                <select id="replicar-dir" className="select-sm">
                  <option value="x">X</option>
                  <option value="y">Y</option>
                </select>
                <button
                  className="btn-sm btn-success"
                  onClick={() => {
                    const qtd = parseInt(document.getElementById('replicar-qtd').value);
                    const dist = parseFloat(document.getElementById('replicar-dist').value);
                    const dir = document.getElementById('replicar-dir').value;
                    handleReplicarFuro(qtd, dist, dir);
                  }}
                >
                  🔁
                </button>
              </div>

              <button
                className="btn-sm btn-danger full-width"
                onClick={() => handleDeleteFuro(selectedFuro.tipo, selectedFuro.index)}
              >
                🗑️ Remover
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default EditorMPR;