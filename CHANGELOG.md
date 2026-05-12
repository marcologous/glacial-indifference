# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- 4 font instances: Regular (400), Medium (500), SemiBold (600), Bold (700)
- All font formats: TTF, OTF, woff, woff2
- Updated fix-fontbakery.py for all instances
- Updated METADATA.pb with all 4 fonts

### Changed
- CI workflow updated for full build pipeline (TTF, OTF, woff, woff2)
- Removed HTML output from fontbakery (JSON only)

## [1.323] - 2026-05-12

### Added
- Source edits: Additional glyphs converted from components to outlines
- FontBakery check run with dated logs

### Changed
- Continued FontBakery compliance improvements

### Known Issues (Source Edits Required)
- freetype_rasterizer: FreeType crashes on outline
- smart_dropout: Missing prep table instructions
- ttx_roundtrip: TTX roundtrip issues
- family/win_ascent_and_descent: OS/2 table metrics

## [1.322] - 2026-04-26

### Added
- Source file updates: glyphs converted from components to outlines
- FontBakery check run with dated logs

### Changed
- Continued FontBakery compliance improvements
- Reporters directory: JSON log only (no HTML)

### Fixed
- nested_components issue resolved (source edits)

### Known Issues
- freetype_rasterizer: FreeType crashes on outline
- smart_dropout: Missing prep table instructions
- ttx_roundtrip: TTX roundtrip issues

## [1.321] - 2026-04-26

### Added
- DecomposeTransformedComponentsFilter in build process
- METADATA.pb with subsets: [latin, menu]
- OFL.txt with canonical SIL OFL 1.1 text
- Fixed name[13] (LICENSE DESCRIPTION) post-build

### Changed
- Rebuild with fontmake filter for transformed components
- Directory structure: fonts/ttf/, fonts/otf/, fonts/woff/, fonts/woff2/
- Source: converted 7 transformed component glyphs to outlines

### Fixed
- FontBakery compliance fixes applied post-build