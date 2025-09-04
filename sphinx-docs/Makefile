# Makefile for Sphinx documentation

# You can set these variables from the command line, and also
# from the environment for the first two.
SPHINXOPTS    ?=
SPHINXBUILD  ?= sphinx-build
SOURCEDIR    = .
BUILDDIR     = _build

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile

# Custom targets for development workflow

# Install documentation dependencies
install-deps:
	pip install -r requirements-docs.txt

# Clean build directory completely
clean-all:
	rm -rf $(BUILDDIR)/*
	rm -rf autoapi/

# Build HTML documentation with clean start
html-clean: clean-all html

# Build documentation and serve locally
serve: html
	@echo "Serving documentation at http://localhost:8000"
	cd $(BUILDDIR)/html && python -m http.server 8000

# Check for broken links and references
linkcheck:
	@$(SPHINXBUILD) -b linkcheck "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

# Check documentation style and formatting
doccheck:
	doc8 --ignore-path $(BUILDDIR) .
	rstcheck --recursive .

# Build and validate everything
validate: doccheck html linkcheck
	@echo "✅ Documentation validation completed successfully!"

# Live reload during development (requires sphinx-autobuild)
livehtml:
	sphinx-autobuild "$(SOURCEDIR)" "$(BUILDDIR)/html" --host 0.0.0.0 --port 8000

# Build PDF documentation
pdf: latexpdf
	@echo "PDF documentation built: $(BUILDDIR)/latex/FuelTuneAnalyzer.pdf"

# Generate coverage report for documentation
coverage:
	@$(SPHINXBUILD) -b coverage "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
	@echo "Documentation coverage report: $(BUILDDIR)/coverage/python.txt"

# Build for production deployment
production: clean-all
	@$(SPHINXBUILD) -b html "$(SOURCEDIR)" "$(BUILDDIR)/html" -D html_theme_options.analytics_id=G-XXXXXXXXXX
	@echo "✅ Production documentation built successfully!"

# Quick development build (faster, less validation)
dev: 
	@$(SPHINXBUILD) -b html "$(SOURCEDIR)" "$(BUILDDIR)/html" -W --keep-going $(SPHINXOPTS) $(O)

# Full build with all formats
all: clean-all html latexpdf epub
	@echo "✅ All documentation formats built successfully!"

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)