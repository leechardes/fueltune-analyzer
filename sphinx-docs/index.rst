==========================================
FuelTune Analyzer - Documentação Oficial
==========================================

.. raw:: html

   <div class="version-badges">
      <img alt="Python Version" src="https://img.shields.io/badge/python-3.11+-blue.svg">
      <img alt="Streamlit" src="https://img.shields.io/badge/streamlit-1.29+-red.svg">
      <img alt="License" src="https://img.shields.io/badge/license-MIT-green.svg">
      <img alt="Build Status" src="https://img.shields.io/badge/build-passing-brightgreen.svg">
      <img alt="Coverage" src="https://img.shields.io/badge/coverage-90%25-green.svg">
   </div>

O **FuelTune Analyzer** é uma plataforma profissional de análise de dados de telemetria automotiva, 
especificamente projetada para processar dados de ECUs FuelTech. Esta aplicação oferece análises 
avançadas de performance, consumo, eficiência e diagnósticos para profissionais da área automotiva, 
operadores de dinamômetro, equipes de corrida e preparadores de motores.

.. note::
   Esta é a versão 2.0 do FuelTune Analyzer, completamente reescrita em Python/Streamlit para 
   melhor performance, facilidade de uso e extensibilidade.

🚀 Características Principais
=============================

.. raw:: html

   <div class="feature-grid">
      <div class="feature-card">
         <h3>📊 Análise Avançada</h3>
         <p>Mais de 9 módulos de análise especializados incluindo performance, consumo, correlações, detecção de anomalias e análises preditivas.</p>
      </div>
      <div class="feature-card">
         <h3>⚡ Alta Performance</h3>
         <p>Processamento otimizado para arquivos com mais de 10.000 linhas por segundo, com uso eficiente de memória através de chunked processing.</p>
      </div>
      <div class="feature-card">
         <h3>📈 Visualizações Interativas</h3>
         <p>Gráficos interativos Plotly com zoom, pan, seleção e exportação. Interface responsiva que funciona em desktop e tablet.</p>
      </div>
      <div class="feature-card">
         <h3>🔧 Suporte Completo FuelTech</h3>
         <p>Compatibilidade com todos os 37+ parâmetros de telemetria FuelTech, incluindo tradução automática de campos em português.</p>
      </div>
      <div class="feature-card">
         <h3>✅ Validação de Dados</h3>
         <p>Sistema robusto de validação com Pandera, detecção de outliers e verificação de limites de segurança automática.</p>
      </div>
      <div class="feature-card">
         <h3>🔗 Integração Completa</h3>
         <p>Pipeline de workflow completo com exportação, importação, notificações e sistema de plugins extensível.</p>
      </div>
   </div>

🎯 Para Quem é Este Sistema
===========================

**Profissionais Automotivos**
   - Preparadores de motores
   - Operadores de dinamômetro
   - Engenheiros de performance
   - Técnicos especializados

**Equipes de Corrida**
   - Análise de telemetria em tempo real
   - Otimização de setup
   - Monitoramento de performance
   - Relatórios técnicos

**Desenvolvedores**
   - API completa e documentada
   - Sistema de plugins
   - Arquitetura extensível
   - Código aberto (MIT)

📚 Navegação da Documentação
============================

.. toctree::
   :maxdepth: 2
   :caption: Guia do Usuário
   
   user-guide/installation
   user-guide/getting-started
   user-guide/configuration
   user-guide/usage
   user-guide/advanced

.. toctree::
   :maxdepth: 2
   :caption: Tutoriais Práticos
   
   tutorials/data-import
   tutorials/analysis-workflow
   tutorials/custom-analysis
   tutorials/export-results

.. toctree::
   :maxdepth: 3
   :caption: Referência da API
   
   api/index
   
.. toctree::
   :maxdepth: 2
   :caption: Guia do Desenvolvedor
   
   dev-guide/architecture
   dev-guide/contributing
   dev-guide/testing
   dev-guide/deployment
   dev-guide/api-reference

⚡ Início Rápido
===============

.. code-block:: bash

   # Clone o repositório
   git clone https://github.com/fueltune/analyzer-streamlit.git
   cd analyzer-streamlit

   # Configure o ambiente Python
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # venv\Scripts\activate  # Windows

   # Instale as dependências
   pip install -r requirements.txt

   # Execute a aplicação
   streamlit run app.py

.. tip::
   Para uma experiência completa, consulte o :doc:`user-guide/installation` que inclui 
   configuração do ambiente, dependências opcionais e troubleshooting.

🛠️ Stack Tecnológico
====================

