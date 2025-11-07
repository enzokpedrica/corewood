import React from 'react';
import './BordasSelector.css';

function BordasSelector({ bordas, onChange }) {
  const handleBordaClick = (lado, tipo) => {
    const novasBordas = { ...bordas };
    
    // Se já tem esse tipo, remove (toggle)
    if (novasBordas[lado] === tipo) {
      novasBordas[lado] = null;
    } else {
      novasBordas[lado] = tipo;
    }
    
    onChange(novasBordas);
  };

  const getBordaClass = (lado) => {
    if (!bordas[lado]) return '';
    return bordas[lado] === 'cor' ? 'borda-cor' : 'borda-pardo';
  };

  return (
    <div className="bordas-selector">
      <h3>🎨 Configuração de Bordas</h3>
      <p className="bordas-hint">Clique nos botões ao redor da peça</p>
      
      <div className="bordas-visual">
        {/* TOPO */}
        <div className="borda-control borda-top">
          <span className="borda-label">TOPO</span>
          <div className="borda-buttons">
            <button
              type="button"
              className={`borda-btn btn-cor ${bordas.top === 'cor' ? 'active' : ''}`}
              onClick={() => handleBordaClick('top', 'cor')}
              title="Borda Cor no Topo"
            >
              🟢 Cor
            </button>
            <button
              type="button"
              className={`borda-btn btn-pardo ${bordas.top === 'pardo' ? 'active' : ''}`}
              onClick={() => handleBordaClick('top', 'pardo')}
              title="Borda Pardo no Topo"
            >
              🟠 Pardo
            </button>
          </div>
        </div>

        {/* MEIO (Peça + Laterais) */}
        <div className="bordas-middle">
          {/* ESQUERDA */}
          <div className="borda-control borda-left">
            <span className="borda-label">ESQ</span>
            <div className="borda-buttons vertical">
              <button
                type="button"
                className={`borda-btn btn-cor ${bordas.left === 'cor' ? 'active' : ''}`}
                onClick={() => handleBordaClick('left', 'cor')}
                title="Borda Cor na Esquerda"
              >
                🟢
              </button>
              <button
                type="button"
                className={`borda-btn btn-pardo ${bordas.left === 'pardo' ? 'active' : ''}`}
                onClick={() => handleBordaClick('left', 'pardo')}
                title="Borda Pardo na Esquerda"
              >
                🟠
              </button>
            </div>
          </div>

          {/* PEÇA CENTRAL */}
          <div className={`peca-central ${getBordaClass('top')} ${getBordaClass('bottom')} ${getBordaClass('left')} ${getBordaClass('right')}`}>
            <div className="peca-info">
              <span className="peca-icon">📦</span>
              <p>PEÇA</p>
            </div>
          </div>

          {/* DIREITA */}
          <div className="borda-control borda-right">
            <span className="borda-label">DIR</span>
            <div className="borda-buttons vertical">
              <button
                type="button"
                className={`borda-btn btn-cor ${bordas.right === 'cor' ? 'active' : ''}`}
                onClick={() => handleBordaClick('right', 'cor')}
                title="Borda Cor na Direita"
              >
                🟢
              </button>
              <button
                type="button"
                className={`borda-btn btn-pardo ${bordas.right === 'pardo' ? 'active' : ''}`}
                onClick={() => handleBordaClick('right', 'pardo')}
                title="Borda Pardo na Direita"
              >
                🟠
              </button>
            </div>
          </div>
        </div>

        {/* BAIXO */}
        <div className="borda-control borda-bottom">
          <span className="borda-label">BAIXO</span>
          <div className="borda-buttons">
            <button
              type="button"
              className={`borda-btn btn-cor ${bordas.bottom === 'cor' ? 'active' : ''}`}
              onClick={() => handleBordaClick('bottom', 'cor')}
              title="Borda Cor Embaixo"
            >
              🟢 Cor
            </button>
            <button
              type="button"
              className={`borda-btn btn-pardo ${bordas.bottom === 'pardo' ? 'active' : ''}`}
              onClick={() => handleBordaClick('bottom', 'pardo')}
              title="Borda Pardo Embaixo"
            >
              🟠 Pardo
            </button>
          </div>
        </div>
      </div>

      {/* Resumo */}
      <div className="bordas-summary">
        {Object.entries(bordas).filter(([_, tipo]) => tipo).length > 0 ? (
          <p>
            <strong>Bordas selecionadas:</strong>{' '}
            {Object.entries(bordas)
              .filter(([_, tipo]) => tipo)
              .map(([lado, tipo]) => `${lado.toUpperCase()}: ${tipo}`)
              .join(', ')}
          </p>
        ) : (
          <p className="no-bordas">Nenhuma borda selecionada</p>
        )}
      </div>
    </div>
  );
}

export default BordasSelector;