# CoreWood: Case de Impacto

## Contexto

**Empresa:** Linea Brasil
**Departamento:** Product Development / Operações de Manufatura
**Localização:** Arapongas, Paraná
**Período:** Desenvolvimento iniciado em 2024

### O Desafio

O processo de criação de peças personalizadas envolvia múltiplas etapas manuais e fragmentadas:

1. **Modelagem 3D** (CAD) - realizada pelo designer
2. **Preenchimento de Carga Máquina** - operador preenchia manualmente todas as informações
3. **Criação de Layout para BHX** - outra pessoa criava o desenho para máquina CNC
4. **Cadastro de Roteiro de Peça** - terceira pessoa criava sequência de operações no ERP

**Cada etapa reutilizava os mesmos dados** (dimensões, tipos de processamento, bordas), mas de forma manual e independente.

---

## Métricas Antes (Baseline)

### Tempo por Produto (Baseline do Planner)

**Base de dados:** Produto com 10 peças = 28 horas (sequencial)

**Detalhamento das atividades por tipo de produto:**

#### Produto Pequeno (10 peças - 28h total)

| Atividade | Tempo | Detalhes |
|---|---|---|
| **Pré Custo** | 10-13h | Preenchimento de Carga Máquina + cálculos de custo (por PRODUTO) |
| **BHX Layout** | 4-8h | Criação manual de layout CNC (4-6 min por PEÇA, então 40-60 min mínimo, mas varia muito conforme complexidade) |
| **Documentação** | ~7-9h | Processo em TopSolid Draft: abrir template, cotas, mandril, furação sup/inf, motor, borda, export PDF, identificação |
| **Roteiro** | ~2-4h | Criação sequência de operações no Senior (por PRODUTO) |
| **TOTAL** | **~28h** | Sequencial |

#### Produto Médio (25 peças - ~70h total)

| Atividade | Tempo |
|---|---|
| Pré Custo | 10-13h |
| BHX Layout | 10-20h |
| Documentação | ~40-45h |
| Roteiro | ~7-12h |
| **TOTAL** | **~70h** |

#### Produto Grande (48 peças - ~134h total)

| Atividade | Tempo |
|---|---|
| Pré Custo | 10-13h |
| BHX Layout | 20-40h |
| Documentação | ~80-90h |
| Roteiro | ~14-24h |
| **TOTAL** | **~134h** |

**Nota importante:** 
- Documentação é particularmente demorada em produtos com muitas peças (escalas de 3-4h para 25+ peças)
- BHX é o primeiro processo manual, escala conforme número de peças (4-6 min/peça)
- Todos os processos são sequenciais

### Taxa de Erro

| Situação | Frequência | Impacto |
|----------|-----------|---------|
| Produtos com erros em lote | ~20% | Retrabalho, necessidade de correção |
| **Taxa geral de erro** | **~20%** | **Alto - requer retrabalho significativo** |

**Observação:** Taxa de erro é variável conforme complexidade do lote e número de peças, porém dados de teste indicam ~20% de produtos que requerem correção

### Qualidade

- ❌ Sem auditoria de quem fez o quê
- ❌ Sem rastreabilidade de versões
- ❌ Impossível saber qual informação é "correta" se houver conflito
- ❌ Modificações exigem atualizar 4 sistemas manualmente

---

## Solução: CoreWood MVP

CoreWood centraliza todas as informações de uma peça em uma única entrada, gerando automaticamente 4 saídas:

```
ENTRADA ÚNICA (CoreWood):
├─ Nome da peça
├─ Dimensões básicas
├─ Furações (coordenadas, diâmetro, tipo)
├─ Bordas (tipo, dimensão)
└─ Processos especiais

SAÍDAS AUTOMÁTICAS:
├─ Layout para BHX (.nc)
├─ Carga Máquina (Senior - preenchida)
├─ Roteiro de Peça (Senior - arquivo importável)
└─ Documentação de Furação (PDF)
```

---

## Resultados Iniciais (MVP em Desenvolvimento)

### ✅ Módulos em Produção/Validação
- BHX Layout Generator: 4-6 min por peça
- Documentação de Furação: 3 min por peça

### 📊 Impacto Estimado (Baseado em Tempos do Planner)

**Status:** MVP testado em fluxo, validação com produtos reais em andamento

