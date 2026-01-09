import React, { useRef, useEffect, useState, useCallback } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls';
import './Canvas3D.css';

function Canvas3D({ 
  peca, 
  bordas, 
  transformacao, 
  selectedFuro, 
  onSelectFuro 
}) {
  const containerRef = useRef(null);
  const rendererRef = useRef(null);
  const sceneRef = useRef(null);
  const cameraRef = useRef(null);
  const controlsRef = useRef(null);
  const meshRef = useRef(null);
  const furosGroupRef = useRef(null);
  const animationIdRef = useRef(null);
  
  const [tooltip, setTooltip] = useState(null);

  // Cores do tema industrial
  const COLORS = {
    background: 0xb8c5e2,
    grid: 0x9aaccd,
    piece: 0xf0d0d0,        // Cor madeira MDF
    pieceEdge: 0xc04040 ,
    furoVerticalTop: 0xff4757,
    furoVerticalBottom: 0x2f3542,
    furoHorizontal: 0x3742fa,
    selected: 0x00ff88,
    bordaCor: 0x2ed573,
    bordaPardo: 0xff7f50,
    pinca: 0x4a4a4a,        // Cor metal da pinça
    pincaDetalhe: 0x2a2a2a, // Detalhe escuro da pinça
    contornoBase: 0xe05050  // Contorno vermelho na base
  };

  // Inicializar cena Three.js
  const initScene = useCallback(() => {
    if (!containerRef.current) return;

    const container = containerRef.current;
    const width = container.clientWidth;
    const height = container.clientHeight;

    // Scene
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(COLORS.background);
    sceneRef.current = scene;

    // Camera
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 10000);
    camera.position.set(500, 400, 500);
    cameraRef.current = camera;

    // Renderer
    const renderer = new THREE.WebGLRenderer({ 
      antialias: true,
      alpha: true 
    });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    container.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    // Controls - só zoom, sem rotação
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableRotate = false;  // desabilita rotação
    controls.enablePan = false;     // desabilita arrastar
    controls.enableZoom = true;     // mantém zoom
    controls.minDistance = 100;
    controls.maxDistance = 2000;

    // Iluminação
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
    scene.add(ambientLight);

    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
    directionalLight.position.set(200, 400, 200);
    directionalLight.castShadow = true;
    directionalLight.shadow.mapSize.width = 2048;
    directionalLight.shadow.mapSize.height = 2048;
    scene.add(directionalLight);

    const fillLight = new THREE.DirectionalLight(0xffffff, 0.3);
    fillLight.position.set(-200, 200, -200);
    scene.add(fillLight);

    // Grid helper
    const gridHelper = new THREE.GridHelper(1000, 20, COLORS.grid, COLORS.grid);
    gridHelper.position.y = -1;
    gridHelper.visible = false;  // invisível
    scene.add(gridHelper);

    // Grupo para furos
    furosGroupRef.current = new THREE.Group();
    scene.add(furosGroupRef.current);

    // Animation loop
    const animate = () => {
      animationIdRef.current = requestAnimationFrame(animate);
      controls.update();
      renderer.render(scene, camera);
    };
    animate();

    // Resize handler
    const handleResize = () => {
      if (!containerRef.current) return;
      const w = containerRef.current.clientWidth;
      const h = containerRef.current.clientHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };

    const resizeObserver = new ResizeObserver(handleResize);
    resizeObserver.observe(container);

    return () => {
      resizeObserver.disconnect();
      cancelAnimationFrame(animationIdRef.current);
      controls.dispose();
      renderer.dispose();
      container.removeChild(renderer.domElement);
    };
  }, []);

  // Criar geometria da peça
  const createPiece = useCallback(() => {
    if (!sceneRef.current || !peca.comprimento || !peca.largura) return;

    // Remover peça anterior
    if (meshRef.current) {
      sceneRef.current.remove(meshRef.current);
      meshRef.current.geometry.dispose();
      meshRef.current.material.dispose();
    }

    // Remover pinça anterior
    const pincaAnterior = sceneRef.current.getObjectByName('pinca');
    if (pincaAnterior) {
      sceneRef.current.remove(pincaAnterior);
    }

    // Remover bordas anteriores (objetos sem nome que não são grid, luz, ou furos)
    const objetosParaRemover = [];
    sceneRef.current.traverse((obj) => {
      if (obj.isMesh && !obj.name && obj !== meshRef.current && !furosGroupRef.current?.children.includes(obj)) {
        objetosParaRemover.push(obj);
      }
    });
    objetosParaRemover.forEach(obj => {
      if (obj.geometry) obj.geometry.dispose();
      if (obj.material) obj.material.dispose();
      sceneRef.current.remove(obj);
    });

    const rotacao = transformacao?.rotacao || 0;
    const espelhado = transformacao?.espelhado || false;

    // Dimensões considerando rotação
    let width = peca.comprimento;
    let depth = peca.largura;
    const height = peca.espessura || 15;

    if (rotacao === 90 || rotacao === 270) {
      [width, depth] = [depth, width];
    }

    // Geometria da peça
    const geometry = new THREE.BoxGeometry(width, height, depth);
    
    // Material com transparência
    const material = new THREE.MeshStandardMaterial({
      color: COLORS.piece,
      roughness: 0.8,
      metalness: 0.1,
      flatShading: false,
      transparent: true,
      opacity: 0.8,
      side: THREE.DoubleSide
    });

    const mesh = new THREE.Mesh(geometry, material);
    mesh.position.y = height / 2;
    mesh.castShadow = true;
    mesh.receiveShadow = true;

    // Aplicar espelhamento
    if (espelhado) {
      mesh.scale.z = -1;
    }

    // Bordas da peça (wireframe)
    const edges = new THREE.EdgesGeometry(geometry);
    const edgeMaterial = new THREE.LineBasicMaterial({ 
      color: COLORS.pieceEdge,
      linewidth: 2 
    });
    const wireframe = new THREE.LineSegments(edges, edgeMaterial);
    mesh.add(wireframe);

    // Contorno vermelho na base da peça
    const baseShape = new THREE.Shape();
    baseShape.moveTo(-width/2, -depth/2);
    baseShape.lineTo(width/2, -depth/2);
    baseShape.lineTo(width/2, depth/2);
    baseShape.lineTo(-width/2, depth/2);
    baseShape.lineTo(-width/2, -depth/2);
    
    const basePoints = baseShape.getPoints();
    const baseGeometry = new THREE.BufferGeometry().setFromPoints(basePoints);
    const baseMaterial = new THREE.LineBasicMaterial({ 
      color: COLORS.contornoBase, 
      linewidth: 3 
    });
    const baseLine = new THREE.Line(baseGeometry, baseMaterial);
    baseLine.rotation.x = -Math.PI / 2;
    baseLine.position.y = 0.5; // Logo acima do chão
    sceneRef.current.add(baseLine);

    sceneRef.current.add(mesh);
    meshRef.current = mesh;

    // Centralizar câmera
    const maxDim = Math.max(width, depth, height);
    cameraRef.current.position.set(maxDim * 1.2, maxDim * 0.8, maxDim * 1.2);
    controlsRef.current.target.set(0, height / 2, 0);
    controlsRef.current.update();

    // Criar bordas coloridas
    createBordas(width, height, depth);

    // Criar pinça/garra no canto superior esquerdo
    createPinca(width, height, depth);

  }, [peca, transformacao, bordas]);

  // Criar bordas coloridas
  const createBordas = (width, height, depth) => {
    if (!bordas || !sceneRef.current) return;

    const espessuraBorda = 2;
    const offset = 0.5;

    const createBordaMesh = (w, h, d, position, color) => {
      if (!color || color === 'nenhum') return null;
      
      const colorHex = color === 'cor' ? COLORS.bordaCor : COLORS.bordaPardo;
      const geo = new THREE.BoxGeometry(w, h, d);
      const mat = new THREE.MeshStandardMaterial({ 
        color: colorHex,
        roughness: 0.5 
      });
      const mesh = new THREE.Mesh(geo, mat);
      mesh.position.set(...position);
      return mesh;
    };

    // Topo (Z negativo)
    const topoMesh = createBordaMesh(
      width, height, espessuraBorda,
      [0, height/2, -depth/2 - offset],
      bordas.topo
    );
    if (topoMesh) sceneRef.current.add(topoMesh);

    // Baixo (Z positivo)
    const baixoMesh = createBordaMesh(
      width, height, espessuraBorda,
      [0, height/2, depth/2 + offset],
      bordas.baixo
    );
    if (baixoMesh) sceneRef.current.add(baixoMesh);

    // Esquerda (X negativo)
    const esquerdaMesh = createBordaMesh(
      espessuraBorda, height, depth,
      [-width/2 - offset, height/2, 0],
      bordas.esquerda
    );
    if (esquerdaMesh) sceneRef.current.add(esquerdaMesh);

    // Direita (X positivo)
    const direitaMesh = createBordaMesh(
      espessuraBorda, height, depth,
      [width/2 + offset, height/2, 0],
      bordas.direita
    );
    if (direitaMesh) sceneRef.current.add(direitaMesh);
  };

  // Criar pinças no topo da peça (2 pinças distribuídas igualmente)
  const createPinca = (width, height, depth) => {
    if (!sceneRef.current) return;

    const pincaGroup = new THREE.Group();
    pincaGroup.name = 'pinca';

    // Dimensões da pinça
    const pincaWidth = Math.min(30, width * 0.06);
    const pincaDepth = 12;
    const pincaHeight = height + 15;

    // Material metálico
    const metalMaterial = new THREE.MeshStandardMaterial({
      color: COLORS.pinca,
      roughness: 0.3,
      metalness: 0.8
    });

    const metalDarkMaterial = new THREE.MeshStandardMaterial({
      color: COLORS.pincaDetalhe,
      roughness: 0.4,
      metalness: 0.7
    });

    // Posições X das duas pinças (divididas igualmente)
    const posicao1 = -width / 4;  // 25% da esquerda
    const posicao2 = width / 4;   // 25% da direita
    const posicoes = [posicao1, posicao2];

    posicoes.forEach((posX) => {
      // Parte vertical (garra que desce)
      const pincaVerticalGeo = new THREE.BoxGeometry(pincaWidth, pincaHeight, pincaDepth);
      const meshVertical = new THREE.Mesh(pincaVerticalGeo, metalMaterial);
      meshVertical.position.set(
        posX,
        pincaHeight / 2,
        -depth / 2 - pincaDepth / 2 - 15
      );
      pincaGroup.add(meshVertical);

      // Parte que encosta na peça (horizontal, entra na peça)
      const pincaContatoGeo = new THREE.BoxGeometry(pincaWidth, height, 8);
      const meshContato = new THREE.Mesh(pincaContatoGeo, metalDarkMaterial);
      meshContato.position.set(
        posX,
        height / 2,
        -depth / 2 - 10
      );
      pincaGroup.add(meshContato);

      // Detalhe superior (cabeça da pinça)
      const cabecaGeo = new THREE.BoxGeometry(pincaWidth + 10, 8, pincaDepth + 6);
      const cabecaMesh = new THREE.Mesh(cabecaGeo, metalMaterial);
      cabecaMesh.position.set(
        posX,
        pincaHeight + 4,
        -depth / 2 - pincaDepth / 2 - 15
      );
      pincaGroup.add(cabecaMesh);

      // Indicador amarelo em cima
      const indicadorGeo = new THREE.BoxGeometry(pincaWidth + 6, 4, 4);
      const indicadorMaterial = new THREE.MeshStandardMaterial({
        color: 0xffcc00,
        roughness: 0.5,
        metalness: 0.3,
        emissive: 0xffcc00,
        emissiveIntensity: 0.2
      });
      const indicadorMesh = new THREE.Mesh(indicadorGeo, indicadorMaterial);
      indicadorMesh.position.set(
        posX,
        pincaHeight + 10,
        -depth / 2 - pincaDepth / 2 - 15
      );
      pincaGroup.add(indicadorMesh);
    });
    sceneRef.current.add(pincaGroup);
  };

  // Criar furos
  const createFuros = useCallback(() => {
    if (!furosGroupRef.current || !peca.comprimento || !peca.largura) return;

    // Limpar furos anteriores
    while (furosGroupRef.current.children.length > 0) {
      const child = furosGroupRef.current.children[0];
      if (child.geometry) child.geometry.dispose();
      if (child.material) child.material.dispose();
      furosGroupRef.current.remove(child);
    }

    const rotacao = transformacao?.rotacao || 0;
    const espelhado = transformacao?.espelhado || false;
    const espessura = peca.espessura || 15;

    // Dimensões base
    let baseWidth = peca.comprimento;
    let baseDepth = peca.largura;

    if (rotacao === 90 || rotacao === 270) {
      [baseWidth, baseDepth] = [baseDepth, baseWidth];
    }

    // Função para transformar coordenadas
    const transformCoord = (x, y) => {
      let nx = x, ny = y;

      if (espelhado) {
        ny = peca.largura - y;
      }

      if (rotacao === 90) {
        [nx, ny] = [peca.largura - ny, x];
      } else if (rotacao === 180) {
        nx = peca.comprimento - x;
        ny = peca.largura - y;
      } else if (rotacao === 270) {
        [nx, ny] = [y, peca.comprimento - x];
      }

      return { x: nx, y: ny };
    };

    // Furos verticais
    peca.furos?.forEach((furo, index) => {
      const coords = transformCoord(furo.x, furo.y);
      const isSelected = selectedFuro?.tipo === 'vertical' && selectedFuro?.index === index;
      const isBottom = furo.lado === 'LI';

      const radius = furo.diametro / 2;
      const depth = Math.min(furo.profundidade || 11, espessura);

      const geometry = new THREE.CylinderGeometry(radius, radius, depth, 32);
      const material = new THREE.MeshStandardMaterial({
        color: isSelected ? COLORS.selected : (isBottom ? COLORS.furoVerticalBottom : COLORS.furoVerticalTop),
        roughness: 0.3,
        emissive: isSelected ? COLORS.selected : 0x000000,
        emissiveIntensity: isSelected ? 0.3 : 0
      });

      const mesh = new THREE.Mesh(geometry, material);

      // Posição: converter de coordenadas 2D para 3D
      const posX = coords.x - baseWidth / 2;
      const posZ = coords.y - baseDepth / 2;
      const posY = isBottom ? depth / 2 : espessura - depth / 2;

      mesh.position.set(posX, posY, posZ);
      mesh.userData = { tipo: 'vertical', index, furo };

      furosGroupRef.current.add(mesh);
    });

    // Furos horizontais
    peca.furosHorizontais?.forEach((furo, index) => {
      const furoX = furo.x === 'x' ? peca.comprimento : furo.x;
      const coords = transformCoord(furoX, furo.y);
      const isSelected = selectedFuro?.tipo === 'horizontal' && selectedFuro?.index === index;

      const radius = furo.diametro / 2;
      const depth = furo.profundidade || 22;

      const geometry = new THREE.CylinderGeometry(radius, radius, depth, 32);
      const material = new THREE.MeshStandardMaterial({
        color: isSelected ? COLORS.selected : COLORS.furoHorizontal,
        roughness: 0.3,
        emissive: isSelected ? COLORS.selected : 0x000000,
        emissiveIntensity: isSelected ? 0.3 : 0
      });

      const mesh = new THREE.Mesh(geometry, material);

      // Rotacionar para horizontal baseado no lado
      const lado = furo.lado || 'XP';
      const posX = coords.x - baseWidth / 2;
      const posZ = coords.y - baseDepth / 2;
      const posY = furo.z || espessura / 2;

      if (lado === 'XP' || lado === 'XM') {
        mesh.rotation.z = Math.PI / 2;
        mesh.position.set(
          lado === 'XP' ? baseWidth/2 - depth/2 : -baseWidth/2 + depth/2,
          posY,
          posZ
        );
      } else {
        mesh.rotation.x = Math.PI / 2;
        mesh.position.set(
          posX,
          posY,
          lado === 'YP' ? baseDepth/2 - depth/2 : -baseDepth/2 + depth/2
        );
      }

      mesh.userData = { tipo: 'horizontal', index, furo };
      furosGroupRef.current.add(mesh);
    });

  }, [peca, transformacao, selectedFuro]);

  // Raycasting para seleção de furos
  const handleClick = useCallback((event) => {
    if (!rendererRef.current || !cameraRef.current || !furosGroupRef.current) return;

    const rect = rendererRef.current.domElement.getBoundingClientRect();
    const mouse = new THREE.Vector2(
      ((event.clientX - rect.left) / rect.width) * 2 - 1,
      -((event.clientY - rect.top) / rect.height) * 2 + 1
    );

    const raycaster = new THREE.Raycaster();
    raycaster.setFromCamera(mouse, cameraRef.current);

    const intersects = raycaster.intersectObjects(furosGroupRef.current.children);

    if (intersects.length > 0) {
      const { tipo, index, furo } = intersects[0].object.userData;
      onSelectFuro?.({ tipo, index, furo });
    }
  }, [onSelectFuro]);

  // Tooltip no hover
  const handleMouseMove = useCallback((event) => {
    if (!rendererRef.current || !cameraRef.current || !furosGroupRef.current) return;

    const rect = rendererRef.current.domElement.getBoundingClientRect();
    const mouse = new THREE.Vector2(
      ((event.clientX - rect.left) / rect.width) * 2 - 1,
      -((event.clientY - rect.top) / rect.height) * 2 + 1
    );

    const raycaster = new THREE.Raycaster();
    raycaster.setFromCamera(mouse, cameraRef.current);

    const intersects = raycaster.intersectObjects(furosGroupRef.current.children);

    if (intersects.length > 0) {
      const { tipo, index, furo } = intersects[0].object.userData;
      setTooltip({
        x: event.clientX - rect.left,
        y: event.clientY - rect.top,
        tipo,
        index,
        furo
      });
    } else {
      setTooltip(null);
    }
  }, []);

  // Inicializar cena
  useEffect(() => {
    const cleanup = initScene();
    return cleanup;
  }, [initScene]);

  // Atualizar peça quando dados mudam
  useEffect(() => {
    createPiece();
  }, [createPiece]);

  // Atualizar furos quando dados mudam
  useEffect(() => {
    createFuros();
  }, [createFuros]);

  // Event listeners
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    container.addEventListener('click', handleClick);
    container.addEventListener('mousemove', handleMouseMove);

    return () => {
      container.removeEventListener('click', handleClick);
      container.removeEventListener('mousemove', handleMouseMove);
    };
  }, [handleClick, handleMouseMove]);

  return (
    <div className="canvas3d-container" ref={containerRef}>
      {/* Tooltip flutuante */}
      {tooltip && (
        <div 
          className="furo-tooltip"
          style={{ 
            left: tooltip.x + 15, 
            top: tooltip.y - 10 
          }}
        >
          <div className="tooltip-header">
            {tooltip.tipo === 'vertical' ? '⬇️' : '➡️'} Furo {tooltip.tipo === 'vertical' ? 'V' : 'H'}{tooltip.index + 1}
          </div>
          <div className="tooltip-body">
            <span>Ø{tooltip.furo.diametro}mm</span>
            <span>Prof: {tooltip.furo.profundidade || 11}mm</span>
            <span>Pos: ({tooltip.furo.x}, {tooltip.furo.y})</span>
            {tooltip.furo.lado && <span>Lado: {tooltip.furo.lado}</span>}
          </div>
        </div>
      )}

      {/* Indicadores de eixo */}
      <div className="axis-indicator">
        <div className="axis x">X</div>
        <div className="axis y">Y</div>
        <div className="axis z">Z</div>
      </div>

      {/* Info da peça */}
      {peca.comprimento && peca.largura && (
        <div className="piece-info">
          <span>{peca.comprimento} × {peca.largura} × {peca.espessura || 15}mm</span>
        </div>
      )}

      {/* Controles de visualização */}
      <div className="view-controls">
        <button 
          className="view-btn" 
          onClick={() => {
            if (cameraRef.current && controlsRef.current) {
              const maxDim = Math.max(peca.comprimento || 100, peca.largura || 100);
              cameraRef.current.position.set(0, maxDim * 1.5, 0);
              controlsRef.current.update();
            }
          }}
          title="Vista Superior"
        >
          ⬆️
        </button>
        <button 
          className="view-btn"
          onClick={() => {
            if (cameraRef.current && controlsRef.current) {
              const maxDim = Math.max(peca.comprimento || 100, peca.largura || 100);
              cameraRef.current.position.set(maxDim * 1.5, maxDim * 0.5, 0);
              controlsRef.current.update();
            }
          }}
          title="Vista Frontal"
        >
          ⏹️
        </button>
        <button 
          className="view-btn"
          onClick={() => {
            if (cameraRef.current && controlsRef.current) {
              const maxDim = Math.max(peca.comprimento || 100, peca.largura || 100);
              cameraRef.current.position.set(maxDim * 1.2, maxDim * 0.8, maxDim * 1.2);
              controlsRef.current.update();
            }
          }}
          title="Vista Isométrica"
        >
          🔷
        </button>
      </div>
    </div>
  );
}

export default Canvas3D;