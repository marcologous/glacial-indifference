# Glacial Indifference

A free and open source display typeface with a bold, contemporary aesthetic.

![Font specimen](images/Glacial%20Indifference%20Specimen_8.png)

## About

Glacial Indifference is a modern display typeface designed for impactful headlines and bold statements. With its clean geometric forms and distinctive character, it brings a fresh voice to any design project.

## Features

- **Display-optimized**: Perfect for headlines, titles, and hero sections
- **Open Source**: Completely free for personal and commercial use
- **Multiple formats**: Available in TTF, OTF, WOFF, and WOFF2
- **Web font ready**: Optimized web font files included

## Installation

### Desktop

1. Download the latest release from the [Releases page](https://github.com/marcologous/glacial-indifference/releases)
2. Unzip the downloaded file
3. Install the font:
   - **macOS**: Double-click the font file and click "Install Font"
   - **Windows**: Right-click the font file and select "Install"

### Web

Using the web fonts in your project:

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Glacial+Indifference&display=swap" rel="stylesheet">
```

Or use the WOFF2 files directly from the repository:

```css
@font-face {
  font-family: 'Glacial Indifference';
  src: url('fonts/GlacialIndifference-Regular.woff2') format('woff2');
  font-weight: 400;
  font-style: normal;
}
```

## Building from Source

### Requirements

- [Glyphs](https://glyphsapp.com/) (for editing)
- [fonttools](https://github.com/fonttools/fonttools) (for building)
- [woff2](https://github.com/google/woff2) (for compression)

### Build process

```bash
# Install dependencies
pip install fonttools brotli zopfli

# Build OTF from Glyphs source
fonttools build sources/GlacialIndifference_1312.glyphs

# Build web fonts
make webfonts
```

## Quality Assurance

This font is checked using [FontBakery](https://fontbakery.org/), an automated quality assurance tool for font families. Check the [quality reports](https://github.com/marcologous/glacial-indifference/actions) for details.

## License

Licensed under the [SIL Open Font License (OFL)](LICENSE). You can use this font freely for personal and commercial projects.

## Contributing

Contributions are welcome! Please read our [contributing guidelines](CONTRIBUTING.md) before submitting pull requests.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Authors

- **Alfredo Marco Pradil** - *Initial design* - [Hanken Design Co.](https://hanken.co)

## Acknowledgments

- Inspired by geometric sans-serif typography
- Built with love for the open source community

## Contact

- Website: https://hanken.co
- Email: hello@hanken.co

---

**Glacial Indifference** is part of the [HDC Foundry](https://github.com/marcologous) open source font collection.