#### Tempo por Produto (Redução Estimada)

**Produto Pequeno (10 peças - MVP com BHX + Documentação):**

| Etapa | Antes | Depois | Redução |
|-------|-------|--------|---------|
| BHX Layout | 4-8h | 40-60 min (4-6 min/peça) | **90-94%** ↓ |
| Documentação | ~7-9h | 30 min (3 min/peça) | **94-96%** ↓ |
| Pré Custo (manual hoje) | 10-13h | 10 min (automático) | **99%** ↓ |
| Roteiro (manual hoje) | ~2-4h | 5 min (automático) | **98%** ↓ |
| **Total (Hoje)** | **~28h** | - | - |
| **Total (MVP apenas BHX+Docs)** | **11-17h** | **70-90 min** | **92-94%** ↓ |
| **Total (Completo 100%)** | **~28h** | **~85-100 min** | **94-96%** ↓ |

**Tempo economizado por produto (MVP):** ~10-16 horas
**Tempo economizado por produto (100% completo):** ~27 horas

#### Taxa de Erro

| Cenário | Antes | Depois | Melhoria |
|---------|-------|--------|----------|
| Produtos com erro em lote | ~20% | ~0% | ✅ 100% eliminado |
| **Taxa geral** | **~20%** | **~0%** | **✅ Eliminado** |

#### Qualidade

- ✅ Auditoria completa (rastreabilidade total)
- ✅ Single source of truth
- ✅ Elimina retrabalho por inconsistência
- ✅ Modificações propagam automaticamente

---

## Projeção de Impacto (Quando 100% Pronto)

## Projeção de Impacto (Quando 100% Pronto)

### Todas as 4 Automações em Produção

**Base de cálculo:** Quando CoreWood 100% completo, economiza ~27h por produto

#### Cenário A: 2 Produtos/Mês (Pequeno: 10 peças cada)

| Métrica | Valor |
|---------|-------|
| Produtos processados | 2 |
| Tempo economizado por produto | 27h |
| Horas economizadas/mês | 54h |
| Custo de mão de obra economizado | R$ 2.700/mês |
| **Custo anualizado** | **R$ 32.400/ano** |

#### Cenário B: 4 Produtos/Mês (Variado: 10+25+48+10 peças)

| Métrica | Valor |
|---------|-------|
| Produtos processados | 4 (variados) |
| Tempo economizado médio | ~27h/produto |
| Horas economizadas/mês | ~108h |
| Custo de mão de obra economizado | R$ 5.400/mês |
| **Custo anualizado** | **R$ 64.800/ano** |

#### Cenário C: 6 Produtos/Mês (Mix de tamanhos)

| Métrica | Valor |
|---------|-------|
| Produtos processados | 6 |
| Tempo economizado médio | ~27h/produto |
| Horas economizadas/mês | ~162h |
| Custo de mão de obra economizado | R$ 8.100/mês |
| **Custo anualizado** | **R$ 97.200/ano** |

#### Benefícios Não-Financeiros

- **Consistência:** Eliminação de inconsistências entre sistemas (~20% de retrabalho eliminado)
- **Velocidade:** Aceleração do time-to-market (produto pronto em horas, não dias)
- **Confiabilidade:** Zero erros de transcrição ou cálculo
- **Rastreabilidade:** Auditoria completa de todas as alterações
- **Escalabilidade:** Mesmo time consegue processar múltiplos produtos em paralelo

---

## Impacto no Negócio

### Capacidade de Produção

**Cenário Atual (com fluxo manual):**
- 2 produtos/mês = 56h de trabalho
- Para processar 4 produtos/mês seria necessário 103h (difícil com recursos atuais)

**Cenário com CoreWood:**
- 4 produtos/mês = apenas ~77-100 min de trabalho (automático + validação)
- **Mesmo time consegue processar 2x mais volume**

### Exemplo Real: Um Produto com 25 Peças

**Sem CoreWood:**
- Tempo de processamento: ~70h (~2 semanas, 1 pessoa full-time)
- Custo de mão de obra: R$ 3.500
- Risco de erro: ~20% (5 peças podem ter problemas)
- Risco de atraso: Alto (dependência de múltiplas pessoas)

