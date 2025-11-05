import axios from 'axios';

// URL da API (Render ou local)
const API_URL = process.env.REACT_APP_API_URL || 'https://corewood.onrender.com';

const api = axios.create({
  baseURL: API_URL,
  timeout: 60000, // 60 segundos (PDF pode demorar)
});

// ✅ Interceptor para adicionar token automaticamente
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Parse arquivo MPR
export const parseMPR = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await api.post('/parse-mpr', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  
  return response.data;
};

// Gerar PDF
export const generatePDF = async (file, config) => {
  const formData = new FormData();
  formData.append('file', file);
  
  // Adicionar configurações como query params
  const params = new URLSearchParams({
    angulo_rotacao: config.angulo_rotacao || 0,
    espelhar_peca: config.espelhar_peca || false,
    posicao_borda_comprimento: config.posicao_borda_comprimento || '',
    posicao_borda_largura: config.posicao_borda_largura || '',
    revisao: config.revisao || '',
    alerta: config.alerta || ''
  });
  
  const response = await api.post(`/generate-pdf?${params}`, formData, {
    responseType: 'blob',
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  
  return response.data;
};

export default api;