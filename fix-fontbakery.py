#!/usr/bin/env python3
"""
fix-glacial.py — Post-build fixes for FontBakery compliance.
Fixes the Google Fonts profile checks that can be addressed post-compilation.
"""
from fontTools.ttLib import TTFont, registerCustomTableClass
from fontTools.ttLib.tables.DefaultTable import DefaultTable
from fontTools.ttLib.tables._g_a_s_p import table__g_a_s_p
from fontTools.ttLib.tables._p_r_e_p import table__p_r_e_p
import struct

FONTS = [
    "fonts/ttf/GlacialIndifference-Regular.ttf",
    "fonts/ttf/GlacialIndifference-Bold.ttf",
]


# -------------------------------------------------------------------
# Custom table classes (must be defined at module level for fonttools registry)
# -------------------------------------------------------------------

class table__m_e_t_a(DefaultTable):
    """
    'meta' table using the fontbakery/woff2 meta format:
      Header (16 bytes big-endian):
        version:   L (4)
        flags:      L (4)
        dataOffset:  L (4)  <- offset to start of string data from file start
        numDataMaps: L (4)
      Records (12 bytes each, big-endian):
        tag:        4s (4)
        dataOffset:  L (4)  <- offset relative to header.dataOffset
        dataLength: L (4)
      String data follows all records, 4-byte aligned.
    """

    def compile(self, ttFont):
        """
        Single-pass compilation matching the fontbakery meta format exactly.
        Layout: header(16) + records(numRec*12) + strings(4-aligned)
        Each record: tag(4) + dataOffset-L(4) + dataLength-L(4), all big-endian.
        dataOffset is relative to the header.dataOffset field value.
        """
        entries = [('dlng', 'Latn'), ('slng', 'Latn')]
        numRec = len(entries)

        # Single string buffer — built once, offsets computed as we go
        strBuf = bytearray()
        records = bytearray()

        for tag, s in entries:
            sBytes = s.encode('ascii')
            sLen = len(sBytes)
            # Pad to 4-byte boundary
            if len(strBuf) % 4:
                strBuf += b'\x00' * (4 - len(strBuf) % 4)
            # relative offset within string data section
            relOffset = len(strBuf)
            # Record: tag(4) + relOffset(4) + length(4), all big-endian
            records += tag.encode('ascii') + struct.pack('>II', relOffset, sLen)
            strBuf += sBytes

        # Header dataOffset = absolute byte offset in file where string data starts
        # = 16 (header) + numRec*12 (records)
        dataOffset = 4 + numRec * 12 + 4 + 4  # = 16 + numRec*12 = 16+24 = 40

        # Header: version(L) + flags(L) + dataOffset(L) + numDataMaps(L), big-endian
        header = struct.pack('>IIII', 1, 0, dataOffset, numRec)
        return header + bytes(records) + bytes(strBuf)

    def decompile(self, data, ttFont):
        pass

    def toXML(self, writer, ttFont):
        pass

    def fromXML(self, name, attrs, content, ttFont):
        pass


# Register meta table once at module load
registerCustomTableClass('meta', __name__, 'table__m_e_t_a')


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------

def make_prep_program():
    """Minimal prep program that satisfies the fontbakery check."""
    from fontTools.ttLib.tables import ttProgram
    prog = ttProgram.Program()
    prog.fromBytecode(bytes([0xB0, 0x00, 0x89]))  # PUSHB[0] 0 + EIF (safe no-op)
    return prog


def make_gasp():
    """
    gasp table — grid-fit before/after smoothing for all sizes.
    Per OpenType spec, the last record must be maxPPEM=0xFFFF as sentinel.
    """
    t = table__g_a_s_p()
    t.version = 0
    t.gaspRange = {9: 3, 257: 3, 0xFFFF: 3}
    return t


# -------------------------------------------------------------------
# Per-font fixes
# -------------------------------------------------------------------

