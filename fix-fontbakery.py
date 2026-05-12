#!/usr/bin/env python3
"""
fix-fontbakery.py — Post-build fixes for FontBakery compliance.
Fixes the Google Fonts profile checks that can be addressed post-compilation.
"""
from fontTools.ttLib import TTFont, registerCustomTableClass
from fontTools.ttLib.tables.DefaultTable import DefaultTable
from fontTools.ttLib.tables._g_a_s_p import table__g_a_s_p
from fontTools.ttLib.tables._p_r_e_p import table__p_r_e_p
import struct

FONTS = [
    "fonts/ttf/GlacialIndifference-Regular.ttf",
    "fonts/ttf/GlacialIndifference-Medium.ttf",
    "fonts/ttf/GlacialIndifference-SemiBold.ttf",
    "fonts/ttf/GlacialIndifference-Bold.ttf",
    "build/ttf/GlacialIndifference-Regular.ttf",
    "build/ttf/GlacialIndifference-Bold.ttf",
]


# -------------------------------------------------------------------
# Custom table classes (must be defined at module level for fonttools registry)
# -------------------------------------------------------------------

class table__m_e_t_a(DefaultTable):
    """'meta' table with proper text-tag format."""

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
        version, flags, dataOffset, numRec = struct.unpack('>IIII', data[:16])
        self.data = {}
        for i in range(numRec):
            off = 16 + i * 12
            tag = data[off:off+4].decode('ascii')
            relOffset, sLen = struct.unpack('>II', data[off+4:off+12])
            s = data[dataOffset + relOffset:dataOffset + relOffset + sLen].decode('ascii')
            self.data[tag] = s

    def toXML(self, writer, ttFont):
        for tag, val in getattr(self, 'data', {'dlng': 'Latn', 'slng': 'Latn'}).items():
            writer.simpletag(tag, val)
            writer.newline()

    def fromXML(self, name, attrs, content, ttFont):
        if not hasattr(self, 'data'):
            self.data = {}
        self.data[name] = attrs.get('init', attrs.get('value', ''))


registerCustomTableClass('meta', __name__, 'table__m_e_t_a')


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------

def make_prep_program():
    """Smart dropout prep program per FontBakery spec."""
    from fontTools.ttLib.tables import ttProgram
    prog = ttProgram.Program()
    # B8 01 FF    PUSHW 0x01FF
    # 85          SCANCTRL (unconditionally turn on dropout control mode)
    # B0 04       PUSHB 0x04
    # 8D          SCANTYPE (enable smart dropout control: rules 1, 2, 5)
    prog.fromBytecode(bytes([0xB8, 0x01, 0xFF, 0x85, 0xB0, 0x04, 0x8D]))
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
    is_bold = "Bold" in filename and "SemiBold" not in filename
    is_regular = "Regular" in filename

    print(f"\n{'='*60}")
    print(f"  Fixing: {filename}")
    print(f"{'='*60}")

    # 1. fsType -> 0 (installable embedding)
    old = ttf["OS/2"].fsType
    ttf["OS/2"].fsType = 0
    print(f"  fsType: {old} -> {ttf['OS/2'].fsType}")

    # 2. fsSelection — bit 7 (USE_TYPO_METRICS) + bits 0/5/6 per style
    # Per fontbakery opentype/fsselection check:
    # - bit 6 (REGULAR) = set for non-bold, clear for Bold
    # - bit 5 (BOLD) = set for Bold only
    # - bit 7 (USE_TYPO_METRICS) = always set
    old_fs = ttf["OS/2"].fsSelection
    val = 0x80  # USE_TYPO_METRICS (bit 7) always set
    if is_bold:
        val |= 0x20  # BOLD bit only, no REGULAR bit for Bold weight
    else:
        val |= 0x40  # REGULAR bit for non-bold weights
    ttf["OS/2"].fsSelection = val
    print(f"  fsSelection: 0x{old_fs:04X} -> 0x{ttf['OS/2'].fsSelection:04X}")

    # 3. usWeightClass
    old_wc = ttf["OS/2"].usWeightClass
    if is_bold:
        target_wc = 700
    elif "SemiBold" in filename:
        target_wc = 600
    elif "Medium" in filename:
        target_wc = 500
    else:
        target_wc = 400
    if old_wc != target_wc:
        ttf["OS/2"].usWeightClass = target_wc
        print(f"  usWeightClass: {old_wc} -> {ttf['OS/2'].usWeightClass}")

    # 4. HTTPS in name table (nameID 14 / license URL)
    for n in ttf["name"].names:
        if n.platformID == 3 and n.platEncID == 1:
            try:
                s = n.toStr()
            except:
                s = str(n)
            if "http://" in s:
                n.string = s.replace("http://", "https://", 1).encode("utf-16-be")
                n.length = len(n.string)
                print(f"  name[{n.nameID}] http -> https")

    # 5. Fix usWinDescent (must be >= 914 per fontbakery)
    old_wd = ttf["OS/2"].usWinDescent
    if old_wd < 914:
        ttf["OS/2"].usWinDescent = 914
        # Adjust usWinAscent to keep sum consistent
        old_wa = ttf["OS/2"].usWinAscent
        diff = 914 - old_wd
        ttf["OS/2"].usWinAscent = old_wa + diff
        print(f"  usWinDescent: {old_wd} -> 914 (usWinAscent: {old_wa} -> {ttf['OS/2'].usWinAscent})")

    # 6. Add 'gasp' table (grid-fitting/scaling)
    ttf["gasp"] = make_gasp()
    print(f"  gasp: added")

    # 7. Add 'prep' table with smart dropout instructions
    ttf["prep"] = table__p_r_e_p()
    ttf["prep"].program = make_prep_program()
    bc = bytes(ttf["prep"].program.getBytecode()).hex()
    print(f"  prep: added (smart dropout, bytecode: {bc})")

    # 8. Add 'meta' table (dlng/slng)
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
    print(f"\n  Saved: {font_path}")


if __name__ == "__main__":
    for font_path in FONTS:
        fix_all(font_path)
    print(f"\n\nAll fonts fixed. Run fontbakery to verify.")