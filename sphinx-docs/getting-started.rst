===============
Início Rápido
===============

Este guia vai te levar do zero ao primeiro resultado em menos de 10 minutos! 
Você aprenderá o essencial para começar a analisar dados FuelTech imediatamente.

.. note::
   **Pré-requisito**: FuelTune Analyzer já instalado. 
   Se ainda não instalou, siga o :doc:`installation`.

🚀 Primeiro Uso (5 minutos)
============================

Passo 1: Iniciar a Aplicação
-----------------------------

.. code-block:: bash

   # Navegar até o diretório
   cd fueltune-analyzer
   
   # Ativar ambiente virtual
   source venv/bin/activate  # Linux/macOS
   # venv\Scripts\activate   # Windows
   
   # Executar aplicação
   streamlit run app.py

Sua aplicação estará disponível em: http://localhost:8501

Passo 2: Upload do Primeiro Arquivo
------------------------------------

1. **Abra o navegador** em http://localhost:8501
2. **Na sidebar esquerda**, clique em "📁 Upload de Dados"
3. **Arraste seu arquivo CSV** FuelTech ou clique em "Browse files"
4. **Aguarde o processamento** (barra de progresso será exibida)

.. tip::
   **Não tem um arquivo FuelTech?** Baixe nosso arquivo de exemplo:
   
   .. code-block:: bash
   
      # Baixar dados de exemplo
      curl -o exemplo_fueltech.csv https://github.com/fueltune/sample-data/raw/main/civic_si_dyno.csv

Passo 3: Visualizar Resultados Instantâneos
--------------------------------------------

Assim que o upload for concluído, você verá:

.. raw:: html

   <div class="feature-grid">
      <div class="feature-card">
         <h3>📊 Dashboard Principal</h3>
         <p>Métricas principais, gráficos em tempo real e resumo da sessão automaticamente carregados.</p>
      </div>
      <div class="feature-card">
         <h3>⚡ Análise Automática</h3>
         <p>Performance, estatísticas básicas e detecção de anomalias executadas automaticamente.</p>
      </div>
      <div class="feature-card">
         <h3>📈 Gráficos Interativos</h3>
         <p>Zoom, pan, seleção e tooltips interativos em todos os gráficos Plotly.</p>
      </div>
   </div>

🎯 Interface Rápida (2 minutos)
===============================

A interface está organizada em seções principais:

**Sidebar (Esquerda)**
   - 📁 **Upload**: Carregar novos arquivos
   - ⚙️ **Configurações**: Ajustes básicos
   - 🎨 **Visualização**: Opções de gráficos
   - 📊 **Análises**: Tipos de análise

**Área Principal (Centro)**
   - 🏠 **Dashboard**: Visão geral e métricas
   - 📈 **Performance**: Potência, torque, aceleração
   - ⛽ **Consumo**: Eficiência e combustível
   - 📊 **Análise**: Estatísticas detalhadas
   - 📄 **Relatórios**: Exportação e documentos

**Barra Superior**
   - 🔄 **Atualizar**: Recarregar dados
   - ⚙️ **Configurações**: Preferências globais
   - ❓ **Ajuda**: Links úteis

.. mermaid::

   graph TD
       UPLOAD[📁 Upload] --> PROCESS[Processamento Automático]
       PROCESS --> DASHBOARD[🏠 Dashboard]
       PROCESS --> PERF[📈 Performance]
       PROCESS --> FUEL[⛽ Consumo]
       PROCESS --> ANALYSIS[📊 Análise]
       PROCESS --> REPORTS[📄 Relatórios]

📊 Dashboard - Visão Geral
===========================

O Dashboard mostra automaticamente:

Métricas Principais
-------------------

.. list-table::
   :widths: 30 70
   :header-rows: 1

   * - Métrica
     - Descrição
   * - **Potência Máxima**
     - Pico de potência detectado (HP/CV/kW)
   * - **Torque Máximo**
     - Pico de torque detectado (Nm/lb-ft)
   * - **RPM Máximo**
     - Maior rotação registrada
   * - **Tempo de Sessão**
     - Duração total da sessão
   * - **Pontos de Dados**
     - Quantidade de amostras válidas
   * - **Qualidade dos Dados**
     - Percentual de dados válidos

Gráficos Padrão
---------------

**Gráfico 1: RPM vs Tempo**
   Mostra a evolução da rotação durante toda a sessão

**Gráfico 2: Potência vs RPM** 
   Curva de potência clássica para análise de performance

**Gráfico 3: Parâmetros Principais**
   Múltiplas variáveis (MAP, Lambda, Temperatura) em um só gráfico

**Gráfico 4: Mapa de Calor**
   Visualização de correlações entre parâmetros

