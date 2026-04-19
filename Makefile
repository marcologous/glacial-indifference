# Makefile for Glacial Indifference font build

PYTHON := python3
FONTNAME := GlacialIndifference
VERSION := 1.312
SOURCES := sources/$(FONTNAME).glyphs
BUILD_DIR := build
DIST_DIR := dist
FONTS_DIR := fonts

# Default target
.PHONY: all
all: build

# Build OTF and TTF fonts
.PHONY: build
build: otf ttf

# Build OTF fonts
.PHONY: otf
otf:
	@echo "Building OTF fonts..."
	@mkdir -p $(BUILD_DIR)/otf
	$(PYTHON) -m fontmake -m $(SOURCES) -o otf --output-path $(BUILD_DIR)/otf/$(FONTNAME)-Regular.otf

# Build TTF fonts
.PHONY: ttf
ttf:
	@echo "Building TTF fonts..."
	@mkdir -p $(BUILD_DIR)/ttf
	$(PYTHON) -m fontmake -m $(SOURCES) -o ttf --output-path $(BUILD_DIR)/ttf/$(FONTNAME)-Regular.ttf

# Build web fonts (WOFF2)
.PHONY: webfonts
webfonts: otf
	@echo "Building web fonts..."
	@mkdir -p $(FONTS_DIR)
	@for font in $(BUILD_DIR)/otf/*.otf; do \
		woff2_compress "$$font" || true; \
	done
	@mv $(BUILD_DIR)/otf/*.woff2 $(FONTS_DIR)/ 2>/dev/null || true

# Package for distribution
.PHONY: package
package: build webfonts
	@echo "Packaging distribution..."
	@mkdir -p $(DIST_DIR)
	@zip -r $(DIST_DIR)/$(FONTNAME)-$(VERSION).zip fonts/ build/otf/ build/ttf/

# Run FontBakery checks
.PHONY: check
check:
	fontbakery check-googlefonts $(SOURCES)

# Clean build artifacts
.PHONY: clean
clean:
	rm -rf $(BUILD_DIR) $(DIST_DIR) $(FONTS_DIR)

# Install build dependencies
.PHONY: install-deps
install-deps:
	$(PYTHON) -m pip install fonttools fontmake brotli zopfli woff2

# Help
.PHONY: help
help:
	@echo "Available targets:"
	@echo "  all        - Build all font formats (default)"
	@echo "  otf        - Build OpenType fonts"
	@echo "  ttf        - Build TrueType fonts"
	@echo "  webfonts   - Build web-optimized fonts"
	@echo "  package    - Create distribution package"
	@echo "  check      - Run FontBakery quality checks"
	@echo "  clean      - Remove build artifacts"
	@echo "  install-deps - Install build dependencies"