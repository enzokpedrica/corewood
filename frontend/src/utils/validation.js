/**
 * Validações para arquivos MPR
 */

// Tamanho máximo: 10MB
const MAX_FILE_SIZE = 10 * 1024 * 1024;

// Extensões aceitas
const VALID_EXTENSIONS = ['.mpr', '.MPR'];

/**
 * Valida arquivo MPR
 */
export const validateMPRFile = (file) => {
  const errors = [];

  // 1. Verificar se arquivo existe
  if (!file) {
    errors.push('Nenhum arquivo selecionado');
    return { valid: false, errors };
  }

  // 2. Verificar extensão
  const fileName = file.name.toLowerCase();
  const hasValidExtension = VALID_EXTENSIONS.some(ext => 
    fileName.endsWith(ext.toLowerCase())
  );
  
  if (!hasValidExtension) {
    errors.push('Arquivo deve ter extensão .mpr ou .MPR');
  }

  // 3. Verificar tamanho
  if (file.size > MAX_FILE_SIZE) {
    errors.push(`Arquivo muito grande (máx: ${(MAX_FILE_SIZE / 1024 / 1024).toFixed(0)}MB)`);
  }

  if (file.size === 0) {
    errors.push('Arquivo está vazio');
  }

  // 4. Verificar tipo MIME (se disponível)
  if (file.type && !file.type.includes('octet-stream') && file.type !== '') {
    // MPR geralmente é octet-stream ou vazio
    console.warn('Tipo MIME inesperado:', file.type);
  }

  return {
    valid: errors.length === 0,
    errors,
    warnings: []
  };
};

/**
 * Valida configurações antes de gerar PDF
 */
export const validateConfig = (config) => {
  const errors = [];
  const warnings = [];

  // Validar ângulo
  const validAngles = [0, 90, 180, 270];
  if (!validAngles.includes(config.angulo_rotacao)) {
    errors.push('Ângulo de rotação inválido');
  }

  // Validar bordas
  const validBordaComp = [null, '', 'top', 'bottom'];
  const validBordaLarg = [null, '', 'left', 'right'];
  
  if (!validBordaComp.includes(config.posicao_borda_comprimento)) {
    errors.push('Posição de borda comprimento inválida');
  }
  
  if (!validBordaLarg.includes(config.posicao_borda_largura)) {
    errors.push('Posição de borda largura inválida');
  }

  // Validar revisão
  if (config.revisao && config.revisao.length > 20) {
    warnings.push('Revisão muito longa (máx: 20 caracteres)');
  }

  // Validar alerta
  if (config.alerta && config.alerta.length > 150) {
    warnings.push('Texto de alerta muito longo (máx: 150 caracteres)');
  }

  // Verificar se tem pelo menos uma borda ou configuração
  if (!config.posicao_borda_comprimento && 
      !config.posicao_borda_largura && 
      !config.espelhar_peca && 
      config.angulo_rotacao === 0 &&
      !config.revisao &&
      !config.alerta) {
    warnings.push('Nenhuma configuração especial aplicada');
  }

  return {
    valid: errors.length === 0,
    errors,
    warnings
  };
};

/**
 * Formata erros para exibição
 */
export const formatErrors = (errors) => {
  if (!errors || errors.length === 0) return '';
  return errors.join('\n• ');
};

/**
 * Formata warnings para exibição
 */
export const formatWarnings = (warnings) => {
  if (!warnings || warnings.length === 0) return '';
  return warnings.join('\n• ');
};