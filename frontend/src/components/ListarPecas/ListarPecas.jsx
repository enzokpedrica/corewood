import React, { useState } from 'react';
import './ListarPecas.css';
import api from '../../services/api';

function ListarPecas({ onSelecionarPeca }) {
  const [codigoProduto, setCodigoProduto] = useState('');
  const [pecas, setPecas] = useState([]);
  const [loading, setLoading] = useState(false);
  const [erro, setErro] = useState(null);
  
  // Estados do modal STEP
  const [showModalStep, setShowModalStep] = useState(false);
  const [stepFile, setStepFile] = useState(null);
  const [stepPecas, setStepPecas] = useState([]);
  const [atribuicoes, setAtribuicoes] = useState({});
  const [loadingStep, setLoadingStep] = useState(false);
  const [erroStep, setErroStep] = useState(null);

  const buscarPecas = async () => {
    if (!codigoProduto) {
      setErro('Digite o código do produto');
      return;
    }

    setLoading(true);
    setErro(null);

    try {
      const response = await api.get(`/pecas/produto/${codigoProduto}`);
      const data = response.data;
      setPecas(data);
      
      if (data.length === 0) {
        setErro('Nenhuma peça encontrada para este produto');
      }
    } catch (error) {
      if (error.response?.status === 404) {
        setErro('Produto não encontrado');
      } else {
        setErro(error.response?.data?.detail || 'Erro ao buscar peças');
      }
      setPecas([]);
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      buscarPecas();
    }
  };

  // ===== FUNÇÕES DO MODAL STEP =====
  
  const handleStepFileChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    setStepFile(file);
    setLoadingStep(true);
    setErroStep(null);
    setStepPecas([]);
    setAtribuicoes({});
    
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await api.post('/parse-step', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      const { pecas: pecasStep } = response.data;
      setStepPecas(pecasStep);
      
      // Inicializar atribuições vazias
      const atribInit = {};
      pecasStep.forEach((p, idx) => {
        atribInit[idx] = '';
      });
      setAtribuicoes(atribInit);
      
    } catch (error) {
      setErroStep(error.response?.data?.detail || 'Erro ao processar arquivo STEP');
      console.error(error);
    } finally {
      setLoadingStep(false);
    }
  };
  
  const handleAtribuicaoChange = (stepIdx, pecaId) => {
    setAtribuicoes(prev => ({
      ...prev,
      [stepIdx]: pecaId
    }));
  };
  
  const handleSalvarAtribuicoes = async () => {
    // Verificar se todas as peças foram atribuídas
    const naoAtribuidas = Object.values(atribuicoes).filter(v => !v).length;
    if (naoAtribuidas > 0) {
      if (!window.confirm(`${naoAtribuidas} peça(s) não foram atribuídas. Deseja continuar mesmo assim?`)) {
        return;
      }
    }
    
    setLoadingStep(true);
    setErroStep(null);
    
    try {
      let salvos = 0;
      
      for (const [stepIdx, pecaId] of Object.entries(atribuicoes)) {
        if (!pecaId) continue;
        
        const stepPeca = stepPecas[parseInt(stepIdx)];
        
        // Debug: ver o que está vindo
        console.log('stepPeca:', stepPeca);
        
        // Pegar dimensões (podem estar em diferentes formatos)
        const largura = stepPeca.largura || stepPeca.dimensoes?.largura || 0;
        const comprimento = stepPeca.comprimento || stepPeca.dimensoes?.comprimento || 0;
        const espessura = stepPeca.espessura || stepPeca.dimensoes?.espessura || 15;
        
        console.log('Dimensões:', { largura, comprimento, espessura });
        
        // Preparar furos no formato esperado
        const furosArray = stepPeca.furos || [];
        const furosFormatados = {
          verticais: furosArray.filter(f => f.tipo === 'vertical').map(f => ({
            x: f.x,
            y: f.y,
            diametro: f.diametro,
            profundidade: f.profundidade || 0,
            lado: f.lado || 'LS'
          })),
          horizontais: furosArray.filter(f => f.tipo === 'horizontal').map(f => ({
            x: f.x,
            y: f.y,
            z: f.z,
            diametro: f.diametro,
            profundidade: f.profundidade || 22,
            lado: f.lado || 'XP'
          }))
        };
        
        // Criar FormData corretamente
        const formData = new FormData();
        formData.append('largura', String(largura));
        formData.append('comprimento', String(comprimento));
        formData.append('espessura', String(espessura));
        formData.append('furos', JSON.stringify(furosFormatados));
        
        await api.put(`/pecas/${pecaId}/salvar`, formData);
        
        salvos++;
      }
      
      alert(`✅ ${salvos} peça(s) atualizada(s) com sucesso!`);
      setShowModalStep(false);
      setStepFile(null);
      setStepPecas([]);
      setAtribuicoes({});
      
      // Recarregar lista de peças
      buscarPecas();
      
    } catch (error) {
      const errorMsg = error.response?.data?.detail;
      if (typeof errorMsg === 'object') {
        setErroStep(JSON.stringify(errorMsg));
      } else {
        setErroStep(errorMsg || 'Erro ao salvar atribuições');
      }
      console.error(error);
    } finally {
      setLoadingStep(false);
    }
  };
  
  const handleBaixarMPRs = async () => {
    if (stepPecas.length === 0) return;
    
    setLoadingStep(true);
    
    try {
      const formData = new FormData();
      formData.append('file', stepFile);
      
      const response = await api.post('/step-to-mpr', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        responseType: 'blob'
      });
      
      // Download do arquivo
      const url = window.URL.createObjectURL(response.data);
      const link = document.createElement('a');
      link.href = url;
      
      // Se for ZIP ou MPR
      const contentType = response.headers['content-type'];
      if (contentType?.includes('zip')) {
        link.download = 'pecas_mpr.zip';
      } else {
        link.download = `${stepPecas[0]?.nome || 'peca'}.mpr`;
      }
      
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
    } catch (error) {
      alert('❌ Erro ao baixar MPRs: ' + (error.response?.data?.detail || error.message));
      console.error(error);
    } finally {
      setLoadingStep(false);
    }
  };
  
  const fecharModal = () => {
    setShowModalStep(false);
    setStepFile(null);
    setStepPecas([]);
    setAtribuicoes({});
    setErroStep(null);
  };

  return (
    <div className="listar-pecas">
      <div className="listar-container">
        <h2>🗂️ Buscar Peças</h2>
        <p className="subtitulo">Busque as peças por código do produto</p>

        <div className="busca-container">
          <input
            type="text"
            value={codigoProduto}
            onChange={(e) => setCodigoProduto(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Digite o código do produto (ex: 8100015098)"
            className="input-busca"
          />
          <button 
            onClick={buscarPecas} 
            className="btn-buscar"
            disabled={loading}
          >
            {loading ? '⏳' : '🔍'} Buscar
          </button>
        </div>

        {erro && (
          <div className="alerta erro">
            ❌ {erro}
          </div>
        )}

        {pecas.length > 0 && (
          <div className="pecas-lista">
            <div className="pecas-header">
              <h3>📦 {pecas.length} peça(s) encontrada(s)</h3>
              <button 
                className="btn-importar-step"
                onClick={() => setShowModalStep(true)}
              >
                📎 Importar STEP
              </button>
            </div>

            {pecas.map((peca) => (
              <div key={peca.id} className="peca-card">
                <div className="peca-info">
                  <div className="peca-codigo">{peca.codigo}</div>
                  <div className="peca-nome">{peca.nome}</div>
                  <div className="peca-dimensoes">
                    📐 {peca.comprimento} × {peca.largura} × {peca.espessura}mm
                  </div>
                  {peca.familia && (
                    <div className="peca-familia">
                      🏷️ {peca.familia}
                    </div>
                  )}
                </div>

                <div className="peca-acoes">
                  <button
                    className="btn-editar"
                    onClick={() => onSelecionarPeca(peca)}
                  >
                    ✏️ Editar no MPR
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* ===== MODAL IMPORTAR STEP ===== */}
      {showModalStep && (
        <div className="modal-overlay" onClick={fecharModal}>
          <div className="modal-step" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>📎 Importar STEP → MPR</h2>
              <button className="btn-fechar" onClick={fecharModal}>✕</button>
            </div>
            
            <div className="modal-body">
              {/* Upload */}
              <div className="step-upload">
                <label className="upload-area">
                  <input
                    type="file"
                    accept=".step,.stp,.STEP,.STP"
                    onChange={handleStepFileChange}
                    disabled={loadingStep}
                  />
                  {stepFile ? (
                    <div className="file-info">
                      <span className="file-icon">📐</span>
                      <span className="file-name">{stepFile.name}</span>
                      <span className="file-size">({(stepFile.size / 1024).toFixed(1)} KB)</span>
                    </div>
                  ) : (
                    <div className="upload-placeholder">
                      <span className="upload-icon">📁</span>
                      <span>Clique ou arraste um arquivo .STEP</span>
                    </div>
                  )}
                </label>
              </div>
              
              {loadingStep && (
                <div className="loading-step">
                  ⏳ Processando arquivo STEP...
                </div>
              )}
              
              {erroStep && (
                <div className="alerta erro">
                  ❌ {erroStep}
                </div>
              )}
              
              {/* Lista de peças do STEP */}
              {stepPecas.length > 0 && (
                <div className="step-pecas-lista">
                  <h3>🔩 {stepPecas.length} peça(s) encontrada(s) no STEP</h3>
                  
                  <table className="tabela-atribuicao">
                    <thead>
                      <tr>
                        <th>Peça no STEP</th>
                        <th>Dimensões</th>
                        <th>Furos</th>
                        <th>Atribuir a</th>
                      </tr>
                    </thead>
                    <tbody>
                      {stepPecas.map((stepPeca, idx) => (
                        <tr key={idx}>
                          <td className="step-peca-nome">{stepPeca.nome}</td>
                          <td className="step-peca-dims">
                            {stepPeca.comprimento} × {stepPeca.largura} × {stepPeca.espessura}mm
                          </td>
                          <td className="step-peca-furos">
                            {stepPeca.furos?.length || 0}
                          </td>
                          <td>
                            <select
                              value={atribuicoes[idx] || ''}
                              onChange={(e) => handleAtribuicaoChange(idx, e.target.value)}
                              className="select-atribuicao"
                            >
                              <option value="">-- Selecionar --</option>
                              {pecas.map((peca) => (
                                <option key={peca.id} value={peca.id}>
                                  {peca.codigo} - {peca.nome}
                                </option>
                              ))}
                            </select>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
            
            {/* Footer com ações */}
            {stepPecas.length > 0 && (
              <div className="modal-footer">
                <button 
                  className="btn-secundario"
                  onClick={handleBaixarMPRs}
                  disabled={loadingStep}
                >
                  📥 Baixar MPRs
                </button>
                <button 
                  className="btn-primario"
                  onClick={handleSalvarAtribuicoes}
                  disabled={loadingStep}
                >
                  💾 Atribuir e Salvar
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default ListarPecas;