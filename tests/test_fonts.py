#!/usr/bin/env python3
"""Test font loading from core/resources/fonts/"""

from pathlib import Path
from zsys.resources import FONTS_DIR

print("=" * 60)
print("Testing core/resources/fonts/")
print("=" * 60)

# Test 1: Check directory exists
print(f"\n1. Fonts directory: {FONTS_DIR}")
print(f"   Exists: {FONTS_DIR.exists()}")

# Test 2: List fonts
fonts = list(FONTS_DIR.glob("*.ttf")) + list(FONTS_DIR.glob("*.ttc"))
print(f"\n2. Font files in root: {len(fonts)}")
for font in fonts:
    print(f"   - {font.name}")

# Test 3: Count all fonts including static/
all_fonts = list(FONTS_DIR.rglob("*.ttf")) + list(FONTS_DIR.rglob("*.ttc"))
print(f"\n3. Total fonts (including static/): {len(all_fonts)}")

# Test 4: Load a font with PIL
try:
    from PIL import ImageFont
    import io
    
    font_path = FONTS_DIR / "Roboto-VariableFont_wdth,wght.ttf"
    with open(font_path, 'rb') as f:
        font_data = f.read()
    
    font = ImageFont.truetype(io.BytesIO(font_data), 32)
    print(f"\n4. Font loading test: SUCCESS")
    print(f"   Loaded: {font_path.name}")
    print(f"   Font name: {font.getname()}")
    
except Exception as e:
    print(f"\n4. Font loading test: FAILED")
    print(f"   Error: {e}")

# Test 5: Check specific fonts used in modules
required_fonts = [
    "Roboto-VariableFont_wdth,wght.ttf",
    "CascadiaCodePL.ttf",
    "Times New Roman.ttf",
    "HelveticaNeue.ttc"
]

print(f"\n5. Required fonts check:")
for font_name in required_fonts:
    font_path = FONTS_DIR / font_name
    exists = font_path.exists()
    status = "✅" if exists else "❌"
    print(f"   {status} {font_name}")

print("\n" + "=" * 60)
print("All tests completed!")
print("=" * 60)
