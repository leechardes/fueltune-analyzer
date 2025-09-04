# FuelTune Analyzer - Application Source Code

This directory will contain the main application source code for the FuelTune Analyzer Streamlit application.

## Directory Structure

```
app/
├── main.py              # Main Streamlit application entry point
├── components/          # Reusable UI components
│   ├── __init__.py
│   ├── vehicle_selector.py
│   ├── data_importer.py
│   ├── table_editor.py
│   ├── chart_viewer.py
│   └── report_generator.py
├── services/            # Business logic services
│   ├── __init__.py
│   ├── database_service.py
│   ├── csv_service.py
│   ├── analysis_service.py
│   ├── table_service.py
│   └── export_service.py
├── models/              # Data models and schemas
│   ├── __init__.py
│   ├── base.py
│   ├── vehicle.py
│   ├── log.py
│   ├── table.py
│   └── analysis.py
├── utils/               # Utility functions
│   ├── __init__.py
│   ├── validation.py
│   ├── calculations.py
│   ├── interpolation.py
│   └── helpers.py
└── pages/               # Streamlit pages
    ├── 1_🚗_Vehicles.py
    ├── 2_📊_Data_Import.py
    ├── 3_🗂️_Tables.py
    ├── 4_📈_Analysis.py
    └── 5_📋_Reports.py
```

## Implementation Guidelines

### Main Application (main.py)
- Configure Streamlit page settings
- Set up navigation and routing
- Initialize database connections
- Handle global error management
- Implement session state management

### Components Directory
Reusable UI components following these patterns:
- Type-safe component interfaces
- Consistent styling and behavior
- Error handling and validation
- Performance optimization
- Accessibility considerations

### Services Directory
Business logic services implementing:
- Repository pattern for data access
- Comprehensive error handling
- Performance optimization
- Logging and monitoring
- Transaction management

### Models Directory
SQLAlchemy models and Pydantic schemas:
- Complete FuelTech field support (37+ fields)
- Data validation and sanitization
- Relationship management
- Database optimization
- Type safety

### Utils Directory
Utility functions for:
- Data validation and cleaning
- Mathematical calculations
- Interpolation algorithms
- Helper functions
- Constants and configuration

### Pages Directory
Streamlit page modules:
- Individual page functionality
- Consistent navigation
- Session state management
- Error handling
- User feedback

## Development Standards

### Code Quality
- Full type hints required
- Docstrings for all public functions
- PEP 8 compliance with Black formatting
- Error handling for all user inputs
- Performance optimization

### Testing
- Unit tests for all components
- Integration tests for services
- UI component testing
- Performance benchmarks
- Security validation

### Documentation
- Comprehensive docstrings
- Code comments for complex logic
- README files for each module
- API documentation
- Usage examples

## Next Steps

This directory structure will be populated by the development agents:

1. **A01-SETUP-PYTHON**: Initialize project structure
2. **A02-DATA-PANDAS**: Implement models and services
3. **A03-UI-STREAMLIT**: Create UI components and pages
4. **A04-ANALYSIS-SCIPY**: Add analysis utilities
5. **A05-INTEGRATION**: Implement export services
6. **A06-TEST-PYTEST**: Add comprehensive testing
7. **A08-DOCS-SPHINX**: Generate documentation
8. **A09-DEPLOY-DOCKER**: Configure deployment

Each agent will follow the established patterns and maintain consistency across the codebase.