⚡ Análise de Performance
========================

Acesse: **Menu lateral** → **📈 Performance**

**O que você verá:**

1. **Curvas de Potência e Torque**
   - Gráfico interativo com ambas as curvas
   - Valores máximos destacados
   - Faixas de RPM otimizadas

2. **Métricas de Aceleração**
   - Tempos 0-100 km/h (se dados disponíveis)
   - Análise de resposta do acelerador
   - Comparações com valores de referência

3. **Eficiência Volumétrica**
   - Cálculos baseados em MAP e RPM
   - Identificação de faixas otimizadas
   - Sugestões de melhoria

**Exemplo de Interpretação:**

.. code-block:: text

   ✅ RESULTADOS TÍPICOS:
   
   Potência Máxima: 187.3 HP @ 6.850 RPM
   Torque Máximo: 196.8 Nm @ 4.200 RPM
   
   📊 ANÁLISE:
   - Pico de potência adequado para motor aspirado
   - Torque concentrado em médias rotações
   - Curva característica de motor VTEC

⛽ Análise de Consumo
====================

Acesse: **Menu lateral** → **⛽ Consumo**

**Informações disponíveis:**

1. **Consumo Instantâneo**
   - L/100km em tempo real
   - Variação por faixa de RPM
   - Condições de maior/menor consumo

2. **Eficiência por Load**
   - BSFC (Brake Specific Fuel Consumption)
   - Mapa de eficiência RPM vs Load
   - Pontos ótimos de operação

3. **Análise Lambda**
   - Mistura ar/combustível
   - Detecção de condições lean/rich
   - Alertas de segurança

.. warning::
   **Atenção às condições lean (Lambda > 1.05):**
   
   - Risco de detonação
   - Possível dano ao motor
   - Verificar calibração da injeção

🔧 Configurações Básicas
========================

Acesse: **⚙️ Configurações** (sidebar)

**Configurações Essenciais:**

.. code-block:: yaml

   # Unidades de Medida
   potencia: HP          # HP, CV, kW
   torque: Nm            # Nm, lb-ft
   temperatura: Celsius  # Celsius, Fahrenheit
   velocidade: km/h      # km/h, mph
   
   # Análise
   auto_analysis: true   # Análise automática no upload
   cache_results: true   # Cache para melhor performance
   
   # Visualização
   theme: light          # light, dark
   language: pt_BR       # pt_BR, en_US

**Configurações de Veículo:**

.. list-table::
   :widths: 30 70
   :header-rows: 1

   * - Campo
     - Exemplo
   * - **Nome do Veículo**
     - "Civic Si 2020"
   * - **Peso (kg)**
     - "1.250"
   * - **Tipo de Combustível**
     - "Gasolina Aditivada"
   * - **Configuração do Motor**
     - "K20A - Aspirado"

📈 Explorando Gráficos Interativos
===================================

**Recursos disponíveis em todos os gráficos:**

🔍 **Zoom e Pan**
   - Clique e arraste para selecionar área
   - Duplo clique para voltar ao zoom original
   - Roda do mouse para zoom rápido

🎯 **Tooltips Informativos**
   - Passe o mouse sobre qualquer ponto
   - Informações detalhadas em tempo real
   - Coordenadas precisas

📊 **Legendas Interativas**
   - Clique na legenda para ocultar/mostrar séries
   - Duplo clique para isolar uma série
   - Controle de transparência

💾 **Exportação**
   - Botão câmera para salvar PNG
   - Menu para salvar SVG, PDF, HTML
   - Dados exportáveis em CSV/Excel

**Exemplo de Uso dos Gráficos:**

.. code-block:: text

   🎯 DICA PRÁTICA:
   
   1. No gráfico "Potência vs RPM":
      - Zoom na faixa 5.000-7.000 RPM
      - Identifique o pico de potência exato
      - Compare com curvas de referência
   
   2. No gráfico "MAP vs Tempo":
      - Procure por picos de pressão
      - Identifique momentos de WOT (Wide Open Throttle)
      - Analise resposta do turbo (se aplicável)

📄 Exportação de Resultados
============================

Acesse: **📄 Relatórios** (menu lateral)

**Opções de Exportação:**

1. **Relatório PDF Executivo**
   - Sumário das principais métricas
   - Gráficos principais incluídos
   - Ideal para apresentações

2. **Relatório Técnico Completo**
   - Todas as análises detalhadas
   - Dados estatísticos completos
   - Metodologia e interpretações

3. **Dados Brutos (Excel/CSV)**
   - Dados processados e validados
   - Colunas padronizadas
   - Metadados incluídos

4. **Gráficos Individuais**
   - PNG alta resolução
   - SVG vetorial
   - Configurações customizáveis

