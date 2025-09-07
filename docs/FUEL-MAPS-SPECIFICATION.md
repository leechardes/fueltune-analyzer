# Especificação Técnica - Sistema de Mapas de Injeção FuelTune

## 1. Visão Geral

### 1.1 Objetivo
Implementar um sistema completo de mapas de injeção compatível com FTManager, permitindo configuração, edição e sincronização de mapas de injeção eletrônica para cada veículo cadastrado no sistema FuelTune.

### 1.2 Princípios de Design
- **Compatibilidade Total**: Estrutura de dados idêntica ao FTManager
- **Slots Fixos**: Cada eixo possui quantidade fixa de slots (32 padrão)
- **Interpolação Automática**: Cálculo automático de valores intermediários
- **Versionamento**: Histórico completo de alterações
- **Interface Profissional**: Sem emojis, apenas Material Design Icons

## 2. Arquitetura de Dados

### 2.1 Conceito de Slots Fixos
- Cada tipo de eixo possui **32 slots disponíveis**
- Usuário ativa apenas os slots necessários
- Valores não utilizados permanecem NULL
- Sistema interpola automaticamente entre pontos ativos

### 2.2 Comportamento de Interpolação
```
Regras de Interpolação:
- Entre pontos existentes: Interpolação linear
- Antes do primeiro ponto: Repete primeiro valor
- Após o último ponto: Repete último valor

Exemplo:
Slot 0: 40°C = 40ms
Slot 1: 60°C = 7ms
Adicionar 50°C → Sistema calcula: 24ms (interpolado)
```

## 3. Tipos de Mapas

### 3.1 Mapas Principais

#### 3.1.1 Mapa Principal de Injeção 2D (MAP) - Bancadas A/B
- **Nome**: main_fuel_2d_map_a, main_fuel_2d_map_b
- **Dimensões**: 2D
- **Eixo X**: MAP (Pressão no coletor em bar)
- **Valores (Eixo Y)**: Tempo de injeção (ms)
- **Slots**: 32 posições
- **Bancadas**: Até 2 (A e B) dependendo da configuração do motor
- **Configuração Padrão**:
  ```
  Eixo X - MAP (21 pontos ativos de 32):
  -1.00, -0.90, -0.80, -0.70, -0.60, -0.50, -0.40, -0.30, 
  -0.20, -0.10, 0.00, 0.20, 0.40, 0.60, 0.80, 1.00, 
  1.20, 1.40, 1.60, 1.80, 2.00
  
  Valores Y - Tempo de Injeção (ms) correspondentes:
  5.550, 5.550, 5.550, 5.550, 5.550, 5.913, 6.277, 6.640,
  7.004, 7.367, 7.731, 8.458, 9.185, 9.912, 10.638, 11.365,
  12.092, 12.819, 13.546, 14.273, 15.000
  ```
- **Faixa de valores**: 5.550ms a 15.000ms
- **Visualização**: Gradiente de cores (vermelho=valores baixos, azul=valores altos)
- **Observação**: Motor aspirado usa apenas valores negativos até 0.00, turbo usa toda a faixa

#### 3.1.2 Mapa Principal de Injeção 2D (RPM)
- **Nome**: main_fuel_2d_rpm
- **Dimensões**: 2D
- **Eixo**: RPM
- **Valores**: Tempo de injeção (ms)
- **Slots**: 32 posições
- **Observação**: Compartilhado entre bancadas A e B (apenas um mapa RPM)