.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - Componente
     - Tecnologia
   * - **Framework Web**
     - Streamlit 1.29+ (Interface moderna e responsiva)
   * - **Processamento de Dados**
     - Pandas 2.0+, NumPy 1.24+, SciPy 1.11+
   * - **Visualização**
     - Plotly 5.18+, Matplotlib 3.7+, Seaborn 0.12+
   * - **Validação**
     - Pandera 0.17+ (Validação robusta de dados)
   * - **Banco de Dados**
     - SQLAlchemy 2.0+ (ORM moderno com suporte async)
   * - **Machine Learning**
     - scikit-learn 1.3+ (Análises preditivas)
   * - **Qualidade**
     - Pytest, MyPy, Black, Pylint, Coverage 90%+

🏗️ Arquitetura do Sistema
=========================

.. mermaid::

   graph TD
       UI[Interface Streamlit] --> APP[Aplicação Principal]
       APP --> DATA[Camada de Dados]
       APP --> ANALYSIS[Módulos de Análise]
       APP --> INTEGRATION[Sistema de Integração]
       
       DATA --> PARSER[Parser CSV]
       DATA --> VALIDATOR[Validadores]
       DATA --> MODELS[Modelos de Dados]
       DATA --> DB[Banco de Dados]
       
       ANALYSIS --> PERF[Performance]
       ANALYSIS --> CONSUMPTION[Consumo]
       ANALYSIS --> STATS[Estatísticas]
       ANALYSIS --> PREDICT[Preditiva]
       
       INTEGRATION --> EXPORT[Exportação]
       INTEGRATION --> WORKFLOW[Workflow]
       INTEGRATION --> PLUGINS[Plugins]

📊 Módulos de Análise
=====================

O sistema inclui **9 módulos especializados** de análise:

1. **Performance Analysis** - Análise de potência, torque e aceleração
2. **Consumption Analysis** - Análise de consumo e eficiência de combustível
3. **Statistical Analysis** - Estatísticas descritivas e inferenciais
4. **Time Series Analysis** - Análises temporais e tendências
5. **Correlation Analysis** - Análises de correlação entre parâmetros
6. **Anomaly Detection** - Detecção automática de anomalias
7. **Predictive Analysis** - Modelos preditivos e forecasting
8. **Dynamic Analysis** - Análises de comportamento dinâmico
9. **Report Generation** - Geração automática de relatórios

📈 Qualidade e Cobertura
========================

.. raw:: html

   <div class="feature-grid">
      <div class="feature-card">
         <h3>🧪 Testes</h3>
         <p><strong>90%+ de cobertura</strong><br>
         • Testes unitários<br>
         • Testes de integração<br>
         • Testes de UI<br>
         • Fixtures e mocks</p>
      </div>
      <div class="feature-card">
         <h3>🔍 Qualidade</h3>
         <p><strong>Zero issues críticos</strong><br>
         • Type checking (MyPy)<br>
         • Code formatting (Black)<br>
         • Linting (Pylint)<br>
         • Security scan (Bandit)</p>
      </div>
      <div class="feature-card">
         <h3>📖 Documentação</h3>
         <p><strong>100% documentado</strong><br>
         • API reference completa<br>
         • Guias de usuário<br>
         • Tutoriais práticos<br>
         • Exemplos funcionais</p>
      </div>
   </div>

🆘 Suporte e Comunidade
=======================

**Documentação e Recursos**
   - 📚 :doc:`Guias completos <user-guide/installation>`
   - 🎓 :doc:`Tutoriais práticos <tutorials/data-import>`
   - 🔧 :doc:`Referência da API <api/index>`
   - 🏗️ :doc:`Guia do desenvolvedor <dev-guide/architecture>`

**Encontrou um Bug?**
   - 🐛 `Issues no GitHub <https://github.com/fueltune/analyzer-streamlit/issues>`_
   - 📧 E-mail: support@fueltune.com
   - 💬 Discord: `FuelTune Community <https://discord.gg/fueltune>`_

**Quer Contribuir?**
   - 🤝 :doc:`Guia de contribuição <dev-guide/contributing>`
   - 🧪 :doc:`Como executar testes <dev-guide/testing>`
   - 🚀 :doc:`Deploy e produção <dev-guide/deployment>`

📄 Licença
==========

Este projeto está licenciado sob a **Licença MIT** - veja o arquivo `LICENSE <https://github.com/fueltune/analyzer-streamlit/blob/main/LICENSE>`_ para detalhes.

.. note::
   **Copyright (c) 2024 FuelTune Team**
   
   Desenvolvido com ❤️ para a comunidade automotiva brasileira e internacional.

----

**Última atualização:** |today|

**Versão da documentação:** |version|

.. raw:: html

   <div style="text-align: center; margin: 2rem 0; padding: 1rem; background: #f8f9fa; border-radius: 8px;">
      <p><strong>🚀 Pronto para começar?</strong></p>
      <p>Siga o <a href="user-guide/installation.html">guia de instalação</a> e comece a analisar seus dados FuelTech em minutos!</p>
   </div>