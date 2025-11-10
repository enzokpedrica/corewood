import React from 'react';
import BordasSelector from './BordasSelector';
import './PecaCard.css';

function PecaCard({ peca, onUpdate, onRemove }) {
  const handleChange = (campo, valor) => {
    onUpdate(peca.id, { ...peca.config, [campo]: valor });
  };

  return (
    <div className="peca-card">
      <div className="peca-card-header">
        <div className="peca-info">
          <span className="peca-icon">📄</span>
          <div>
            <h4>{peca.nome}</h4>
            <span className="peca-size">{(peca.file.size / 1024).toFixed(1)} KB</span>
          </div>
        </div>
        <button 
          className="btn-remove"
          onClick={() => onRemove(peca.id)}
          title="Remover arquivo"
        >
          ✕
        </button>
      </div>

      <div className="peca-card-body">
        {/* Rotação e Espelhamento */}
        <div className="config-row">
          <div className="form-group-inline">
            <label>Rotação:</label>
            <select
              value={peca.config.angulo_rotacao}
              onChange={(e) => handleChange('angulo_rotacao', parseInt(e.target.value))}
            >
              <option value={0}>0° (Original)</option>
              <option value={90}>90° (Horário)</option>
              <option value={180}>180° (Inverter)</option>
              <option value={270}>270° (Anti-horário)</option>
            </select>
          </div>

          <div className="form-group-inline">
            <label>
              <input
                type="checkbox"
                checked={peca.config.espelhar_peca}
                onChange={(e) => handleChange('espelhar_peca', e.target.checked)}
              />
              Espelhar peça
            </label>
          </div>
        </div>

        {/* Bordas - versão compacta */}
        <div className="bordas-compacta">
          <h5>Bordas:</h5>
          <BordasSelector
            bordas={peca.config.bordas}
            onChange={(novasBordas) => handleChange('bordas', novasBordas)}
          />
        </div>

        {/* Revisão */}
        <div className="form-group-inline">
          <label>Revisão: <span className="required">*</span></label>
          <input
            type="text"
            value={peca.config.revisao || ''}
            onChange={(e) => handleChange('revisao', e.target.value)}
            placeholder="Ex: 01"
            maxLength={10}
            required
          />
        </div>

        {/* Alerta */}
        <div className="form-group-inline">
          <label>Alerta:</label>
          <input
            type="text"
            value={peca.config.alerta || ''}
            onChange={(e) => handleChange('alerta', e.target.value)}
            placeholder="Texto de atenção (opcional)"
            maxLength={100}
          />
        </div>
      </div>
    </div>
  );
}

export default PecaCard;