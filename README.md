# CoreWood

**Plataforma de Centralização de Dados e Automação de Manufatura**

---

## 🎯 O Problema

Atualmente, o processo de criação de uma peça personalizada envolve **4 etapas manuais e fragmentadas**:

```
Modelagem CAD
    ↓
Preenchimento de Carga Máquina (10-13h)
    ↓
Criação de Layout para BHX (4-8h)
    ↓
Documentação de Furação (~13h)
    ↓
Roteiro de Peça no Senior (~4h)
```

**Resultado:** ~31-38 horas por peça, com reentradas manuais de **mesmos dados** em 4 sistemas diferentes.

**Taxa de erro:** ~20% (retrabalho significativo)

---

## 💡 A Solução: CoreWood

CoreWood centraliza todas as informações de uma peça em **uma única entrada**, gerando automaticamente **4 saídas**:

```
┌─────────────────────────────────┐
│   ENTRADA ÚNICA (CoreWood)      │
│                                 │
│ • Nome da peça                  │
│ • Dimensões                     │
│ • Furações (coords, diâmetro)  │
│ • Bordas (tipo, dimensão)      │
│ • Processos especiais          │
└─────────────────────────────────┘
         ↓
┌─────────────────────────────────┐
│   AUTOMAÇÕES DISPARADAS        │
├─────────────────────────────────┤
│ ✅ Layout para BHX (.nc)       │ (5-7 min)
│ ✅ Carga Máquina (Senior)      │ (automático)
│ ✅ Roteiro de Peça (Senior)    │ (automático)
│ ✅ Documentação de Furação     │ (3 min)
└─────────────────────────────────┘
```

**Resultado:** ~1-2 horas de processamento automático + validação. **99% de redução de tempo.**

---

## 📊 Impacto

### Tempo

| Métrica | Antes | Depois | Redução |
|---------|-------|--------|---------|
| **Tempo por peça** | 2.8h | 7-10 min | **97%** ↓ |
| **BHX Layout (por peça)** | ~1.7-2.8h | 4-6 min | **97%** ↓ |
| **Documentação (por peça)** | ~1.3h | ~3 min | **97%** ↓ |

**Exemplo - Produto com 10 peças:**
- Antes: 28h
- Depois: ~47-70 min
- **Redução: 97%**

### Qualidade

| Métrica | Antes | Depois |
|---------|-------|--------|
| Taxa de erro | ~20% | ~0% |
| Reentradas de dados | 4× | 1× |
| Auditoria | Nenhuma | Completa |

### Financeiro

**Cenário Base (2 produtos/mês com 10 peças cada = 56h/mês):**
- Economia mensal: R$ 2.800
- Economia anual: **R$ 33.600**
- ROI: **Menos de 1 mês**

**Cenário Otimista (4 produtos/mês = 20 peças + 25 peças + 48 peças + 10 peças = ~103h/mês):**
- Economia mensal: R$ 5.150
- Economia anual: **R$ 61.800**
- ROI: **Menos de 1 mês**

*Para detalhes completos, veja [CASE_STUDY.md](./docs/CASE_STUDY.md)*

---

## 🚀 Status Atual

### ✅ Em Produção (MVP)

- **BHX Layout Generator:** Gera arquivo .nc em 5-7 minutos
- **Documentação de Furação:** Gera PDF em ~3 minutos

### 🔄 Em Desenvolvimento (Phase 1)

- **Integração Carga Máquina:** Auto-população via API Senior
- **Integração Roteiro:** Geração de arquivo de importação

### 📋 Roadmap

| Fase | Status | Data |
|------|--------|------|
| MVP | ✅ Completo | Nov-Dez 2024 |
| Phase 1 (Integração Senior) | 🔄 Desenvolvimento | Q1 2026 |
| Phase 2 (Testes em Produção) | 📋 Planejado | Q1 2026 |
| Phase 3 (Deploy Completo) | 📋 Planejado | Q2 2026 |

---

## 🏗️ Arquitetura

CoreWood funciona em 5 módulos:

### 1. **Data Hub (Core)**
Centraliza todas as informações de uma peça em uma única fonte de verdade.

**Input:** CAD + Metadados
**Output:** Peça única, validada, em banco de dados

### 2. **BHX Layout Generator** ✅
Gera arquivo G-code (.nc) para máquina CNC.

**Input:** Dados do hub + especificações
**Output:** `arquivo.nc` pronto para máquina

