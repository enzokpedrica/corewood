import React, { useRef, useEffect, useState } from 'react';
import './Canvas.css';

function Canvas({ peca, onAddFuro, selectedTool }) {
  const canvasRef = useRef(null);
  const containerRef = useRef(null);
  const [canvasSize, setCanvasSize] = useState({ width: 800, height: 350 });

  // Calcular escala automática baseado no tamanho da peça e espaço disponível
  const calcularEscala = () => {
    if (!peca.largura || !peca.comprimento) return 1;

    const margemX = 100; // Margem horizontal
    const margemY = 80;  // Margem vertical
    
    const espacoDisponivelX = canvasSize.width - margemX * 2;
    const espacoDisponivelY = canvasSize.height - margemY * 2;
    
    const escalaX = espacoDisponivelX / peca.comprimento;
    const escalaY = espacoDisponivelY / peca.largura;
    
    // Usar a menor escala para caber nos dois eixos
    return Math.min(escalaX, escalaY, 3); // Máximo 3x para não ficar gigante
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

    // Calcular offset para centralizar a peça
    const larguraPecaPx = peca.comprimento * scale;
    const alturaPecaPx = peca.largura * scale;
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
        `${peca.comprimento} mm`,
        offsetX + larguraPecaPx / 2,
        offsetY + alturaPecaPx + 20
      );

      // Largura (Y) - lado esquerdo
      context.save();
      context.translate(offsetX - 20, offsetY + alturaPecaPx / 2);
      context.rotate(-Math.PI / 2);
      context.fillText(`${peca.largura} mm`, 0, 0);
      context.restore();

      // Indicadores de eixo
      context.font = '10px Arial';
      context.fillStyle = '#999';
      context.fillText('X →', offsetX + larguraPecaPx + 15, offsetY + alturaPecaPx);
      context.fillText('Y ↑', offsetX - 10, offsetY - 10);
    };

    const drawFuros = (context) => {
      // Furos verticais
      peca.furos?.forEach((furo) => {
        const x = offsetX + (furo.x * scale);
        const y = offsetY + (furo.y * scale);
        const raio = Math.max(4, furo.diametro * scale / 2);

        context.fillStyle = '#FF6B6B';
        context.beginPath();
        context.arc(x, y, raio, 0, Math.PI * 2);
        context.fill();

        context.strokeStyle = '#c0392b';
        context.lineWidth = 1;
        context.stroke();

        // Label
        context.font = '9px Arial';
        context.fillStyle = '#333';
        context.textAlign = 'center';
        context.fillText(`Ø${furo.diametro}`, x, y - raio - 4);
      });

      // Furos horizontais
      peca.furosHorizontais?.forEach((furo) => {
        const x = offsetX + (furo.x === 'x' ? larguraPecaPx : furo.x * scale);
        const y = offsetY + (furo.y * scale);
        const raio = Math.max(4, furo.diametro * scale / 2);

        context.fillStyle = '#4ECDC4';
        context.beginPath();
        context.arc(x, y, raio, 0, Math.PI * 2);
        context.fill();

        context.strokeStyle = '#16a085';
        context.lineWidth = 1;
        context.stroke();

        // Label
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
      drawFuros(ctx);
    } else {
      ctx.font = '16px Arial';
      ctx.fillStyle = '#999';
      ctx.textAlign = 'center';
      ctx.fillText('Defina as dimensões da peça', canvas.width / 2, canvas.height / 2);
    }
  }, [peca, canvasSize]);

  const handleCanvasClick = (e) => {
    if (!selectedTool || !peca.largura || !peca.comprimento) return;

    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const clickY = e.clientY - rect.top;

    const scale = calcularEscala();
    const larguraPecaPx = peca.comprimento * scale;
    const alturaPecaPx = peca.largura * scale;
    const offsetX = (canvasSize.width - larguraPecaPx) / 2;
    const offsetY = (canvasSize.height - alturaPecaPx) / 2;

    // Verificar se clicou dentro da peça
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