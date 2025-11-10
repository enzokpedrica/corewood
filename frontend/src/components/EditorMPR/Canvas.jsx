import React, { useRef, useEffect, useState } from 'react';
import './Canvas.css';

function Canvas({ peca, onAddFuro, selectedTool }) {
  const canvasRef = useRef(null);
  const [scale, setScale] = useState(1);
  const [offset, setOffset] = useState({ x: 50, y: 50 });

  // Constantes
  const PIXELS_PER_MM = 2; // 2 pixels = 1mm (escala visual)

  useEffect(() => {
    drawCanvas();
  }, [peca, scale, offset]);

  const drawCanvas = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Fundo
    ctx.fillStyle = '#f8f9fa';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Grid
    drawGrid(ctx);

    // Peça (se definida)
    if (peca.largura && peca.comprimento) {
      drawPeca(ctx);
      drawFuros(ctx);
    } else {
      // Mensagem inicial
      ctx.font = '20px Arial';
      ctx.fillStyle = '#999';
      ctx.textAlign = 'center';
      ctx.fillText('Defina as dimensões da peça →', canvas.width / 2, canvas.height / 2);
    }
  };

  const drawGrid = (ctx) => {
    const gridSize = 50; // Grid a cada 50px
    ctx.strokeStyle = '#e0e0e0';
    ctx.lineWidth = 1;

    // Linhas verticais
    for (let x = 0; x < ctx.canvas.width; x += gridSize) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, ctx.canvas.height);
      ctx.stroke();
    }

    // Linhas horizontais
    for (let y = 0; y < ctx.canvas.height; y += gridSize) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(ctx.canvas.width, y);
      ctx.stroke();
    }
  };

  const drawPeca = (ctx) => {
    const larguraPx = peca.largura * PIXELS_PER_MM * scale;
    const comprimentoPx = peca.comprimento * PIXELS_PER_MM * scale;

    // Retângulo da peça
    ctx.fillStyle = '#fff';
    ctx.strokeStyle = '#333';
    ctx.lineWidth = 3;
    ctx.fillRect(offset.x, offset.y, larguraPx, comprimentoPx);
    ctx.strokeRect(offset.x, offset.y, larguraPx, comprimentoPx);

    // Dimensões (labels)
    ctx.font = '14px Arial';
    ctx.fillStyle = '#0066CC';
    ctx.textAlign = 'center';

    // Largura (embaixo)
    ctx.fillText(
      `${peca.largura}mm`,
      offset.x + larguraPx / 2,
      offset.y + comprimentoPx + 25
    );

    // Comprimento (lado)
    ctx.save();
    ctx.translate(offset.x - 15, offset.y + comprimentoPx / 2);
    ctx.rotate(-Math.PI / 2);
    ctx.fillText(`${peca.comprimento}mm`, 0, 0);
    ctx.restore();
  };

  const drawFuros = (ctx) => {
    peca.furos.forEach((furo, index) => {
      const x = offset.x + (furo.x * PIXELS_PER_MM * scale);
      const y = offset.y + (furo.y * PIXELS_PER_MM * scale);
      const raio = 5;

      // Círculo do furo
      ctx.fillStyle = furo.tipo === 'vertical' ? '#FF6B6B' : '#4ECDC4';
      ctx.beginPath();
      ctx.arc(x, y, raio, 0, Math.PI * 2);
      ctx.fill();

      // Borda
      ctx.strokeStyle = '#333';
      ctx.lineWidth = 1;
      ctx.stroke();

      // Label
      ctx.font = '10px Arial';
      ctx.fillStyle = '#333';
      ctx.textAlign = 'center';
      ctx.fillText(`Ø${furo.diametro}`, x, y - 10);
    });
  };

  const handleCanvasClick = (e) => {
    if (!selectedTool || !peca.largura) return;

    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const clickY = e.clientY - rect.top;

    // Verificar se clicou dentro da peça
    const larguraPx = peca.largura * PIXELS_PER_MM * scale;
    const comprimentoPx = peca.comprimento * PIXELS_PER_MM * scale;

    if (
      clickX >= offset.x &&
      clickX <= offset.x + larguraPx &&
      clickY >= offset.y &&
      clickY <= offset.y + comprimentoPx
    ) {
      // Converter coordenadas de pixel para mm
      const furoX = (clickX - offset.x) / (PIXELS_PER_MM * scale);
      const furoY = (clickY - offset.y) / (PIXELS_PER_MM * scale);

      onAddFuro({
        x: Math.round(furoX * 10) / 10, // Arredondar para 0.1mm
        y: Math.round(furoY * 10) / 10,
        tipo: selectedTool,
        diametro: 5, // Padrão
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
        width={800}
        height={600}
        onClick={handleCanvasClick}
        style={{ cursor: selectedTool ? 'crosshair' : 'default' }}
      />
    </div>
  );
}

export default Canvas;