#### 3.1.3 Mapa Principal de Injeção 3D (MAP x RPM) - Bancadas A/B
- **Nome**: main_fuel_3d_a, main_fuel_3d_b
- **Dimensões**: 3D
- **Eixo X**: MAP (bar)
- **Eixo Y**: RPM
- **Valores (Z)**: Tempo de injeção (ms) - Matriz 21x24
- **Slots**: 32x32 (21 MAP x 24 RPM ativos)
- **Bancadas**: Até 2 (A e B) dependendo da configuração do motor
- **Configuração Padrão**:
  ```
  Eixo X - MAP (21 pontos):
  -1.00, -0.90, -0.80, -0.70, -0.60, -0.50, -0.40, -0.30,
  -0.20, -0.10, 0.00, 0.20, 0.40, 0.60, 0.80, 1.00,
  1.20, 1.40, 1.60, 1.80, 2.00
  
  Eixo Y - RPM (24 pontos):
  400, 600, 800, 1000, 1200, 1400, 1600, 1800,
  2000, 2200, 2400, 2600, 2800, 3000, 3500, 4000,
  4500, 5000, 5500, 6000, 6500, 7000, 7500, 8000
  
  Valores Z - Matriz de Injeção (ms):
  504 células (21x24) com valores de ~5.550ms a ~16.690ms
  ```
- **Faixa de valores**: 5.550ms a 16.690ms
- **Comportamento**:
  - Baixa carga/RPM: ~5.5ms (células vermelhas)
  - Alta carga/RPM: ~16.7ms (células azuis)
  - Progressão suave através das células
- **Visualização**: Mapa de calor (Vermelho → Laranja → Amarelo → Verde → Azul)
- **Edição**: Por célula individual ou interpolação automática
- **Conversão**: Pode ser gerado automaticamente dos mapas 2D ou editado manualmente
- **Observação**: Tabela principal do sistema, define precisamente o combustível para cada condição operacional

#### 3.1.4 Mapa de Ignição (3D)
- **Nome**: ignition
- **Dimensões**: 3D (RPM x MAP)
- **Eixo X**: RPM (0-20000)
- **Eixo Y**: MAP (-1.0 a 3.0 bar)
- **Valores**: Avanço (graus)
- **Slots**: 32x32

### 3.2 Mapas de Compensação

#### 3.2.1 Compensação por RPM (2D)
- **Nome**: rpm_compensation
- **Dimensões**: 2D
- **Eixo X**: RPM
- **Valores (Y)**: Fator de correção (%)
- **Slots**: 32 posições
- **Configuração Padrão**:
  ```
  Eixo X - RPM (24 pontos ativos de 32):
  400, 600, 800, 1000, 1200, 1400, 1600, 1800, 
  2000, 2200, 2400, 2600, 2800, 3000, 3500, 4000, 
  4500, 5000, 5500, 6000, 6500, 7000, 7500, 8000
  
  Valores Y - Compensação (%) correspondentes:
  0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
  0.0, 0.0, 1.0, 2.0, 3.0, 4.0, 7.0, 11.0,
  12.0, 10.0, 8.0, 5.0, 1.0, -1.0, -3.0, -6.0
  ```
- **Faixa de valores**: -6.0% a +12.0%
- **Comportamento**: 
  - Marcha lenta até 2200 RPM: 0% (sem compensação)
  - Pico em 4500 RPM: +12% (enriquecimento máximo)
  - Alta rotação: Valores negativos (empobrecimento)
- **Visualização**: Verde (zero) → Amarelo (positivo) → Vermelho (negativo)

#### 3.2.2 Compensação por Temperatura do Motor (2D)
- **Nome**: temp_compensation
- **Dimensões**: 2D
- **Eixo X**: Temperatura do Motor (°C)
- **Valores (Y)**: Fator de correção (%)
- **Slots**: 16 posições
- **Configuração Padrão**:
  ```
  Eixo X - Temperatura (14 pontos ativos de 16):
  -10, 0, 10, 20, 30, 40, 50, 60, 
  70, 80, 90, 100, 120, 180
  
  Valores Y - Compensação (%) correspondentes:
  45.0, 42.0, 40.0, 37.0, 34.0, 29.0, 22.0, 15.0,
  7.0, 0.0, 0.0, 0.0, 10.0, 10.0
  ```
- **Faixa de valores**: 0% a +45%
- **Comportamento**:
  - Motor muito frio (-10°C): +45% (máximo enriquecimento)
  - Temperatura normal (80-100°C): 0% (sem compensação)
  - Superaquecimento (120°C+): +10% (proteção térmica)
