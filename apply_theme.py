import re

with open('e:/New folder/carbon_credits/ai_engine_farm/agrichain_1.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Replace fonts
html = html.replace('href="https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap"', 'href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap"')
html = html.replace("--font: 'Syne', sans-serif;", "--font: 'Outfit', sans-serif;")

# CSS Variables Replacement (Earthy Forest Theme)
html = html.replace('--bg: #050d07;', '--bg: #EAE6DB; /* Muted oat background */')
html = html.replace('--bg2: #091508;', '--bg2: #F3F0E8;')
html = html.replace('--bg3: #0d1f0f;', '--bg3: #FFFFFF;')
html = html.replace('--green: #16ff6e;', '--green: #4C8259; /* Forest green */')
html = html.replace('--green2: #0aad4a;', '--green2: #65A175;')
html = html.replace('--green3: #073d1c;', '--green3: #A0C2A8;')
html = html.replace('--gold: #f5c518;', '--gold: #CC913A; /* Harvest gold */')
html = html.replace('--blue: #38bdf8;', '--blue: #558797;')
html = html.replace('--red: #ff4d4d;', '--red: #BD5B4A;')
html = html.replace('--teal: #2dd4bf;', '--teal: #64968C;')
html = html.replace('--text: #dffce8;', '--text: #213326; /* Dark slate green for text */')
html = html.replace('--muted: #4d7a5a;', '--muted: #6B8071;')
html = html.replace('--border: rgba(22, 255, 110, 0.11);', '--border: rgba(76, 130, 89, 0.2);')
html = html.replace('--glow: 0 0 28px rgba(22, 255, 110, 0.2);', '--glow: 0 4px 20px rgba(76, 130, 89, 0.1);')

# Replace neon rgbas in styles/inline (these are used in backgrounds, glows, charts)
# Neon green (22, 255, 110) to solid forest green (76, 130, 89)
html = re.sub(r'rgba\(22,\s*255,\s*110,', 'rgba(76, 130, 89,', html)

# Dark backgrounds used for cards (5, 13, 7) / (9, 21, 8) / (13, 31, 15) to solid white or cream 
# e.g rgba(255,255,255,
html = re.sub(r'rgba\(5,\s*13,\s*7,', 'rgba(255, 255, 255,', html)
html = re.sub(r'rgba\(9,\s*21,\s*8,', 'rgba(255, 255, 255,', html)
html = re.sub(r'rgba\(13,\s*31,\s*15,', 'rgba(243, 240, 232,', html)
html = re.sub(r'rgba\(7,\s*17,\s*9,', 'rgba(255, 255, 255,', html)

# Replace remaining text/SVG hardcoded colors to light theme palette
html = re.sub(r'#1ae870', '#83BF91', html) # Button highlight
html = re.sub(r'#16ff6e', '#4c8259', html) # SVG color green
html = re.sub(r'#0aad4a', '#65a175', html) # SVG color green 2
html = re.sub(r'#38bdf8', '#558797', html) # SVG blue
html = re.sub(r'#ff4d4d', '#bd5b4a', html) # SVG red
html = re.sub(r'#f5c518', '#cc913a', html) # SVG gold
html = re.sub(r'#4d7a5a', '#6b8071', html) # SVG muted

with open('e:/New folder/carbon_credits/ai_engine_farm/agrichain_1.html', 'w', encoding='utf-8') as f:
    f.write(html)
print('Theme applied successfully.')
