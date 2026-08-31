import glob
import re

html_files = glob.glob('frontend/*.html')
print(f'Found {len(html_files)} html files')

for filepath in html_files:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Add favicon if missing
    if 'rel="icon"' not in content and '</head>' in content:
        content = content.replace('</head>', '    <link rel="icon" type="image/png" href="/assets/railopt_logo.png">\n</head>')

    # 2. Update logo image src and alt
    content = re.sub(
        r'src=["\']/assets/10_indian_railways_official_logo_ad892ab5\.png["\']',
        'src="/assets/railopt_logo.png"',
        content
    )
    content = re.sub(
        r'alt=["\']Indian Railways Official Logo["\']',
        'alt="RailOpt Logo"',
        content
    )

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

print('Successfully updated HTML files with RailOpt logo and favicon!')