- **Visualização**: Azul (frio/alta compensação) → Verde (normal) → Vermelho (quente)

#### 3.2.3 Compensação por TPS (2D)
- **Nome**: tps_compensation
- **Dimensões**: 2D
- **Eixo X**: TPS (%)
- **Valores (Y)**: Fator de correção (%)
- **Slots**: 20 posições
- **Configuração Padrão**:
  ```
  Eixo X - TPS (11 pontos ativos de 20):
  0.00, 10.00, 20.00, 30.00, 40.00, 50.00, 
  60.00, 70.00, 80.00, 90.00, 100.00
  
  Valores Y - Compensação (%) correspondentes:
  -5.0, -4.4, -3.8, -3.1, -2.5, -1.9, 
  -1.3, -0.6, 0.0, 0.0, 0.0
  ```
- **Faixa de valores**: -5.0% a 0%
- **Comportamento**:
  - Marcha lenta (0% TPS): -5% (empobrecimento máximo)
  - Carga parcial: Redução gradual do empobrecimento
  - Carga alta (80%+ TPS): 0% (sem compensação)
- **Visualização**: Vermelho (negativo/empobrecido) → Azul (zero)
- **Observação**: Empobrecimento em cargas baixas para economia de combustível

#### 3.2.4 Compensação por Tensão de Bateria (2D) - Bancadas A/B
- **Nome**: battery_voltage_compensation_a, battery_voltage_compensation_b
- **Dimensões**: 2D
- **Eixo X**: Tensão (Volts)
- **Valores (Y)**: Compensação (ms)
- **Slots**: 9 posições
- **Bancadas**: Até 2 (A e B) para compensação individual por bancada
- **Configuração Padrão**:
  ```
  Eixo X - Tensão (9 pontos ativos de 9):
  8.00, 9.00, 10.00, 11.00, 12.00, 13.00, 14.00, 15.00, 16.00
  
  Valores Y - Compensação (ms) correspondentes:
  0.600, 0.500, 0.400, 0.300, 0.180, 0.050, -0.060, -0.150, -0.220
  ```
- **Faixa de valores**: +0.600ms a -0.220ms
- **Comportamento**:
  - Bateria fraca (8V): +0.600ms (máxima compensação positiva)
  - Tensão nominal (12V): +0.180ms (compensação leve)
  - Tensão de carga (14V): -0.060ms (compensação negativa)
  - Sobretensão (16V): -0.220ms (máxima compensação negativa)
- **Visualização**: Azul (baixa tensão/comp. positiva) → Vermelho (alta tensão/comp. negativa)
- **Observação**: Compensa o tempo de resposta dos bicos injetores conforme tensão de alimentação

#### 3.2.5 Compensação por Temperatura do Ar (2D)
- **Nome**: air_temp_compensation
- **Dimensões**: 2D
- **Eixo X**: Temperatura do Ar (°C)
- **Valores (Y)**: Fator de correção (%)
- **Slots**: 16 posições
- **Configuração Padrão**:
  ```
  Eixo X - Temperatura (14 pontos ativos de 16):
  -10, 0, 10, 20, 30, 40, 50, 60,
  70, 80, 90, 100, 120, 180
  
  Valores Y - Compensação (%) correspondentes:
  3.9, 3.8, 3.4, 3.0, 2.5, 2.0, 1.4, 0.8,
  0.0, 0.0, 0.0, 0.0, 0.0, 0.0
  ```
- **Faixa de valores**: 0% a +3.9%
- **Comportamento**:
  - Ar muito frio (-10°C): +3.9% (máxima compensação)
  - Ar ambiente (20°C): +3.0%
  - Ar quente (50°C): +1.4%
  - Ar muito quente (70°C+): 0% (sem compensação)
- **Visualização**: Azul (frio/compensação alta) → Vermelho (quente/sem compensação)
- **Observação**: Ar frio é mais denso (mais O₂), requer mais combustível para manter estequiometria

