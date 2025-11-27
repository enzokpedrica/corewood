import React, { useRef, useEffect, useState } from 'react';
import './Canvas.css';

function Canvas({ peca, onAddFuro, selectedTool }) {
  const canvasRef = useRef(null);
  const [scale, setScale] = useState(1);
  const [offset] = useState({ x: 200, y: 200 });

  // Constantes
  const PIXELS_PER_MM = 2;

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');

    const drawGrid = (context) => {
      const gridSize = 50;
      context.strokeStyle = '#e0e0e0';
      context.lineWidth = 1;

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
      const larguraPx = peca.comprimento * PIXELS_PER_MM * scale;
      const comprimentoPx = peca.largura * PIXELS_PER_MM * scale;

      context.fillStyle = '#fff';
      context.strokeStyle = '#333';
      context.lineWidth = 3;
      context.fillRect(offset.x, offset.y, larguraPx, comprimentoPx);
      context.strokeRect(offset.x, offset.y, larguraPx, comprimentoPx);

      // Desenhar eixos de referência
      context.strokeStyle = '#999';
      context.lineWidth = 1;
      context.setLineDash([5, 5]);

      // Eixo X (horizontal - embaixo)
      context.beginPath();
      context.moveTo(offset.x, offset.y + comprimentoPx);
      context.lineTo(offset.x + larguraPx, offset.y + comprimentoPx);
      context.stroke();

      // Eixo Y (vertical - esquerda)
      context.beginPath();
      context.moveTo(offset.x, offset.y);
      context.lineTo(offset.x, offset.y + comprimentoPx);
      context.stroke();
      context.setLineDash([]);

      // Labels dos eixos
      context.font = 'bold 16px Arial';
      context.fillStyle = '#666';
      context.fillText('X →', offset.x + larguraPx + 10, offset.y + comprimentoPx);
      context.fillText('↑', offset.x - 20, offset.y - 10);
      context.fillText('Y', offset.x - 20, offset.y + 10);

      context.font = '14px Arial';
      context.fillStyle = '#0066CC';
      context.textAlign = 'center';

      context.fillText(
        `${peca.largura}mm`,
        offset.x + larguraPx / 2,
        offset.y + comprimentoPx + 25
      );

      // context.save();
      // context.translate(offset.x - 15, offset.y + comprimentoPx / 2);
      // context.rotate(-Math.PI / 2);
      // context.fillText(`${peca.comprimento}mm`, 0, 0);
      // context.restore();
    };

    const drawFuros = (context) => {
      
      peca.furos.forEach((furo) => {
        const x = offset.x + (furo.x * PIXELS_PER_MM * scale);
        const y = offset.y + (furo.y * PIXELS_PER_MM * scale);
        const raio = 5;

        context.fillStyle = furo.tipo === 'vertical' ? '#FF6B6B' : '#4ECDC4';
        context.beginPath();
        context.arc(x, y, raio, 0, Math.PI * 2);
        context.fill();

        context.strokeStyle = '#333';
        context.lineWidth = 1;
        context.stroke();

        context.font = '10px Arial';
        context.fillStyle = '#333';
        context.textAlign = 'center';
        context.fillText(`Ø${furo.diametro}`, x, y - 10);
      });
    };

    // Desenhar
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = '#f8f9fa';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    drawGrid(ctx);

    if (peca.largura && peca.comprimento) {
      drawPeca(ctx);
      drawFuros(ctx);
    } else {
      ctx.font = '20px Arial';
      ctx.fillStyle = '#999';
      ctx.textAlign = 'center';
      ctx.fillText('Defina as dimensões da peça →', canvas.width / 2, canvas.height / 2);
    }
  }, [peca, scale, offset, PIXELS_PER_MM]);

    const handleCanvasClick = (e) => {
      if (!selectedTool || !peca.largura) return;

      const canvas = canvasRef.current;
      const rect = canvas.getBoundingClientRect();
      const clickX = e.clientX - rect.left;
      const clickY = e.clientY - rect.top;

      const larguraPx = peca.comprimento * PIXELS_PER_MM * scale;
      const comprimentoPx = peca.largura * PIXELS_PER_MM * scale;

      if (
        clickX >= offset.x &&
        clickX <= offset.x + larguraPx &&
        clickY >= offset.y &&
        clickY <= offset.y + comprimentoPx
      ) {
    
    const furoX = (clickX - offset.x) / (PIXELS_PER_MM * scale);
    const furoY = (clickY - offset.y) / (PIXELS_PER_MM * scale);

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
    <div className="canvas-container">
      <div className="canvas-controls">
        <button onClick={() => setScale(scale + 0.1)}>🔍 +</button>
        <span>{Math.round(scale * 100)}%</span>
        <button onClick={() => setScale(Math.max(0.3, scale - 0.1))}>🔍 -</button>
      </div>

      <canvas
        ref={canvasRef}
        width={1800}  //
        height={700}  //
        onClick={handleCanvasClick}
        style={{ cursor: selectedTool ? 'crosshair' : 'default' }}
      />
    </div>
  );
}

export default Canvas;