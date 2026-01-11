import React, { useState } from 'react';
import './FuroManual.css';

function FuroManual({ onAddFuro, pecaDimensoes }) {
  const [furoData, setFuroData] = useState({
    tipo: 'vertical',
    x: '',
    y: '',
    z: '',
    diametro: '5',
    profundidade: '0',
    lado: 'XP'
  });

  const [errors, setErrors] = useState({});

  const handleChange = (campo, valor) => {
    setFuroData({
      ...furoData,
      [campo]: valor
    });
    
    // Limpar erro do campo quando usuário editar
    if (errors[campo]) {
      setErrors({
        ...errors,
        [campo]: null
      });
    }
  };

  const validarFuro = () => {
    const novosErros = {};

    // Validar X
    const x = parseFloat(furoData.x);
    if (isNaN(x) || x < 0 || x > pecaDimensoes.comprimento) {
      novosErros.x = `X deve estar entre 0 e ${pecaDimensoes.comprimento}mm`;
    }

    // Validar Y
    const y = parseFloat(furoData.y);
    if (isNaN(y) || y < 0 || y > pecaDimensoes.largura) {
      novosErros.y = `Y deve estar entre 0 e ${pecaDimensoes.largura}mm`;
    }

    // Validar Diâmetro
    const diametro = parseFloat(furoData.diametro);
    if (isNaN(diametro) || diametro <= 0 || diametro > 50) {
      novosErros.diametro = 'Diâmetro deve estar entre 0.1 e 50mm';
    }

    // Validar Profundidade
    const profundidade = parseFloat(furoData.profundidade);
    if (isNaN(profundidade) || profundidade < 0) {
      novosErros.profundidade = 'Profundidade não pode ser negativa';
    }

    setErrors(novosErros);
    return Object.keys(novosErros).length === 0;
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    if (!validarFuro()) {
      return;
    }

    const novoFuro = {
      x: parseFloat(furoData.x),
      y: parseFloat(furoData.y),
      z: furoData.tipo === 'horizontal' ? (parseFloat(furoData.z) || pecaDimensoes.espessura / 2) : null,
      tipo: furoData.tipo,
      diametro: parseFloat(furoData.diametro),
      profundidade: parseFloat(furoData.profundidade),
      lado: furoData.tipo === 'horizontal' ? furoData.lado : null
    };

    onAddFuro(novoFuro);

    // Resetar formulário (mantém tipo e diâmetro)
    setFuroData({
      ...furoData,
      x: '',
      y: '',
      profundidade: furoData.tipo === 'vertical' ? '0' : '11.5'
    });
  };

  return (
    <div className="furo-manual">
      <h3>➕ Adicionar por Coordenadas</h3>
      
      <form onSubmit={handleSubmit} className="furo-manual-form">
      {/* Tipo */}
      <div className="form-group">
        <select
          value={furoData.tipo}
          onChange={(e) => {
            const novoTipo = e.target.value;
            setFuroData({
              ...furoData,
              tipo: novoTipo,
              profundidade: novoTipo === 'vertical' ? '0' : '11.5'
            });
          }}
        >
          <option value="vertical">🔴 Vertical</option>
          <option value="horizontal">🔵 Horizontal</option>
        </select>
      </div>

      {/* X / Y / Z */}
      <div className="form-row-3">
        <div className="form-group">
          <label>X</label>
          <input
            type="number"
            step="0.1"
            value={furoData.x}
            onChange={(e) => handleChange('x', e.target.value)}
            placeholder="0"
          />
        </div>
        <div className="form-group">
          <label>Y</label>
          <input
            type="number"
            step="0.1"
            value={furoData.y}
            onChange={(e) => handleChange('y', e.target.value)}
            placeholder="0"
          />
        </div>
        {furoData.tipo === 'horizontal' && (
          <div className="form-group">
            <label>Z</label>
            <input
              type="number"
              step="0.1"
              value={furoData.z}
              onChange={(e) => handleChange('z', e.target.value)}
              placeholder={String(pecaDimensoes.espessura / 2)}
            />
          </div>
        )}
      </div>

      {/* Diâmetro / Profundidade */}
      <div className="form-row">
        <div className="form-group">
          <label>Ø</label>
          <input
            type="number"
            step="0.1"
            value={furoData.diametro}
            onChange={(e) => handleChange('diametro', e.target.value)}
            placeholder="5"
          />
        </div>
        <div className="form-group">
          <label>Prof.</label>
          <input
            type="number"
            step="0.1"
            value={furoData.profundidade}
            onChange={(e) => handleChange('profundidade', e.target.value)}
            placeholder="0"
          />
        </div>
      </div>

      {/* Lado (se horizontal) */}
      {furoData.tipo === 'horizontal' && (
        <div className="lado-selector">
          <button type="button" className={`lado-btn ${furoData.lado === 'XM' ? 'active' : ''}`} onClick={() => handleChange('lado', 'XM')}>→</button>
          <div className="lado-meio">
            <button type="button" className={`lado-btn ${furoData.lado === 'YM' ? 'active' : ''}`} onClick={() => handleChange('lado', 'YM')}>↓</button>
            <div className="lado-peca">▭</div>
            <button type="button" className={`lado-btn ${furoData.lado === 'YP' ? 'active' : ''}`} onClick={() => handleChange('lado', 'YP')}>↑</button>
          </div>
          <button type="button" className={`lado-btn ${furoData.lado === 'XP' ? 'active' : ''}`} onClick={() => handleChange('lado', 'XP')}>←</button>
        </div>
      )}

      {/* Botão */}
      <button type="submit" className="btn-add-furo">➕ Adicionar</button>
    </form>
    </div>
  );
}

export default FuroManual;