### 3.3 Mapas de Partida

#### 3.3.1 Primeiro Pulso de Partida (2D)
- **Nome**: first_pulse_cold_start
- **Dimensões**: 2D
- **Eixo X**: Temperatura do Motor (°C)
- **Valores (Y)**: Tempo de injeção (ms)
- **Slots**: 8 posições
- **Configuração Padrão**:
  ```
  Eixo X - Temperatura (8 pontos ativos de 8):
  10, 20, 40, 50, 60, 80, 100, 110
  
  Valores Y - Tempo do Pulso (ms) correspondentes:
  130, 100, 40, 24, 7, 5, 5, 5
  ```
- **Faixa de valores**: 5ms a 130ms
- **Comportamento**:
  - Motor muito frio (10°C): 130ms (máximo combustível)
  - Transição (40-60°C): Redução abrupta de 40ms para 7ms
  - Motor quente (80°C+): 5ms (mínimo constante)
- **Visualização**: Azul (frio/pulso longo) → Vermelho (quente/pulso curto)
- **Observação**: Pulso único disparado antes do motor girar, crítico para partida a frio

#### 3.3.2 Partida do Motor (2D)
- **Nome**: cranking_pulse
- **Dimensões**: 2D
- **Eixo X**: Temperatura do Motor (°C)
- **Valores (Y)**: Tempo de injeção (ms)
- **Slots**: 8 posições
- **Configuração Padrão**:
  ```
  Eixo X - Temperatura (8 pontos ativos de 8):
  -10, 0, 10, 20, 40, 60, 80, 100
  
  Valores Y - Tempo de Injeção (ms) correspondentes:
  24.00, 24.00, 21.00, 18.00, 15.00, 9.00, 6.00, 6.00
  ```
- **Faixa de valores**: 6ms a 24ms
- **Comportamento**:
  - Motor congelado (-10°C a 0°C): 24ms (máximo constante)
  - Transição gradual (10°C a 40°C): 21ms → 15ms
  - Redução abrupta (60°C): 9ms
  - Motor quente (80°C+): 6ms (mínimo constante)
- **Visualização**: Azul (frio/tempo longo) → Vermelho (quente/tempo curto)
- **Observação**: Pulsos contínuos durante cranking até o motor pegar

#### 3.3.3 Enriquecimento Após a Partida - 3D
- **Nome**: after_start_enrichment
- **Dimensões**: 3D (Tempo x Temperatura) - SOMENTE 3D
- **Eixo X**: Tempo após partida (segundos)
- **Eixo Y**: Temperatura do Motor (°C)
- **Valores (Z)**: Enriquecimento (%)
- **Slots**: 4x4 (todos ativos)
- **Configuração Padrão**:
  ```
  Eixo X - Tempo (4 pontos):
  0, 1, 3, 8 segundos
  
  Eixo Y - Temperatura (4 pontos):
  10, 30, 50, 80 °C
  
  Valores Z - Matriz de Enriquecimento (%):
  
  Temp\Tempo   0s     1s     3s     8s
  80°C       10.0    6.0    2.5    0.0
  50°C       20.0    9.0    7.0    0.5
  30°C       30.0   20.0   11.0    2.0
  10°C       70.0   45.0   16.7    4.0
  ```
- **Faixa de valores**: 0% a 70%
- **Comportamento**:
  - Motor frio (10°C) no início (0s): +70% (máximo enriquecimento)
  - Motor quente (80°C) após 8s: 0% (sem enriquecimento)
  - Decaimento progressivo com o tempo
  - Mais enriquecimento quanto mais frio o motor
- **Visualização**: Azul (alto enriquecimento) → Verde → Amarelo → Vermelho (baixo/zero)
- **Observação**: 
  - Este mapa existe APENAS em 3D (não há versão 2D)
  - Crítico para estabilização pós-partida
  - Garante funcionamento suave em motores frios
  - Mapa compacto 4x4 mas muito efetivo

