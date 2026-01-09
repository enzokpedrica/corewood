import React, { useState } from 'react';
import './FuroManual.css';

function FuroManual({ onAddFuro, pecaDimensoes }) {
  const [furoData, setFuroData] = useState({
    tipo: 'vertical',
    x: '',
    y: '',
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
        {/* Tipo de Furo */}
        <div className="form-group">
          <label>Tipo:</label>
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

        {/* Coordenadas */}
        <div className="form-row">
          <div className="form-group">
            <label>X (mm):</label>
            <input
              type="number"
              step="0.1"
              value={furoData.x}
              onChange={(e) => handleChange('x', e.target.value)}
              placeholder="0"
              className={errors.x ? 'input-error' : ''}
            />
            {errors.x && <span className="error-msg">{errors.x}</span>}
          </div>

          <div className="form-group">
            <label>Y (mm):</label>
            <input
              type="number"
              step="0.1"
              value={furoData.y}
              onChange={(e) => handleChange('y', e.target.value)}
              placeholder="0"
              className={errors.y ? 'input-error' : ''}
            />
            {errors.y && <span className="error-msg">{errors.y}</span>}
          </div>
        </div>

        {/* Diâmetro e Profundidade */}
        <div className="form-row">
          <div className="form-group">
            <label>Ø (mm):</label>
            <input
              type="number"
              step="0.1"
              value={furoData.diametro}
              onChange={(e) => handleChange('diametro', e.target.value)}
              placeholder="5"
              className={errors.diametro ? 'input-error' : ''}
            />
            {errors.diametro && <span className="error-msg">{errors.diametro}</span>}
          </div>

          <div className="form-group">
            <label>Prof. (mm):</label>
            <input
              type="number"
              step="0.1"
              value={furoData.profundidade}
              onChange={(e) => handleChange('profundidade', e.target.value)}
              placeholder="0"
              className={errors.profundidade ? 'input-error' : ''}
            />
            {errors.profundidade && <span className="error-msg">{errors.profundidade}</span>}
            <small>0 = passante</small>
          </div>
        </div>

        {/* Lado (se horizontal) */}
        {furoData.tipo === 'horizontal' && (
          <div className="form-group">
            <label>Lado:</label>
            <select
              value={furoData.lado}
              onChange={(e) => handleChange('lado', e.target.value)}
            >
              <option value="XP">XP (Frente)</option>
              <option value="XM">XM (Trás)</option>
              <option value="YP">YP (Direita)</option>
              <option value="YM">YM (Esquerda)</option>
            </select>
          </div>
        )}

        {/* Botão Submit */}
        <button type="submit" className="btn-add-furo">
          ➕ Adicionar Furo
        </button>
      </form>
    </div>
  );
}

export default FuroManual;