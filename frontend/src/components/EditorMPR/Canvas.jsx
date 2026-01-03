import React, { useRef, useEffect, useState } from 'react';
import './Canvas.css';

function Canvas({ peca, onAddFuro, selectedTool, bordas, transformacao }) {
  const canvasRef = useRef(null);
  const containerRef = useRef(null);
  const [canvasSize, setCanvasSize] = useState({ width: 800, height: 350 });

  // Calcular dimensões considerando rotação
  const getDimensoesRotacionadas = () => {
    const rotacao = transformacao?.rotacao || 0;
    
    if (rotacao === 90 || rotacao === 270) {
      // Rotação 90° ou 270° - inverte largura e comprimento
      return {
        largura: peca.comprimento,
        comprimento: peca.largura
      };
    }
    return {
      largura: peca.largura,
      comprimento: peca.comprimento
    };
  };

  // Calcular escala automática baseado no tamanho da peça e espaço disponível
  const calcularEscala = () => {
    const dims = getDimensoesRotacionadas();
    if (!dims.largura || !dims.comprimento) return 1;

    const margemX = 100;
    const margemY = 80;
    
    const espacoDisponivelX = canvasSize.width - margemX * 2;
    const espacoDisponivelY = canvasSize.height - margemY * 2;
    
    const escalaX = espacoDisponivelX / dims.comprimento;
    const escalaY = espacoDisponivelY / dims.largura;
    
    return Math.min(escalaX, escalaY, 3);
  };

  // Transformar bordas baseado na rotação e espelhamento
  const transformarBordas = () => {
    if (!bordas) return null;
    
    const rotacao = transformacao?.rotacao || 0;
    const espelhado = transformacao?.espelhado || false;
    
    let { topo, baixo, esquerda, direita } = bordas;
    
    // Aplicar espelhamento primeiro (inverte topo <-> baixo)
    if (espelhado) {
      [topo, baixo] = [baixo, topo];
    }
    
    // Aplicar rotação
    if (rotacao === 90) {
      return { topo: esquerda, direita: topo, baixo: direita, esquerda: baixo };
    } else if (rotacao === 180) {
      return { topo: baixo, baixo: topo, esquerda: direita, direita: esquerda };
    } else if (rotacao === 270) {
      return { topo: direita, esquerda: topo, baixo: esquerda, direita: baixo };
    }
    
    return { topo, baixo, esquerda, direita };
  };

  // Transformar coordenadas de furo baseado na rotação e espelhamento
  const transformarCoordenadas = (x, y) => {
    const rotacao = transformacao?.rotacao || 0;
    const espelhado = transformacao?.espelhado || false;
    
    let novoX = x;
    let novoY = y;
    
    // Aplicar espelhamento primeiro
    if (espelhado) {
      novoY = peca.largura - y;
    }
    
    // Aplicar rotação
    if (rotacao === 90) {
      const tempX = novoX;
      novoX = peca.largura - novoY;
      novoY = tempX;
      if (espelhado) {
        novoX = peca.largura - novoX;
      }
    } else if (rotacao === 180) {
      novoX = peca.comprimento - novoX;
      novoY = peca.largura - novoY;
      if (espelhado) {
        novoY = peca.largura - novoY;
      }
    } else if (rotacao === 270) {
      const tempX = novoX;
      novoX = novoY;
      novoY = peca.comprimento - tempX;
      if (espelhado) {
        novoX = peca.largura - novoX;
      }
    }
    
    return { x: novoX, y: novoY };
  };

  // Observar tamanho do container
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const resizeObserver = new ResizeObserver((entries) => {
      for (let entry of entries) {
        const { width, height } = entry.contentRect;
        setCanvasSize({ 
          width: Math.max(width, 400), 
          height: Math.max(height, 250) 
        });
      }
    });

    resizeObserver.observe(container);
    return () => resizeObserver.disconnect();
  }, []);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const scale = calcularEscala();
    const dims = getDimensoesRotacionadas();

    // Calcular offset para centralizar a peça
    const larguraPecaPx = dims.comprimento * scale;
    const alturaPecaPx = dims.largura * scale;
    const offsetX = (canvasSize.width - larguraPecaPx) / 2;
    const offsetY = (canvasSize.height - alturaPecaPx) / 2;

    const drawGrid = (context) => {
      const gridSize = 50;
      context.strokeStyle = '#f0f0f0';
      context.lineWidth = 0.5;

      for (let x = 0; x < context.canvas.width; x += gridSize) {
        context.beginPath();
        context.moveTo(x, 0);
        context.lineTo(x, context.canvas.height);
        context.stroke();
      }

      for (let y = 0; y < context.canvas.height; y += gridSize) {
        context.beginPath();
        context.moveTo(0, y);
        context.lineTo(context.canvas.width, y);
        context.stroke();
      }
    };

    const drawPeca = (context) => {
      // Desenhar peça
      context.fillStyle = '#fff';
      context.strokeStyle = '#333';
      context.lineWidth = 2;
      context.fillRect(offsetX, offsetY, larguraPecaPx, alturaPecaPx);
      context.strokeRect(offsetX, offsetY, larguraPecaPx, alturaPecaPx);

      // Labels de dimensão
      context.font = '12px Arial';
      context.fillStyle = '#666';
      context.textAlign = 'center';

      // Comprimento (X) - embaixo
      context.fillText(
        `${dims.comprimento} mm`,
        offsetX + larguraPecaPx / 2,
        offsetY + alturaPecaPx + 20
      );

      // Largura (Y) - lado esquerdo
      context.save();
      context.translate(offsetX - 20, offsetY + alturaPecaPx / 2);
      context.rotate(-Math.PI / 2);
      context.fillText(`${dims.largura} mm`, 0, 0);
      context.restore();

      // Indicadores de eixo
      context.font = '10px Arial';
      context.fillStyle = '#999';
      context.fillText('X →', offsetX + larguraPecaPx + 15, offsetY + alturaPecaPx);
      context.fillText('Y ↑', offsetX - 10, offsetY - 10);
      
      // Indicador de transformação
      const rotacao = transformacao?.rotacao || 0;
      const espelhado = transformacao?.espelhado || false;
      if (rotacao !== 0 || espelhado) {
        context.font = '10px Arial';
        context.fillStyle = '#667eea';
        let textoTransf = [];
        if (rotacao !== 0) textoTransf.push(`↻${rotacao}°`);
        if (espelhado) textoTransf.push('⇄');
        context.fillText(textoTransf.join(' '), offsetX + larguraPecaPx - 30, offsetY - 10);
      }
    };

    const drawBordas = (context) => {
      const bordasTransformadas = transformarBordas();
      if (!bordasTransformadas) return;
      
      const espessuraBorda = 3;
      
      const cores = {
        cor: '#32CD32',
        pardo: '#FF8C00',
        nenhum: null
      };
      
      // Topo
      if (bordasTransformadas.topo && bordasTransformadas.topo !== 'nenhum') {
        context.fillStyle = cores[bordasTransformadas.topo];
        context.fillRect(offsetX, offsetY - espessuraBorda, larguraPecaPx, espessuraBorda);
      }
      
      // Baixo
      if (bordasTransformadas.baixo && bordasTransformadas.baixo !== 'nenhum') {
        context.fillStyle = cores[bordasTransformadas.baixo];
        context.fillRect(offsetX, offsetY + alturaPecaPx, larguraPecaPx, espessuraBorda);
      }
      
      // Esquerda
      if (bordasTransformadas.esquerda && bordasTransformadas.esquerda !== 'nenhum') {
        context.fillStyle = cores[bordasTransformadas.esquerda];
        context.fillRect(offsetX - espessuraBorda, offsetY, espessuraBorda, alturaPecaPx);
      }
      
      // Direita
      if (bordasTransformadas.direita && bordasTransformadas.direita !== 'nenhum') {
        context.fillStyle = cores[bordasTransformadas.direita];
        context.fillRect(offsetX + larguraPecaPx, offsetY, espessuraBorda, alturaPecaPx);
      }
    };

    const drawFuros = (context) => {
      const rotacao = transformacao?.rotacao || 0;
      
      // Furos verticais
      peca.furos?.forEach((furo) => {
        const coordsTransformadas = transformarCoordenadas(furo.x, furo.y);
        
        // Ajustar escala baseado na rotação
        let x, y;
        if (rotacao === 90 || rotacao === 270) {
          x = offsetX + (coordsTransformadas.x * scale);
          y = offsetY + (coordsTransformadas.y * scale);
        } else {
          x = offsetX + (coordsTransformadas.x * scale);
          y = offsetY + (coordsTransformadas.y * scale);
        }
        
        const raio = Math.max(4, furo.diametro * scale / 2);
        
        const isLadoInferior = furo.lado === 'LI';
        
        if (isLadoInferior) {
          context.fillStyle = '#333333';
          context.beginPath();
          context.arc(x, y, raio, 0, Math.PI * 2);
          context.fill();
          
          context.strokeStyle = '#000000';
          context.lineWidth = 2;
          context.stroke();
        } else {
          context.fillStyle = '#FF6B6B';
          context.beginPath();
          context.arc(x, y, raio, 0, Math.PI * 2);
          context.fill();
          
          context.strokeStyle = '#c0392b';
          context.lineWidth = 1;
          context.stroke();
        }

        context.font = '9px Arial';
        context.fillStyle = '#333';
        context.textAlign = 'center';
        context.fillText(`Ø${furo.diametro}`, x, y - raio - 4);
      });

      // Furos horizontais
      peca.furosHorizontais?.forEach((furo) => {
        const furoX = furo.x === 'x' ? peca.comprimento : furo.x;
        const coordsTransformadas = transformarCoordenadas(furoX, furo.y);
        
        let x, y;
        if (rotacao === 90 || rotacao === 270) {
          x = offsetX + (coordsTransformadas.x * scale);
          y = offsetY + (coordsTransformadas.y * scale);
        } else {
          x = offsetX + (coordsTransformadas.x * scale);
          y = offsetY + (coordsTransformadas.y * scale);
        }
        
        const raio = Math.max(4, furo.diametro * scale / 2);

        context.fillStyle = '#1900ffff';
        context.beginPath();
        context.arc(x, y, raio, 0, Math.PI * 2);
        context.fill();

        context.strokeStyle = '#1900ffff';
        context.lineWidth = 1;
        context.stroke();

        context.font = '9px Arial';
        context.fillStyle = '#333';
        context.textAlign = 'center';
        context.fillText(`Ø${furo.diametro}`, x, y - raio - 4);
      });
    };

    // Limpar e desenhar
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = '#fafafa';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    drawGrid(ctx);

    if (peca.largura && peca.comprimento) {
      drawPeca(ctx);
      drawBordas(ctx);
      drawFuros(ctx);
    } else {
      ctx.font = '16px Arial';
      ctx.fillStyle = '#999';
      ctx.textAlign = 'center';
      ctx.fillText('Defina as dimensões da peça', canvas.width / 2, canvas.height / 2);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [peca, canvasSize, bordas, transformacao]);

  const handleCanvasClick = (e) => {
    if (!selectedTool || !peca.largura || !peca.comprimento) return;

    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const clickY = e.clientY - rect.top;

    const scale = calcularEscala();
    const dims = getDimensoesRotacionadas();
    const larguraPecaPx = dims.comprimento * scale;
    const alturaPecaPx = dims.largura * scale;
    const offsetX = (canvasSize.width - larguraPecaPx) / 2;
    const offsetY = (canvasSize.height - alturaPecaPx) / 2;

    if (
      clickX >= offsetX &&
      clickX <= offsetX + larguraPecaPx &&
      clickY >= offsetY &&
      clickY <= offsetY + alturaPecaPx
    ) {
      const furoX = (clickX - offsetX) / scale;
      const furoY = (clickY - offsetY) / scale;

      onAddFuro({
        x: Math.round(furoX * 10) / 10,
        y: Math.round(furoY * 10) / 10,
        tipo: selectedTool,
        diametro: 5,
        profundidade: selectedTool === 'vertical' ? 0 : 11.5,
        lado: selectedTool === 'horizontal' ? 'XP' : null
      });
    }
  };

  return (
    <div className="canvas-container" ref={containerRef}>
      <canvas
        ref={canvasRef}
        width={canvasSize.width}
        height={canvasSize.height}
        onClick={handleCanvasClick}
        style={{ cursor: selectedTool ? 'crosshair' : 'default' }}
      />
    </div>
  );
}

export default Canvas;