#### 3.3.4 Tempo de Decaimento Pós-Partida (2D)
- **Nome**: after_start_decay_time
- **Dimensões**: 2D
- **Eixo X**: Temperatura do Motor (°C)
- **Valores**: Tempo (segundos)
- **Slots**: 32
- **Observação**: Define quanto tempo o enriquecimento pós-partida permanece ativo

### 3.4 Mapas de Malha Fechada

#### 3.4.1 Mapa de Alvos de Malha Fechada (Lambda) - 3D
- **Nome**: target_lambda
- **Dimensões**: 3D (MAP x RPM) - SOMENTE 3D
- **Eixo X**: MAP (bar)
- **Eixo Y**: RPM
- **Valores (Z)**: Lambda alvo (λ)
- **Slots**: 16x16 (5 MAP x 5 RPM ativos)
- **Configuração Padrão**:
  ```
  Eixo X - MAP (5 pontos ativos de 16):
  -1.00, 0.00, 0.60, 1.00, 6.00
  
  Eixo Y - RPM (5 pontos ativos de 16):
  1000, 3000, 5000, 7000, 9000
  
  Valores Z - Matriz Lambda (λ):
  Exemplo de valores (5x5 = 25 células):
  
  MAP\RPM  1000   3000   5000   7000   9000
  -1.00    0.900  0.870  0.860  0.860  0.860
   0.00    0.850  0.840  0.840  0.840  0.840
   0.60    0.800  0.790  0.790  0.790  0.790
   1.00    0.790  0.770  0.760  0.760  0.760
   6.00    0.790  0.770  0.760  0.760  0.760
  ```
- **Faixa de valores**: 0.760 a 0.900 (sempre < 1.0 para proteção)
- **Comportamento**:
  - Baixa carga (-1.00 bar): λ ~0.86-0.90 (levemente rico)
  - Carga média (0.00-0.60 bar): λ ~0.79-0.84 (próximo estequiométrico)
  - Alta carga (1.00+ bar): λ ~0.76-0.79 (rico para proteção)
- **Visualização**: Azul (lambda alto/menos rico) → Vermelho (lambda baixo/mais rico)
- **Observação**: 
  - Este mapa existe APENAS em 3D (não há versão 2D)
  - Usado pela sonda lambda para correção automática
  - Lambda = 1.00 seria estequiométrico (14.7:1 para gasolina)
  - Valores < 1.00 indicam mistura rica (proteção do motor)

## 4. Estrutura de Banco de Dados

### 4.1 Importante: Nomenclatura dos Eixos
**ESCLARECIMENTO IMPORTANTE**:
- **Mapas 2D**: 
  - **Eixo X** = Eixo de entrada (MAP, RPM, Temperatura, TPS, etc.)
  - **Valores Y** = Valores de saída (tempo injeção, correção, etc.)
  - Não há "Eixo Y" propriamente dito, são os valores resultantes
  
- **Mapas 3D**: 
  - **Eixo X** = Primeiro eixo (ex: RPM)
  - **Eixo Y** = Segundo eixo (ex: MAP)
  - **Valores Z** = Matriz de valores resultantes

