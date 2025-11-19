import React, { useState } from 'react';
import './ListarPecas.css';

function ListarPecas({ onSelecionarPeca }) {
  const [codigoProduto, setCodigoProduto] = useState('');
  const [pecas, setPecas] = useState([]);
  const [loading, setLoading] = useState(false);
  const [erro, setErro] = useState(null);

  const buscarPecas = async () => {
    if (!codigoProduto) {
      setErro('Digite o código do produto');
      return;
    }

    setLoading(true);
    setErro(null);

    try {
      const response = await fetch(
        `${process.env.REACT_APP_API_URL}/pecas/produto/${codigoProduto}`
      );

      if (response.ok) {
        const data = await response.json();
        setPecas(data);
        
        if (data.length === 0) {
          setErro('Nenhuma peça encontrada para este produto');
        }
      } else {
        setErro('Produto não encontrado');
        setPecas([]);
      }
    } catch (error) {
      setErro('Erro ao buscar peças');
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
    </div>
  );
}

export default ListarPecas;