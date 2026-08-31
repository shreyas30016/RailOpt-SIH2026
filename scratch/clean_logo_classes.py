import glob
import re

html_files = glob.glob('frontend/*.html')
for filepath in html_files:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Clean up sidebar logo
    content = re.sub(
        r'class="w-9 h-9 rounded-full bg-white p-0\.5 shadow-sm object-cover"',
        'class="w-10 h-10 rounded-full object-contain shrink-0"',
        content
    )

    # Clean up mobile topbar logo
    content = re.sub(
        r'class="w-8 h-8 rounded-full bg-white p-0\.5 object-cover"',
        'class="w-8 h-8 rounded-full object-contain shrink-0"',
        content
    )

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

print(f"Updated classes across {len(html_files)} HTML files!")