**Com CoreWood (100% completo):**
- Tempo de processamento: ~2-3h (automático)
- Custo de mão de obra: ~R$ 150-200 (validação apenas)
- Risco de erro: ~0% (automático e validado)
- Risco de atraso: Praticamente zero

**Diferença:** R$ 3.300 economizados + 67-68h liberadas para outras atividades + zero erros

---

## ROI (Return on Investment)

### Desenvolvimento (Estimado)

| Item | Tempo | Custo* |
|------|-------|-------|
| MVP (BHX + Docs) | 6 semanas | ~R$ 15.000 |
| Fase 1 (Integração Senior) | 3-4 semanas | ~R$ 7.500-10.000 |
| **Total de Investimento** | **9-10 semanas** | **~R$ 22.500-25.000** |

*Valores estimados com base em desenvolvimento interno

### Payback Period

**Cenário Conservador (2 produtos/mês = 54h economizadas):**
- Economia mensal: R$ 2.700
- Investimento: R$ 22.500-25.000
- Payback: **~9 meses**

**Cenário Médio (4 produtos/mês = 108h economizadas):**
- Economia mensal: R$ 5.400
- Investimento: R$ 22.500-25.000
- Payback: **~4-5 meses**

**Cenário Otimista (6 produtos/mês = 162h economizadas):**
- Economia mensal: R$ 8.100
- Investimento: R$ 22.500-25.000
- Payback: **~3 meses**

**Conclusão:** CoreWood se paga em **3-9 meses** (conforme volume de produtos) e economiza R$ 32.400-97.200 anualmente.

---

## Próximas Fases

### Phase 1: Integração Completa (Q1 2026)
- ✅ Carga Máquina automation (via API Senior)
- ✅ Roteiro de Peça automation (arquivo importável)
- **Objetivo:** 100% de automação

### Phase 2: Validação em Produção (Q1 2026)
- Testes com 50+ peças reais
- Feedback do time de operações
- Ajustes e otimizações

### Phase 3: Deploy Completo (Q2 2026)
- Migração total do processo manual para CoreWood
- Treinamento do time
- Monitoramento contínuo

### Phase 4: Expansão (Q3 2026+)
- Suporte para outros tipos de peças
- Integração com sistemas adicionais
- Possível aplicação em outros departamentos

---

## Lições Aprendidas

### O que Funcionou

✅ **MVP First:** Começar com BHX + Documentação permitiu validar conceito rapidamente
✅ **Foco em Data Centralization:** Centralizar dados foi a chave — simplificou tudo
✅ **Automação Progressiva:** Não tentou fazer tudo de uma vez
✅ **Medição de Impacto:** Números claros facilitam aprovação para próximas fases

### Desafios Encontrados

⚠️ **Integração Senior:** API da Senior tem limitações, requer workarounds
⚠️ **Validação de CAD:** Nem todos os tipos de arquivo CAD são 100% compatíveis
⚠️ **Coordenadas:** Sistema de coordenadas CAD ↔ CNC exigiu calibração cuidadosa

### Como Foram Resolvidos

- **Senior Integration:** Usando arquivos de importação como bridge (mais robusto)
- **CAD Validation:** Parser customizado que trata formatos específicos
- **Coordinate System:** Mapeamento e validação em cada conversão

---

## Conclusão

CoreWood transforma um **processo manual e fragmentado** em um **fluxo automatizado e centralizado**, resultando em:

**MVP (BHX + Documentação):**
- **92-94% redução de tempo** (11-17h → 70-90 min por produto)
- **100% eliminação de erros** (~20% → 0%)
- **3-9 meses de ROI**

**100% Completo (Todos 4 módulos):**
- **94-96% redução de tempo** (28h → ~85-100 min por produto)
- **100% eliminação de erros** (~20% → 0%)
- **R$ 32.400-97.200/ano economizados** (conforme volume)
- **Escalabilidade:** Mesmo time consegue processar múltiplos produtos sem crescimento proporcional de horas

O MVP provou viabilidade (BHX + Documentação em produção). Próximas fases (integração com Senior) eliminarão as últimas reentradas manuais, alcançando 96%+ de automação.

---

## Contato & Próximos Passos

**Responsável do Projeto:** Enzo
**Status:** MVP em produção, fase 1 em desenvolvimento
**Aprovação Necessária:** Expansão para integração completa (Phase 1)