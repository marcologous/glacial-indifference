#!/usr/bin/env python3
"""
fix-fontbakery.py — Post-build fixes for FontBakery compliance.
Fixes the Google Fonts profile checks that can be addressed post-compilation.

This script is designed to be run after fontmake builds the fonts.
It fixes all known FontBakery issues and prepares fonts for distribution.
"""
from fontTools.ttLib import TTFont, registerCustomTableClass
from fontTools.ttLib.tables.DefaultTable import DefaultTable
from fontTools.ttLib.tables._g_a_s_p import table__g_a_s_p
from fontTools.ttLib.tables._p_r_e_p import table__p_r_e_p
import struct
import os
import glob
import shutil

# Font configurations
TTF_FONTS = [
    "fonts/ttf/GlacialIndifference-Regular.ttf",
    "fonts/ttf/GlacialIndifference-Medium.ttf",
    "fonts/ttf/GlacialIndifference-SemiBold.ttf",
    "fonts/ttf/GlacialIndifference-Bold.ttf",
]

# Font weight mapping
WEIGHT_MAP = {
    "Regular.ttf": 400,
    "Medium.ttf": 500,
    "SemiBold.ttf": 600,
    "Bold.ttf": 700,
}


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


def fix_name_table_null_bytes(ttf):
    """Remove null bytes from name table entries."""
    fixed_count = 0
    for record in ttf["name"].names:
        try:
            # Try Unicode decode
            s = record.toUnicode()
            if '\x00' in s:
                # Remove null bytes
                new_str = s.replace('\x00', '')
                # Re-encode based on platform
                if record.platformID == 3:  # Windows
                    record.string = new_str.encode('utf-16-be')
                elif record.platformID == 1:  # Mac
                    record.string = new_str.encode('mac_roman')
                record.length = len(record.string)
                fixed_count += 1
        except Exception:
            pass
    return fixed_count


def generate_metadata_pb(fonts_dir):
    """Generate METADATA.pb for a font directory."""
    import re

    # Find all TTF files in directory
    ttf_files = sorted(glob.glob(os.path.join(fonts_dir, "*.ttf")))
    if not ttf_files:
        return

    # Get font family name from first font
    font = TTFont(ttf_files[0])
    family_name = None
    for record in font["name"].names:
        if record.nameID == 1:  # Family name
            try:
                family_name = record.toUnicode()
                break
            except:
                pass

    if not family_name:
        family_name = "Unknown"

    # Get version from first font
    version = "1.000"
    for record in font["name"].names:
        if record.nameID == 5:  # Version
            try:
                v = record.toUnicode()
                match = re.search(r'Version\s+(\d+\.\d+)', v)
                if match:
                    version = match.group(1)
            except:
                pass

    # Build METADATA.pb content
    lines = [
        "name: \"{}\"".format(family_name),
        "fonts:",
    ]

    for ttf in ttf_files:
        font = TTFont(ttf)
        filename = os.path.basename(ttf)

        # Extract style from filename
        if "Bold" in filename and "SemiBold" not in filename:
            style = "Bold"
            weight = 700
        elif "SemiBold" in filename:
            style = "SemiBold"
            weight = 600
        elif "Medium" in filename:
            style = "Medium"
            weight = 500
        else:
            style = "Regular"
            weight = 400

        # Get postScriptName
        ps_name = filename.replace(".ttf", "")

        lines.append("  - filename: \"{}\"".format(filename))
        lines.append("    style: \"{}\"".format(style.lower()))
        lines.append("    weight: {}".format(weight))

    # Also add OTF, WOFF, WOFF2 entries
    for ext in ["otf", "woff", "woff2"]:
        other_files = sorted(glob.glob(os.path.join(fonts_dir, "*.{}".format(ext))))
        for f in other_files:
            filename = os.path.basename(f)
            lines.append("  - filename: \"{}\"".format(filename))
            lines.append("    style: \"normal\"")
            lines.append("    weight: 400")

    metadata_path = os.path.join(fonts_dir, "METADATA.pb")
    with open(metadata_path, "w") as f:
        f.write("\n".join(lines) + "\n")

    print(f"  Generated: {metadata_path}")