### 4.2 Configuração de Injeção no Modelo Vehicle
```sql
-- Adicionar ao modelo Vehicle
ALTER TABLE vehicles ADD COLUMN bank_a_enabled BOOLEAN DEFAULT TRUE;
ALTER TABLE vehicles ADD COLUMN bank_a_mode VARCHAR(20) DEFAULT 'semissequential';
ALTER TABLE vehicles ADD COLUMN bank_a_outputs JSON; -- [2, 4] etc
ALTER TABLE vehicles ADD COLUMN bank_a_injector_flow FLOAT; -- lb/h por bico
ALTER TABLE vehicles ADD COLUMN bank_a_injector_count INTEGER;
ALTER TABLE vehicles ADD COLUMN bank_a_total_flow FLOAT; -- calculado
ALTER TABLE vehicles ADD COLUMN bank_a_dead_time FLOAT; -- ms

ALTER TABLE vehicles ADD COLUMN bank_b_enabled BOOLEAN DEFAULT FALSE;
ALTER TABLE vehicles ADD COLUMN bank_b_mode VARCHAR(20) DEFAULT 'semissequential';
ALTER TABLE vehicles ADD COLUMN bank_b_outputs JSON; -- [2, 4] etc
ALTER TABLE vehicles ADD COLUMN bank_b_injector_flow FLOAT; -- lb/h por bico
ALTER TABLE vehicles ADD COLUMN bank_b_injector_count INTEGER;
ALTER TABLE vehicles ADD COLUMN bank_b_total_flow FLOAT; -- calculado
ALTER TABLE vehicles ADD COLUMN bank_b_dead_time FLOAT; -- ms
```

### 4.3 Tabela Principal de Mapas
```sql
CREATE TABLE fuel_maps (
    id INTEGER PRIMARY KEY,
    vehicle_id INTEGER REFERENCES vehicles(id),
    map_type VARCHAR(50),  -- 'main_fuel', 'ignition', etc
    bank_id VARCHAR(1),     -- 'A', 'B' ou NULL para mapas sem bancada
    name VARCHAR(100),
    description TEXT,
    dimensions INTEGER,     -- 1 para 2D, 2 para 3D
    x_axis_type VARCHAR(50), -- 'RPM', 'MAP', 'TEMP'
    y_axis_type VARCHAR(50), -- NULL para 2D (apenas mapas 3D)
    data_unit VARCHAR(20),   -- 'ms', '%', 'degrees', 'lambda'
    version INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP,
    modified_at TIMESTAMP,
    
    -- Constraint única para evitar duplicatas
    UNIQUE(vehicle_id, map_type, bank_id)
);
```

### 4.3 Tabelas de Eixos

#### 4.3.1 Eixo RPM
```sql
CREATE TABLE axis_rpm (
    id INTEGER PRIMARY KEY,
    map_id INTEGER REFERENCES fuel_maps(id),
    slot_0 FLOAT, slot_1 FLOAT, ..., slot_31 FLOAT,
    active_slots INTEGER
);
```

#### 4.3.2 Eixo MAP
```sql
CREATE TABLE axis_map (
    id INTEGER PRIMARY KEY,
    map_id INTEGER REFERENCES fuel_maps(id),
    slot_0 FLOAT, slot_1 FLOAT, ..., slot_31 FLOAT,
    active_slots INTEGER
);
```

#### 4.3.3 Eixo Temperatura
```sql
CREATE TABLE axis_temperature (
    id INTEGER PRIMARY KEY,
    map_id INTEGER REFERENCES fuel_maps(id),
    slot_0 FLOAT, slot_1 FLOAT, ..., slot_31 FLOAT,
    active_slots INTEGER
);
```

### 4.4 Tabelas de Dados

#### 4.4.1 Dados 2D
```sql
CREATE TABLE map_data_2d (
    id INTEGER PRIMARY KEY,
    map_id INTEGER REFERENCES fuel_maps(id),
    value_0 FLOAT, value_1 FLOAT, ..., value_31 FLOAT
);
```

#### 4.4.2 Dados 3D
```sql
CREATE TABLE map_data_3d (
    id INTEGER PRIMARY KEY,
    map_id INTEGER REFERENCES fuel_maps(id),
    -- Matriz 32x32 = 1024 campos
    value_0_0 FLOAT, value_0_1 FLOAT, ..., value_31_31 FLOAT
);
```

## 5. Interface de Usuário

### 5.1 Página Principal de Mapas
- Lista de mapas do veículo selecionado
- Botões para criar, editar, copiar, importar/exportar
- Indicadores de versão e última modificação