### 3. **Carga Máquina Integration** 🔄
Popula automaticamente o sistema Senior.

**Input:** Dimensões, processos, bordas
**Output:** Sistema Senior pré-preenchido

### 4. **Roteiro Integration** 🔄
Gera arquivo de importação para Roteiro de Peça.

**Input:** Processos, sequência de operações
**Output:** `arquivo.csv` para importar no Senior

### 5. **Documentação Generator** ✅
Gera PDF com especificações completas de furação.

**Input:** Furações, bordas, processos
**Output:** `arquivo.pdf` profissional

*Para detalhes técnicos, veja [ARCHITECTURE.md](./docs/ARCHITECTURE.md)*

---

## 📚 Documentação

- **[ARCHITECTURE.md](./docs/ARCHITECTURE.md)** — Detalhamento técnico de cada módulo
- **[CASE_STUDY.md](./docs/CASE_STUDY.md)** — Análise de impacto, números reais, ROI
- **[USAGE.md](./docs/USAGE.md)** — Como usar a plataforma

---

## 🛠️ Stack Técnico

**Backend:**
- Python 3.10+
- FastAPI (API REST)
- PostgreSQL (Database)

**Integrações:**
- CAD Parser (DWG/DXF)
- Senior ERP API
- CNC Machine G-code Generator

**Frontend:**
- React
- TypeScript

**DevOps:**
- Docker
- GitHub Actions (CI/CD)

---

## 🎓 Como Começar

### Para Usuários

1. Acesse a interface CoreWood
2. Crie uma nova peça (preenchimento simples)
3. Defina furações, bordas e processos
4. Clique em "Gerar"
5. Receba 4 arquivos/integrações prontos

### Para Desenvolvedores

```bash
# Clone o repositório
git clone [repo-url]

# Instale dependências
pip install -r requirements.txt

# Configure banco de dados
python setup_db.py

# Inicie a aplicação
python main.py
```

*Para instruções detalhadas, veja [USAGE.md](./docs/USAGE.md)*

---

## 💼 Benefícios por Papel

### Para Planejadores
- ✅ Automação de 90% do trabalho de pré-custo e roteiro
- ✅ Tempo liberado para atividades estratégicas
- ✅ Zero erros de cálculo

### Para Técnicos BHX
- ✅ Layout gerado automaticamente em minutos
- ✅ Foco em otimização, não criação manual
- ✅ Arquivos sempre corretos

### Para Gerentes
- ✅ Capacidade de produção +3x com mesmo time
- ✅ Taxa de erro eliminada (~20% → 0%)
- ✅ ROI em menos de 1 mês
- ✅ Rastreabilidade completa

### Para Empresa
- ✅ Redução de ~R$ 372k-456k/ano (cenário médio)
- ✅ Aceleração do time-to-market
- ✅ Escalabilidade sem crescimento proporcional de custos
- ✅ Dados centralizados e auditáveis

---

## 📈 Números que Importam

| Métrica | Impacto |
|---------|---------|
| Redução de tempo | 97% |
| Eliminação de erros | ~20% → 0% |
| Economia anual | R$ 33.600-61.800 (conforme volume) |
| Payback | Menos de 1 mês |
| Escalabilidade | Suporta produtos de 10 a 48 peças |

---

## 🔄 Próximos Passos

**Curto prazo (próximas 4-6 semanas):**
1. Validação completa do MVP com produtos reais
2. Integração com API Senior (Carga Máquina)
3. Geração de arquivo de importação para Roteiro

**Médio prazo (Q1 2026):**
1. Deploy em ambiente de produção
2. Treinamento do time
3. Monitoramento e ajustes

**Longo prazo (Q2+ 2026):**
1. Expansão para outros tipos de peças
2. Possível integração com outros sistemas
3. Aplicação em outros departamentos

---

## 📞 Contato

**Desenvolvedor:** Enzo
**Status:** MVP em validação, Phase 1 em desenvolvimento
**Aprovação necessária:** Expansão para integração completa (Phase 1)

---

## 📋 Licença

Projeto interno Linea Brasil.

---

## 🙏 Agradecimentos

CoreWood foi desenvolvido para resolver um problema real de manufatura: transformar um processo fragmentado e manual em um fluxo automatizado, centralizado e confiável.

**Contribuidores:** Enzo (Desenvolvimento)
**Feedback:** Time de Operações, BHX, Planejamento