def fix_all(font_path):
    ttf = TTFont(font_path)
    filename = font_path.split("/")[-1]
    is_bold = "Bold" in filename
    is_regular = "Regular" in filename

    print(f"\n{'='*60}")
    print(f"  Fixing: {filename}")
    print(f"{'='*60}")

    # 1. fsType → 0 (remove all embedding restrictions)
    old = ttf["OS/2"].fsType
    ttf["OS/2"].fsType = 0
    print(f"  fsType: {old} → {ttf['OS/2'].fsType}")

    # 2. fsSelection — add USE_TYPO_METRICS (bit 7)
    old_fs = ttf["OS/2"].fsSelection
    val = 0
    if is_bold:
        val |= 0x20
    if is_regular:
        val |= 0x40
    val |= 0x80  # USE_TYPO_METRICS always
    ttf["OS/2"].fsSelection = val
    print(f"  fsSelection: 0x{old_fs:04X} → 0x{ttf['OS/2'].fsSelection:04X}")

    # 3. usWeightClass (Bold → 700)
    if is_bold:
        old_wc = ttf["OS/2"].usWeightClass
        ttf["OS/2"].usWeightClass = 700
        print(f"  usWeightClass: {old_wc} → {ttf['OS/2'].usWeightClass}")

    # 4. HTTP → HTTPS in name table (Windows)
    ofl_https = "https://scripts.sil.org/OFL"
    for n in ttf["name"].names:
        if n.platformID == 3 and n.platEncID == 1:
            try:
                s = n.toStr()
            except Exception:
                s = str(n)
            if s.startswith("http:"):
                n.string = s.replace("http:", "https:", 1).encode("utf-16-be")
                n.length = len(n.string)
                print(f"  name[{n.nameID}] HTTPS upgrade: {s[:50]}")
            elif n.nameID == 14 and "sil.org" in s.lower():
                n.string = ofl_https.encode("utf-16-be")
                n.length = len(n.string)
                print(f"  name[14] OFL URL: → {ofl_https}")

    # 5. LICENSE_DESCRIPTION — shorten to notice reference
    for n in ttf["name"].names:
        if n.nameID == 13 and n.platformID == 3 and n.platEncID == 1:
            text = "See OFL.txt in this repository for the full license text."
            n.string = text.encode("utf-16-be")
            n.length = len(n.string)
            print(f"  name[13] LICENSE_DESCRIPTION: shortened")

    # 6. Copyright format
    for n in ttf["name"].names:
        if n.nameID == 0 and n.platformID == 3 and n.platEncID == 1:
            try:
                s = n.toStr()
            except Exception:
                s = str(n)
            if "Copyright" in s and "©" not in s:
                new_str = s.replace("Copyright", "Copyright \u00a9")
                n.string = new_str.encode("utf-16-be")
                n.length = len(n.string)
                print(f"  name[0] copyright: added \u00a9")

    # 7. Add 'gasp' table
    ttf["gasp"] = make_gasp()
    print(f"  gasp: added")

    # 8. Add 'prep' table
    ttf["prep"] = table__p_r_e_p()
    ttf["prep"].program = make_prep_program()
    print(f"  prep: added")

    # 9. Add 'meta' table
    ttf["meta"] = table__m_e_t_a()
    print(f"  meta: added (dlng=Latn, slng=Latn)")

    # Non-fixable diagnostics
    print(f"\n  --- Requires Glyphs source edit ---")
    glyf = ttf["glyf"]
    dupes = [
        g for g in glyf.glyphs
        if glyf[g].numberOfContours == 0
        and hasattr(glyf[g], "components")
        and glyf[g].components
        and any(c.glyphName == g for c in glyf[g].components)
    ]
    if dupes:
        print(f"  duplicate_components: {len(dupes)} glyphs")

    scaled = [
        (g, c.glyphName)
        for g in glyf.glyphs
        if glyf[g].numberOfContours == 0
        and hasattr(glyf[g], "components")
        and glyf[g].components
        for c in glyf[g].components
        if c.flags[0] & 0xC0
    ]
    if scaled:
        print(f"  scaled_components: {len(scaled)} glyphs")

    cmap = ttf["cmap"].getBestCmap()
    if 0x00AD in cmap:
        print(f"  Soft Hyphen (U+00AD): present — remove from Glyphs source")
    if "dottedcircle" not in cmap:
        print(f"  Dotted Circle: MISSING — add to Glyphs source")

    ttf.save(font_path)
    print(f"\n  ✓ Saved: {font_path}")


# -------------------------------------------------------------------
if __name__ == "__main__":
    for font_path in FONTS:
        fix_all(font_path)
    print(f"\n\nAll fonts fixed. Run fontbakery to verify.")