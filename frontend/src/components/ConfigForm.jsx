import React from 'react';
import './ConfigForm.css';
import BordasSelector from './BordasSelector';

function ConfigForm({ config, onChange }) {
  const handleChange = (field, value) => {
    onChange({ ...config, [field]: value });
  };

  return (
    <div className="config-form">
      <h3>⚙️ Configurações</h3>
      
      {/* Rotação */}
      <div className="form-group">
        <label>Rotação da Peça</label>
        <div className="radio-group">
          {[0, 90, 180, 270].map(angle => (
            <label key={angle} className="radio-label">
              <input
                type="radio"
                name="angulo"
                value={angle}
                checked={config.angulo_rotacao === angle}
                onChange={(e) => handleChange('angulo_rotacao', parseInt(e.target.value))}
              />
              <span>{angle}°</span>
            </label>
          ))}
        </div>
      </div>

      {/* Espelhamento */}
      <div className="form-group">
        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={config.espelhar_peca}
            onChange={(e) => handleChange('espelhar_peca', e.target.checked)}
          />
          <span>Espelhar Peça Verticalmente</span>
        </label>
      </div>

      {/* Bordas
      <div className="form-group">
        <label>Borda Comprimento (Horizontal)</label>
        <select 
          value={config.posicao_borda_comprimento || ''}
          onChange={(e) => handleChange('posicao_borda_comprimento', e.target.value || null)}
        >
          <option value="">Sem borda</option>
          <option value="top">Em cima</option>
          <option value="bottom">Embaixo</option>
        </select>
      </div>

      <div className="form-group">
        <label>Borda Largura (Vertical)</label>
        <select 
          value={config.posicao_borda_largura || ''}
          onChange={(e) => handleChange('posicao_borda_largura', e.target.value || null)}
        >
          <option value="">Sem borda</option>
          <option value="left">Esquerda</option>
          <option value="right">Direita</option>
        </select>
      </div>*/}

      {/* Bordas - Novo Seletor Visual */}
      <BordasSelector 
        bordas={config.bordas || { top: null, bottom: null, left: null, right: null }}
        onChange={(novasBordas) => handleChange('bordas', novasBordas)}
      />

      {/* Revisão */}
      <div className="form-group">
        <label>Revisão</label>
        <input
          type="text"
          placeholder="Ex: 01"
          value={config.revisao || ''}
          onChange={(e) => handleChange('revisao', e.target.value)}
          maxLength={2}
          required
        />
      </div>

      {/* Alerta */}
      <div className="form-group">
        <label>Alerta (Opcional)</label>
        <input
          type="text"
          placeholder="Ex: Furação dupla conferir medidas"
          value={config.alerta || ''}
          onChange={(e) => handleChange('alerta', e.target.value)}
          maxLength={100}
        />
      </div>
    </div>
  );
}

export default ConfigForm;