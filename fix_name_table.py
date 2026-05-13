#!/usr/bin/env python3
"""
Fix null bytes in name table for Google Fonts compliance.
"""
import os
from fontTools import ttLib

def fix_name_table_null_bytes(font_path):
    """Remove null bytes from name table entries."""
    font = ttLib.TTFont(font_path)

    fixed_count = 0
    for record in font['name'].names:
        if record.nameID in [1, 4, 16, 17]:  # Family, Full, Preferred, Compatible
            try:
                old_str = record.toUnicode()
                if '\x00' in old_str:
                    # Remove null bytes
                    new_str = old_str.replace('\x00', '')
                    # Re-encode and set
                    if record.isUnicode():
                        record.string = new_str
                    else:
                        record.string = new_str.encode('mac_roman') if record.platformID == 1 else new_str.encode('utf-16-be')
                    fixed_count += 1
                    print(f"  Fixed nameID {record.nameID}: {old_str[:30]}... -> {new_str[:30]}...")
            except Exception as e:
                print(f"  Warning: Could not process nameID {record.nameID}: {e}")

    if fixed_count > 0:
        font.save(font_path)
        print(f"  Saved: {os.path.basename(font_path)}")
    else:
        print(f"  No null bytes found in: {os.path.basename(font_path)}")

    return fixed_count

if __name__ == "__main__":
    import glob

    ttf_dir = "fonts/ttf"
    ttf_files = glob.glob(os.path.join(ttf_dir, "*.ttf"))

    print("Fixing null bytes in name tables...")
    total_fixed = 0
    for ttf in sorted(ttf_files):
        print(f"\n{os.path.basename(ttf)}:")
        total_fixed += fix_name_table_null_bytes(ttf)

    print(f"\nTotal entries fixed: {total_fixed}")