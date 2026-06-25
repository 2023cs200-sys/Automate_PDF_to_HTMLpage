import re
with open('output/html/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

for tid in ['vesak', 'editor', 'sinhala', 'builders', 'teaching']:
    start = html.find(f'id="topic-{tid}"')
    end = html.find('<section', start+20)
    if end == -1: end = start + 3000
    section = html[start:end]

    h3s = re.findall(r'<h3[^>]*>(.*?)</h3>', section)
    h4s = re.findall(r'<h4[^>]*>(.*?)</h4>', section)
    strongs = len(re.findall(r'<strong>', section))

    print(f'{tid}:')
    print(f'  h3: {len(h3s)} {h3s[:3]}')
    print(f'  h4: {len(h4s)} {h4s[:3]}')
    print(f'  strong tags: {strongs}')
    print()