### 5.2 Editor de Mapas
- **Visualização 2D**: Gráfico de linha com pontos editáveis
- **Visualização 3D**: Superfície 3D interativa (Plotly)
- **Grid Editor**: Tabela estilo Excel para edição direta
- **Editor de Eixos**: Modal para configurar slots dos eixos

### 5.3 Ferramentas de Edição
- **Interpolação**: Preencher valores intermediários
- **Suavização**: Aplicar filtro de suavização
- **Copiar/Colar**: Regiões ou mapas completos
- **Comparação**: Visualizar diferenças entre versões

## 6. Funcionalidades Avançadas

### 6.1 Importação/Exportação
- **Formato FTManager**: .ftm (compatibilidade total)
- **CSV**: Exportar/importar tabelas
- **JSON**: Backup completo estruturado

### 6.2 Versionamento
- Salvar snapshots antes de alterações
- Comparar versões lado a lado
- Rollback para versão anterior
- Histórico de alterações com timestamps

### 6.3 Templates
- Mapas base por tipo de motor
- Templates por combustível (gasolina, etanol, flex)
- Configurações para turbo/aspirado

## 7. Validações e Limites

### 7.1 Limites por Tipo de Eixo
- **RPM**: 0 a RPM máximo do veículo
- **MAP**: -1.0 a 5.0 bar (configurável)
- **Temperatura**: -40 a 150°C
- **Lambda**: 0.6 a 1.5

### 7.2 Validações de Dados
- Valores dos eixos em ordem crescente
- Mínimo 2 pontos ativos por eixo
- Máximo 32 pontos por eixo
- Valores dentro dos limites físicos

## 8. Integração com Sistema Existente

### 8.1 Vínculo com Veículo
- Cada mapa pertence a um veículo específico
- Herança de limites do veículo (RPM máximo, etc)
- Possibilidade de copiar mapas entre veículos

### 8.2 Análise de Dados
- Overlay de dados reais sobre mapas
- Sugestões de ajuste baseadas em telemetria
- Identificação de regiões não utilizadas

## 9. Relação entre Mapas 2D e 3D

### 9.1 Conceito de Conversão
- **Mapas 2D**: Armazenam dados unidimensionais (1 eixo de entrada)
- **Mapas 3D**: Combinam dois mapas 2D ou permitem edição célula por célula
- **Armazenamento**: Tabelas separadas (map_data_2d vs map_data_3d)
- **Conversão Automática**: Sistema pode gerar 3D a partir de 2D usando interpolação

### 9.2 Exemplo Prático
```
Mapa 2D MAP: 21 pontos → 21 valores
Mapa 2D RPM: 24 pontos → 24 valores
Mapa 3D MAP x RPM: 21 x 24 = 504 células

Conversão 2D → 3D:
Para cada célula (map[i], rpm[j]):
  valor_3d[i][j] = valor_2d_map[i] * fator_rpm[j]
```

### 9.3 Edição
- **2D**: Edita-se a curva completa
- **3D**: Edita-se célula por célula ou região
- **Sincronização**: Alterações no 3D podem atualizar os 2D base

## 10. Configuração de Bancadas

### 10.1 Configuração das Bancadas de Injeção

#### Parâmetros por Bancada (A e B):
```
Bancada A:
- Ativada: Sim/Não (padrão: Sim)
- Modo: Multiponto / Semissequencial / Sequencial
- Saídas: [1, 2, 3, 4, 5, 6, 7, 8] (seleção múltipla)
- Vazão por bico: XX lb/h
- Quantidade de bicos: N
- Vazão total: Calculada (vazão_por_bico * quantidade_bicos)
- Dead time: Compensação em ms

Bancada B:
- Ativada: Sim/Não (padrão: Não)
- Modo: Multiponto / Semissequencial / Sequencial
- Saídas: [1, 2, 3, 4, 5, 6, 7, 8] (seleção múltipla)
- Vazão por bico: XX lb/h
- Quantidade de bicos: N
- Vazão total: Calculada (vazão_por_bico * quantidade_bicos)
- Dead time: Compensação em ms
```

