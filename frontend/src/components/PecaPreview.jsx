import React from 'react';
import './PecaPreview.css';

function PecaPreview({ pecaData, loading }) {
  if (loading) {
    return (
      <div className="peca-preview loading">
        <div className="spinner"></div>
        <p>Analisando arquivo...</p>
      </div>
    );
  }

  if (!pecaData) {
    return null;
  }

  const { nome, dimensoes, furos_verticais, furos_horizontais } = pecaData;

  return (
    <div className="peca-preview">
      <h3>📋 Preview da Peça</h3>
      
      {/* Nome */}
      <div className="preview-section">
        <label>Nome:</label>
        <strong>{nome}</strong>
      </div>

      {/* Dimensões */}
      <div className="preview-section">
        <label>Dimensões (mm):</label>
        <div className="dimensoes-grid">
          <div className="dimensao-item">
            <span className="dimensao-label">Largura</span>
            <span className="dimensao-value">{dimensoes.largura}</span>
          </div>
          <div className="dimensao-item">
            <span className="dimensao-label">Comprimento</span>
            <span className="dimensao-value">{dimensoes.comprimento}</span>
          </div>
          <div className="dimensao-item">
            <span className="dimensao-label">Espessura</span>
            <span className="dimensao-value">{dimensoes.espessura}</span>
          </div>
        </div>
      </div>

      {/* Furos */}
      <div className="preview-section">
        <label>Furações:</label>
        <div className="furos-info">
          <div className="furo-count">
            <span className="furo-icon">🔴</span>
            <div>
              <strong>{furos_verticais?.length || 0}</strong>
              <span className="furo-type">Verticais</span>
            </div>
          </div>
          <div className="furo-count">
            <span className="furo-icon">🔵</span>
            <div>
              <strong>{furos_horizontais?.length || 0}</strong>
              <span className="furo-type">Horizontais</span>
            </div>
          </div>
        </div>
      </div>

      {/* Visualização simplificada */}
      <div className="preview-section">
        <label>Visualização 2D:</label>
        <div className="peca-visual">
          <svg viewBox="0 0 300 400" className="peca-svg">
            {/* Retângulo da peça */}
            <rect 
              x="50" 
              y="50" 
              width="200" 
              height="300" 
              fill="#f0f0f0" 
              stroke="#333" 
              strokeWidth="2"
            />
            
            {/* Furos verticais (simplificado) */}
            {furos_verticais && furos_verticais.slice(0, 8).map((furo, index) => {
              const x = 50 + (furo.x / dimensoes.largura) * 200;
              const y = 50 + (furo.y / dimensoes.comprimento) * 300;
              return (
                <circle
                  key={`v-${index}`}
                  cx={x}
                  cy={y}
                  r="5"
                  fill="#ff4444"
                  opacity="0.7"
                />
              );
            })}

            {/* Texto de dimensões */}
            <text x="150" y="370" textAnchor="middle" fontSize="12" fill="#666">
              {dimensoes.largura} mm
            </text>
            <text x="30" y="200" textAnchor="middle" fontSize="12" fill="#666" transform="rotate(-90 30 200)">
              {dimensoes.comprimento} mm
            </text>
          </svg>
          
          {furos_verticais && furos_verticais.length > 8 && (
            <p className="preview-note">
              + {furos_verticais.length - 8} furos não mostrados
            </p>
          )}
        </div>
      </div>

      {/* Botão Parse novamente */}
      <button className="btn-secondary" onClick={() => window.location.reload()}>
        🔄 Carregar outro arquivo
      </button>
    </div>
  );
}

export default PecaPreview;