.. code-block:: python

   # Exemplo de exportação programática
   from src.integration.export_import import ExportManager
   
   exporter = ExportManager()
   
   # Exportar relatório completo
   exporter.export_full_report(
       data=session_data,
       format='pdf',
       include_charts=True,
       output_path='relatorio_civic_si.pdf'
   )

🚨 Alertas e Diagnósticos
=========================

O sistema monitora automaticamente:

**Alertas de Segurança:**

.. list-table::
   :widths: 20 30 50
   :header-rows: 1

   * - Tipo
     - Condição
     - Ação Recomendada
   * - 🔥 **Superaquecimento**
     - Temp > 105°C
     - Parar imediatamente
   * - ⚡ **Knock/Detonação**
     - Detecção de batida
     - Reduzir timing/boost
   * - 💨 **Mistura Lean**
     - Lambda > 1.1
     - Verificar injeção
   * - 📈 **RPM Excessivo**
     - RPM > limite
     - Verificar limitador

**Alertas de Qualidade:**

- **Dados Inconsistentes**: Gaps ou valores impossíveis
- **Baixa Resolução**: Poucos pontos por segundo
- **Ruído Excessivo**: Sinais muito irregulares
- **Calibração**: Valores fora dos padrões FuelTech

⚠️ Problemas Comuns e Soluções
==============================

**"Arquivo não é reconhecido como FuelTech"**
   ✅ Verifique se é um CSV exportado diretamente da FuelTech
   ✅ Headers devem estar em português ou inglês
   ✅ Primeira linha deve conter os nomes dos parâmetros

**"Análise falhou - dados insuficientes"**
   ✅ Mínimo de 100 pontos de dados necessários
   ✅ Pelo menos TIME, RPM e MAP devem estar presentes
   ✅ Verificar se dados não estão todos zerados

**"Gráficos não carregam"**
   ✅ Aguardar processamento completo (barra de progresso)
   ✅ Atualizar página (Ctrl+R / Cmd+R)
   ✅ Verificar se JavaScript está habilitado

**"Performance lenta"**
   ✅ Arquivos grandes (>50MB) demoram mais
   ✅ Ativar cache nas configurações
   ✅ Fechar abas desnecessárias do navegador

🎓 Próximos Passos
==================

Agora que você domina o básico:

1. **📖 Leia o** :doc:`usage` **para recursos avançados**
2. **🧪 Experimente** :doc:`../tutorials/analysis-workflow` **para workflows completos**
3. **⚙️ Configure** :doc:`configuration` **para otimizar sua experiência**
4. **🤝 Junte-se à** `comunidade no Discord <https://discord.gg/fueltune>`_

**Dicas de Aprofundamento:**

.. raw:: html

   <div class="feature-grid">
      <div class="feature-card">
         <h3>📈 Análises Avançadas</h3>
         <p>Correlações, análises preditivas, detecção de anomalias e modelos personalizados.</p>
      </div>
      <div class="feature-card">
         <h3>🔧 Customização</h3>
         <p>Temas personalizados, dashboards customizados e integrações com outros softwares.</p>
      </div>
      <div class="feature-card">
         <h3>🏆 Comparações</h3>
         <p>Compare múltiplas sessões, benchmarks da indústria e evolução temporal.</p>
      </div>
   </div>

📚 Recursos de Aprendizado
===========================

**Documentação:**
   - :doc:`../api/index` - Referência completa da API
   - :doc:`../tutorials/index` - Tutoriais passo-a-passo
   - :doc:`../dev-guide/index` - Para desenvolvedores

**Comunidade:**
   - 💬 `Discord Server <https://discord.gg/fueltune>`_ - Chat em tempo real
   - 📺 `Canal YouTube <https://youtube.com/fueltune>`_ - Vídeo tutoriais
   - 📰 `Blog <https://blog.fueltune.com>`_ - Artigos técnicos

**Exemplos Práticos:**
   - 🏁 Análise de Drag Race
   - 🏎️ Setup de Circuito
   - 🔧 Diagnóstico de Problemas
   - 📊 Comparação de Combustíveis

.. tip::
   **💡 Dica Final**: Mantenha sempre backups de seus arquivos importantes 
   e experimente diferentes configurações para encontrar o setup ideal 
   para suas necessidades!

----

**Parabéns!** 🎉 Você agora sabe o essencial para usar o FuelTune Analyzer. 
Continue explorando para descobrir todo o potencial da ferramenta!

**Tempo investido**: ~10 minutos  
**Nível alcançado**: Usuário Básico ⭐  
**Próximo nível**: :doc:`usage` (Usuário Avançado ⭐⭐)