#### Modos de Injeção:
- **Multiponto**: Todos os bicos injetam simultaneamente
- **Semissequencial**: Pares de bicos injetam juntos
- **Sequencial**: Cada bico injeta individualmente sincronizado

#### Cálculo de Vazão:
```
Vazão Total = Vazão por Bico × Quantidade de Bicos
Exemplo: 4 bicos de 80 lb/h = 320 lb/h total
```

### 10.2 Mapas com Suporte a Bancadas A/B

#### Mapas Duplicados (A e B):
- **Mapa Principal de Injeção 2D (MAP)**: Bancada A e B separadas
- **Mapa Principal de Injeção 3D (MAP x RPM)**: Bancada A e B separadas
- **Compensação por Tensão de Bateria**: Bancada A e B separadas
- **Dead Time dos Injetores**: Bancada A e B separadas

#### Mapa Compartilhado:
- **Mapa Principal de Injeção 2D (RPM)**: Único para ambas as bancadas

### 10.3 Uso Típico das Bancadas

#### Por Tipo de Motor:
- **Motor 4 cilindros**: Geralmente usa apenas Bancada A
- **Motor 6-8 cilindros**: Pode usar Bancadas A e B
- **Motor com turbo grande**: Bancada A principal, B auxiliar

#### Por Tipo de Sistema:
- **Injeção sequencial**: Bancadas separadas para pares de cilindros
- **Bi-combustível**: Bancada A para gasolina, B para etanol
- **Staged injection**: Bancada A primária, B secundária em alta carga

## 11. Resumo de Tamanhos de Slots

### 11.1 Mapas 2D
- **32 slots**: MAP, RPM (principais), Decaimento Pós-Partida
- **20 slots**: TPS
- **16 slots**: Temperatura Motor, Temperatura do Ar
- **9 slots**: Tensão de Bateria
- **8 slots**: Primeiro Pulso, Partida Motor

### 11.2 Mapas 3D
- **32x32 slots**: Mapa Principal Injeção (21x24 ativos), Ignição
- **16x16 slots**: Target Lambda (5x5 ativos)
- **4x4 slots**: Enriquecimento Após Partida (todos ativos)

### 11.3 Mapas Exclusivamente 3D
- Target Lambda (Malha Fechada)
- Enriquecimento Após Partida

## 12. Plano de Implementação

### Fase 1: Estrutura Base
- [ ] Criar modelos de banco de dados com slots variáveis (8, 16, 20, 32)
- [ ] Implementar tabelas separadas por tipo de eixo
- [ ] Criar sistema de interpolação linear

### Fase 2: Interface Básica 2D
- [ ] Editor de mapas 2D com gráfico de linha
- [ ] Editor de eixos com tabela de slots
- [ ] Sistema de versionamento básico

### Fase 3: Interface 3D
- [ ] Grid editor estilo planilha
- [ ] Visualização 3D com Plotly
- [ ] Conversão 2D ↔ 3D
- [ ] Edição por célula ou região

### Fase 4: Integração FTManager
- [ ] Parser de formato .ftm
- [ ] Importação/Exportação
- [ ] Sincronização bidirecional

## 13. Considerações Técnicas

### 13.1 Performance
- Índices nas tabelas de mapas por vehicle_id
- Cache de mapas ativos em memória
- Lazy loading para grids grandes

### 13.2 Segurança
- Validação de limites antes de salvar
- Backup automático antes de alterações
- Confirmação para alterações críticas

### 13.3 Compatibilidade
- Estrutura idêntica ao FTManager
- Preservar formato de importação/exportação
- Suporte a diferentes versões de firmware

---

## Notas de Implementação

**AGUARDANDO INFORMAÇÕES ADICIONAIS**:
- Configurações específicas de cada tipo de mapa
- Limites e ranges padrão
- Formato exato do arquivo .ftm
- Outros tipos de mapas necessários

Este documento será atualizado conforme novas informações forem fornecidas.

---

*Documento em construção - Versão 1.0*