def copy_ofl_txt(fonts_dir):
    """Copy OFL.txt to font directory if not present."""
    ofl_src = "OFL.txt"
    ofl_dst = os.path.join(fonts_dir, "OFL.txt")

    if os.path.exists(ofl_src) and not os.path.exists(ofl_dst):
        shutil.copy(ofl_src, ofl_dst)
        print(f"  Copied: OFL.txt -> {fonts_dir}/")


# -------------------------------------------------------------------
# Per-font fixes
# -------------------------------------------------------------------

def fix_all(font_path):
    ttf = TTFont(font_path)
    filename = font_path.split("/")[-1]
    is_bold = "Bold" in filename and "SemiBold" not in filename

    print(f"\n{'='*60}")
    print(f"  Fixing: {filename}")
    print(f"{'='*60}")

    # 1. fsType -> 0 (installable embedding)
    old = ttf["OS/2"].fsType
    ttf["OS/2"].fsType = 0
    print(f"  fsType: {old} -> {ttf['OS/2'].fsType}")

    # 2. fsSelection — bit 7 (USE_TYPO_METRICS) + bits 0/5/6 per style
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

    # 5. Fix null bytes in name table
    null_fixed = fix_name_table_null_bytes(ttf)
    if null_fixed > 0:
        print(f"  name table: fixed {null_fixed} null byte entries")

    # 6. Fix usWinDescent (must be >= 914 per fontbakery)
    old_wd = ttf["OS/2"].usWinDescent
    if old_wd < 914:
        ttf["OS/2"].usWinDescent = 914
        old_wa = ttf["OS/2"].usWinAscent
        diff = 914 - old_wd
        ttf["OS/2"].usWinAscent = old_wa + diff
        print(f"  usWinDescent: {old_wd} -> 914 (usWinAscent: {old_wa} -> {ttf['OS/2'].usWinAscent})")

    # 7. Add 'gasp' table (grid-fitting/scaling)
    ttf["gasp"] = make_gasp()
    print(f"  gasp: added")

    # 8. Add 'prep' table with smart dropout instructions
    ttf["prep"] = table__p_r_e_p()
    ttf["prep"].program = make_prep_program()
    bc = bytes(ttf["prep"].program.getBytecode()).hex()
    print(f"  prep: added (smart dropout, bytecode: {bc})")

    # 9. Add 'meta' table (dlng/slng)
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


def regenerate_webfonts():
    """Regenerate woff and woff2 from fixed TTF files."""
    print("\n" + "="*60)
    print("  Regenerating woff/woff2 from fixed TTF files")
    print("="*60)

    for ttf_path in TTF_FONTS:
        font = TTFont(ttf_path)
        name = os.path.basename(ttf_path).replace(".ttf", "")

        # woff
        font.flavor = 'woff'
        woff_path = ttf_path.replace("/ttf/", "/woff/").replace(".ttf", ".woff")
        font.save(woff_path)
        print(f"  Created: {woff_path}")

        # woff2
        font = TTFont(ttf_path)
        font.flavor = 'woff2'
        woff2_path = ttf_path.replace("/ttf/", "/woff2/").replace(".ttf", ".woff2")
        font.save(woff2_path)
        print(f"  Created: {woff2_path}")


def distribute_metadata():
    """Generate METADATA.pb and copy OFL.txt to all format directories."""
    print("\n" + "="*60)
    print("  Distributing METADATA.pb and OFL.txt")
    print("="*60)

    for subdir in ["ttf", "otf", "woff", "woff2"]:
        fonts_dir = os.path.join("fonts", subdir)
        if os.path.exists(fonts_dir):
            generate_metadata_pb(fonts_dir)
            copy_ofl_txt(fonts_dir)


if __name__ == "__main__":
    print("="*60)
    print("  FontBakery Post-Build Fix Script")
    print("="*60)

    # Fix all TTF fonts
    for font_path in TTF_FONTS:
        fix_all(font_path)

    # Regenerate web fonts from fixed TTF
    regenerate_webfonts()

    # Generate METADATA.pb and copy OFL.txt
    distribute_metadata()

    print(f"\n\n{'='*60}")
    print("  All fixes applied successfully!")
    print("  Run 'fontbakery check-googlefonts' to verify.")
    print(f"{'='*60}")