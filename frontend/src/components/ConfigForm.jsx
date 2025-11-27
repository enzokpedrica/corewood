import React from 'react';
import './ConfigForm.css';
import BordasSelector from './BordasSelector';

function ConfigForm({ config, onChange, pecaParseada }) {
  const handleChange = (field, value) => {
    onChange({ ...config, [field]: value });
  };

  const handleOffsetChange = (furoIndex, tipo, value) => {
    const offsets = { ...(config.offsets_cotas || {}) };
    if (!offsets[furoIndex]) {
      offsets[furoIndex] = { x: 25, y: 25 };
    }
    offsets[furoIndex][tipo] = parseInt(value) || 25;
    onChange({ ...config, offsets_cotas: offsets });
  };

    return (
      <div className="config-form">
        <h3>⚙️ Configurações</h3>
        
        {/* ... seus campos existentes (Rotação, Espelhamento, Bordas, etc.) ... */}
        
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

        {/* Bordas */}
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

        {/* Status */}
        <div className="form-group">
          <label>Status</label>
          <select
            value={config.status || 'CÓPIA CONTROLADA'}
            onChange={(e) => handleChange('status', e.target.value)}
          >
            <option value="CÓPIA CONTROLADA">CÓPIA CONTROLADA</option>
            <option value="EM REVISÃO">EM REVISÃO</option>
            <option value="CÓPIA ÚNICA">CÓPIA ÚNICA</option>
          </select>
        </div>

        {/* ===== AJUSTE DE COTAS (MVP) ===== */}
        {pecaParseada && pecaParseada.furos_verticais && pecaParseada.furos_verticais.length > 0 && (
          <div className="form-group">
            <h4>📏 Ajuste de Cotas</h4>
            <p style={{ fontSize: '0.85rem', color: '#666', marginBottom: '0.5rem' }}>
              Ajuste a distância das cotas para evitar sobreposição
            </p>
            
            <div style={{ maxHeight: '200px', overflowY: 'auto' }}>
              {pecaParseada.furos_verticais.map((furo, index) => (
                <div key={index} style={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: '0.5rem',
                  padding: '0.5rem',
                  background: index % 2 === 0 ? '#f5f5f5' : 'white',
                  borderRadius: '4px',
                  marginBottom: '0.25rem'
                }}>
                  <span style={{ fontSize: '0.8rem', minWidth: '120px' }}>
                    Furo {index + 1} ({furo.x}, {furo.y})
                  </span>
                  <label style={{ fontSize: '0.75rem' }}>X:</label>
                  <input
                    type="number"
                    min="15"
                    max="80"
                    value={config.offsets_cotas?.[index]?.x || 25}
                    onChange={(e) => handleOffsetChange(index, 'x', e.target.value)}
                    style={{ width: '50px', padding: '0.25rem' }}
                  />
                  <label style={{ fontSize: '0.75rem' }}>Y:</label>
                  <input
                    type="number"
                    min="15"
                    max="80"
                    value={config.offsets_cotas?.[index]?.y || 25}
                    onChange={(e) => handleOffsetChange(index, 'y', e.target.value)}
                    style={{ width: '50px', padding: '0.25rem' }}
                  />
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
}

export default ConfigForm;