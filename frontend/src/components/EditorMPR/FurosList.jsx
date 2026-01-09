import React from 'react';
import './FurosList.css';

function FurosList({ 
  furosVerticais = [], 
  furosHorizontais = [], 
  selectedFuro, 
  onSelectFuro,
  onDeleteFuro 
}) {
  const totalFuros = furosVerticais.length + furosHorizontais.length;

  const isSelected = (tipo, index) => {
    return selectedFuro?.tipo === tipo && selectedFuro?.index === index;
  };

  const handleSelect = (tipo, index, furo) => {
    onSelectFuro?.({ tipo, index, furo });
  };

  const formatPosition = (x, y) => {
    const xVal = x === 'x' ? 'MAX' : Math.round(x);
    return `(${xVal}, ${Math.round(y)})`;
  };

  return (
    <div className="furos-list">
      {/* Header */}
      <div className="furos-header">
        <h3>
          <span className="header-icon">◉</span>
          Furos
        </h3>
        <span className="furos-count">{totalFuros}</span>
      </div>

      {/* Lista */}
      <div className="furos-scroll">
        {totalFuros === 0 ? (
          <div className="furos-empty">
            <span className="empty-icon">○</span>
            <p>Nenhum furo</p>
            <small>Importe um arquivo MPR ou clique no canvas para adicionar</small>
          </div>
        ) : (
          <>
            {/* Furos Verticais */}
            {furosVerticais.length > 0 && (
              <div className="furos-section">
                <div className="section-header">
                  <span className="section-icon vertical">⬇</span>
                  <span>Verticais</span>
                  <span className="section-count">{furosVerticais.length}</span>
                </div>
                <div className="section-items">
                  {furosVerticais.map((furo, index) => (
                    <div
                      key={`v-${index}`}
                      className={`furo-item ${isSelected('vertical', index) ? 'selected' : ''} ${furo.lado === 'LI' ? 'bottom' : 'top'}`}
                      onClick={() => handleSelect('vertical', index, furo)}
                    >
                      <div className="furo-main">
                        <span className="furo-id">V{index + 1}</span>
                        <span className="furo-diameter">Ø{furo.diametro}</span>
                        <span className="furo-position">{formatPosition(furo.x, furo.y)}</span>
                      </div>
                      <div className="furo-details">
                        <span className="furo-depth">{furo.profundidade || 11}mm</span>
                        <span className={`furo-side ${furo.lado === 'LI' ? 'inferior' : 'superior'}`}>
                          {furo.lado === 'LI' ? 'INF' : 'SUP'}
                        </span>
                      </div>
                      {isSelected('vertical', index) && onDeleteFuro && (
                        <button 
                          className="furo-delete"
                          onClick={(e) => {
                            e.stopPropagation();
                            onDeleteFuro('vertical', index);
                          }}
                          title="Excluir furo"
                        >
                          ×
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Furos Horizontais */}
            {furosHorizontais.length > 0 && (
              <div className="furos-section">
                <div className="section-header">
                  <span className="section-icon horizontal">➡</span>
                  <span>Horizontais</span>
                  <span className="section-count">{furosHorizontais.length}</span>
                </div>
                <div className="section-items">
                  {furosHorizontais.map((furo, index) => (
                    <div
                      key={`h-${index}`}
                      className={`furo-item horizontal ${isSelected('horizontal', index) ? 'selected' : ''}`}
                      onClick={() => handleSelect('horizontal', index, furo)}
                    >
                      <div className="furo-main">
                        <span className="furo-id">H{index + 1}</span>
                        <span className="furo-diameter">Ø{furo.diametro}</span>
                        <span className="furo-position">{formatPosition(furo.x, furo.y)}</span>
                      </div>
                      <div className="furo-details">
                        <span className="furo-depth">{furo.profundidade || 22}mm</span>
                        <span className="furo-side lado">{furo.lado || 'XP'}</span>
                      </div>
                      {isSelected('horizontal', index) && onDeleteFuro && (
                        <button 
                          className="furo-delete"
                          onClick={(e) => {
                            e.stopPropagation();
                            onDeleteFuro('horizontal', index);
                          }}
                          title="Excluir furo"
                        >
                          ×
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </div>

      {/* Legenda */}
      <div className="furos-legend">
        <div className="legend-item">
          <span className="legend-dot vertical-top"></span>
          <span>Superior</span>
        </div>
        <div className="legend-item">
          <span className="legend-dot vertical-bottom"></span>
          <span>Inferior</span>
        </div>
        <div className="legend-item">
          <span className="legend-dot horizontal"></span>
          <span>Horizontal</span>
        </div>
      </div>
    </div>
  );
}

export default FurosList;