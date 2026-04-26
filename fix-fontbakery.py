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
    "build/ttf/GlacialIndifference-Regular.ttf",
    "build/ttf/GlacialIndifference-Bold.ttf",
]


# -------------------------------------------------------------------
# Custom table classes (must be defined at module level for fonttools registry)
# -------------------------------------------------------------------

class table__m_e_t_a(DefaultTable):
    """'meta' table using the fontbakery/woff2 meta format."""

    def compile(self, ttFont):
        entries = [('dlng', 'Latn'), ('slng', 'Latn')]
        numRec = len(entries)
        strBuf = bytearray()
        records = bytearray()

        for tag, s in entries:
            sBytes = s.encode('ascii')
            sLen = len(sBytes)
            if len(strBuf) % 4:
                strBuf += b'\x00' * (4 - len(strBuf) % 4)
            relOffset = len(strBuf)
            records += tag.encode('ascii') + struct.pack('>II', relOffset, sLen)
            strBuf += sBytes

        dataOffset = 4 + numRec * 12 + 4 + 4
        header = struct.pack('>IIII', 1, 0, dataOffset, numRec)
        return header + bytes(records) + bytes(strBuf)

    def decompile(self, data, ttFont):
        pass

    def toXML(self, writer, ttFont):
        pass

    def fromXML(self, name, attrs, content, ttFont):
        pass


registerCustomTableClass('meta', __name__, 'table__m_e_t_a')


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------

def make_prep_program():
    from fontTools.ttLib.tables import ttProgram
    prog = ttProgram.Program()
    prog.fromBytecode(bytes([0xB0, 0x00, 0x89]))
    return prog


def make_gasp():
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

    # 1. fsType → 0
    old = ttf["OS/2"].fsType
    ttf["OS/2"].fsType = 0
    print(f"  fsType: {old} → {ttf['OS/2'].fsType}")

    # 2. fsSelection — add USE_TYPO_METRICS (bit 7)
    old_fs = ttf["OS/2"].fsSelection
    val = 0x80
    if is_bold:
        val |= 0x20
    if is_regular:
        val |= 0x40
    ttf["OS/2"].fsSelection = val
    print(f"  fsSelection: 0x{old_fs:04X} → 0x{ttf['OS/2'].fsSelection:04X}")

    # 3. usWeightClass
    if is_bold:
        old_wc = ttf["OS/2"].usWeightClass
        ttf["OS/2"].usWeightClass = 700
        print(f"  usWeightClass: {old_wc} → {ttf['OS/2'].usWeightClass}")

    # 4. HTTPS in name table
    ofl_https = "https://scripts.sil.org/OFL"
    for n in ttf["name"].names:
        if n.platformID == 3 and n.platEncID == 1:
            try:
                s = n.toStr()
            except:
                s = str(n)
            if s.startswith("http:"):
                n.string = s.replace("http:", "https:", 1).encode("utf-16-be")
                n.length = len(n.string)
                print(f"  name[{n.nameID}] HTTPS upgrade")

    # 5. Add 'gasp' table
    ttf["gasp"] = make_gasp()
    print(f"  gasp: added")

    # 6. Add 'prep' table
    ttf["prep"] = table__p_r_e_p()
    ttf["prep"].program = make_prep_program()
    print(f"  prep: added")

    # 7. Add 'meta' table
    ttf["meta"] = table__m_e_t_a()
    print(f"  meta: added (dlng=Latn, slng=Latn)")

    # Diagnostics
    glyf = ttf["glyf"]
    dupes = [g for g in glyf.glyphs if glyf[g].numberOfContours == 0 and hasattr(glyf[g], "components") and glyf[g].components and any(c.glyphName == g for c in glyf[g].components)]
    if dupes:
        print(f"\n  --- Requires Glyphs source edit ---")
        print(f"  duplicate_components: {len(dupes)} glyphs")

    cmap = ttf["cmap"].getBestCmap()
    if 0x00AD in cmap:
        print(f"  Soft Hyphen (U+00AD): present — remove from Glyphs source")
    if "dottedcircle" not in cmap:
        print(f"  Dotted Circle: MISSING — add to Glyphs source")

    ttf.save(font_path)
    print(f"\n  ✓ Saved: {font_path}")


if __name__ == "__main__":
    for font_path in FONTS:
        fix_all(font_path)
    print(f"\n\nAll fonts fixed. Run fontbakery to verify.")