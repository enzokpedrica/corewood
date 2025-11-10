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
  
  // Converter bordas para JSON string
  const bordasJson = config.bordas ? JSON.stringify(config.bordas) : '{}';
  
  // Adicionar configurações como query params
  const params = new URLSearchParams({
    angulo_rotacao: config.angulo_rotacao || 0,
    espelhar_peca: config.espelhar_peca || false,
    bordas: bordasJson,
    revisao: config.revisao || '',
    alerta: config.alerta || ''
  });
  
  const response = await api.post(`/generate-pdf?${params}`, formData, {
    responseType: 'blob',
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  
  return response.data;
};

/**
 * Gerar múltiplos PDFs em lote e retornar ZIP
 */
export const generatePDFBatch = async (arquivos, onProgress) => {
  const formData = new FormData();
  
  // Adicionar todos os arquivos
  arquivos.forEach((arq, index) => {
    formData.append('files', arq.file);
  });
  
  // Adicionar configurações como JSON - CORRIGIDO
  const configs = arquivos.map(arq => ({
    angulo_rotacao: arq.config.angulo_rotacao || 0,
    espelhar_peca: arq.config.espelhar_peca || false,
    bordas: arq.config.bordas || { top: null, bottom: null, left: null, right: null },
    revisao: arq.config.revisao || '',
    alerta: arq.config.alerta || ''
  }));

  console.log('📤 Enviando configs:', configs);
  formData.append('configs', JSON.stringify(configs));
  
  try {
    const response = await axios.post(
      `${API_URL}/generate-pdf-batch`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        responseType: 'blob',
        onUploadProgress: (progressEvent) => {
          if (onProgress && progressEvent.total) {
            const percentCompleted = Math.round(
              (progressEvent.loaded * 100) / progressEvent.total
            );
            // Estimativa de progresso
            const current = Math.floor((percentCompleted / 100) * arquivos.length);
            onProgress(current, arquivos.length);
          }
        }
      }
    );
    
    // Chamar progresso final
    if (onProgress) {
      onProgress(arquivos.length, arquivos.length);
    }
    
    return response.data;
  } catch (error) {
    console.error('Erro ao gerar PDFs em lote:', error);
    throw error;
  }
};

/**
 * Exportar peça do editor como MPR
 */
export const exportarMPR = async (pecaData) => {
  try {
    const response = await axios.post(
      `${API_URL}/editor/export-mpr`,
      pecaData,
      {
        responseType: 'blob'
      }
    );
    
    return response.data;
  } catch (error) {
    console.error('Erro ao exportar MPR:', error);
    throw error;
  }
};

/**
 * Gerar PDF direto do editor
 */
export const gerarPDFEditor = async (pecaData) => {
  try {
    const response = await axios.post(
      `${API_URL}/editor/generate-pdf`,
      pecaData,
      {
        responseType: 'blob'
      }
    );
    
    return response.data;
  } catch (error) {
    console.error('Erro ao gerar PDF do editor:', error);
    throw error;
  }
};

export default api;