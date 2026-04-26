# Makefile for Glacial Indifference
#
# Targets:
#   make ttf              Build TTF fonts (Regular + Bold)
#   make otf              Build OTF fonts (Regular + Bold)
#   make all              Build all formats
#   make fix              Run post-build FontBakery compliance fixes
#   make check            Build + fix + run FontBakery checks
#   make clean            Remove all build artifacts
#   make package          Build all formats and zip for distribution

PYTHON := python3
FONTNAME := GlacialIndifference
VERSION := 1.312
SOURCES := sources/$(FONTNAME).glyphs
DIST_DIR := dist
FONTS_DIR := fonts
TTF_DIR := $(FONTS_DIR)/ttf
OTF_DIR := $(FONTS_DIR)/otf
TTF_DIR := $(BUILD_DIR)/ttf
OTF_DIR := $(BUILD_DIR)/otf
REPORTERS := reporters

# ── Default ──────────────────────────────────────────────────
.PHONY: all
all: ttf otf

# ── Build ──────────────────────────────────────────────────────
.PHONY: ttf otf build
build: ttf otf

ttf:
	@echo "Building TTF fonts..."
	@mkdir -p $(TTF_DIR)
	$(PYTHON) -m fontmake -g "$(SOURCES)" -o ttf --output-dir $(TTF_DIR) --filter DecomposeTransformedComponentsFilter

otf:
	@echo "Building OTF fonts..."
	@mkdir -p $(OTF_DIR)
	$(PYTHON) -m fontmake -g "$(SOURCES)" -o otf --output-dir $(OTF_DIR)

# ── FontBakery pipeline ───────────────────────────────────────────
.PHONY: check fix
check: fix
	@echo ""
	@echo "=== Running FontBakery check-googlefonts ==="
	@fontbakery check-googlefonts $(TTF_DIR)/*.ttf \
		--json $(REPORTERS)/index.json \
		--verbose 2>&1 | tee $(REPORTERS)/fontbakery.log
	@echo ""
	@echo "=== Summary ==="
	@if grep -q "^Total:" $(REPORTERS)/fontbakery.log; then \
		grep -A8 "^Total:" $(REPORTERS)/fontbakery.log | tail -7; \
	else \
		echo "No summary found — see $(REPORTERS)/fontbakery.log"; \
	fi

fix:
	@echo "=== Running post-build FontBakery fixes ==="
	@mkdir -p $(REPORTERS)
	@$(PYTHON) fix-fontbakery.py && echo "All fixes applied." \
		|| echo "Fixer encountered errors (see above)."

# ── Distribution ─────────────────────────────────────────────
.PHONY: package
package: all
	@echo "Packaging distribution..."
	@mkdir -p $(DIST_DIR)
	zip -r $(DIST_DIR)/$(FONTNAME)-$(VERSION).zip $(FONTS_DIR)/

# ── Clean ─────────────────────────────────────────────────────────
.PHONY: clean
clean:
	rm -rf $(DIST_DIR) $(FONTS_DIR)/ttf $(FONTS_DIR)/otf $(FONTS_DIR)/woff $(FONTS_DIR)/woff2 $(REPORTERS)
	rm -rf $(BUILD_DIR) $(DIST_DIR) $(FONTS_DIR) $(REPORTERS)

# ── Install dependencies ────────────────────────────────────────────
.PHONY: install-deps
install-deps:
	$(PYTHON) -m pip install -r requirements.txt

# ── Help ─────────────────────────────────────────────────────────
.PHONY: help
help:
	@echo "Glacial Indifference Makefile"
	@echo ""
	@echo "  make ttf          Build TTF fonts from source"
	@echo "  make otf          Build OTF fonts from source"
	@echo "  make all          Build all formats (ttf + otf)"
	@echo "  make fix         Run post-build FontBakery compliance fixes"
	@echo "  make check        Build TTF + fix + run FontBakery quality checks"
	@echo "  make package     Build all formats and zip for distribution"
	@echo "  make clean        Remove all build artifacts"
	@echo "  make install-deps Install build dependencies"
	@echo ""
	@echo "The 'check' target is the full FontBakery pipeline:"
	@echo "  1. Build TTF from Glyphs source"
	@echo "  2. Apply fix-fontbakery.py (fsType, fsSelection, weightClass, URLs, gasp, prep, meta)"
	@echo "  3. Run fontbakery check-googlefonts"
	@echo ""
	@echo "Remaining FAILs after fix-fontbakery.py are source-level issues"
	@echo "that require edits in the Glyphs source file."