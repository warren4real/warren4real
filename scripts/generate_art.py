"""Generate profile artwork from the public GitHub contribution calendar."""
import datetime as dt
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
USERNAME = 'warren4real'

class Calendar(HTMLParser):
    def __init__(self):
        super().__init__()
        self.days = {}
        self.counts = {}
        self.tip = None
        self.text = ''
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get('data-date'):
            self.days[a['id']] = {'date': a['data-date'], 'level': int(a['data-level'])}
        if tag == 'tool-tip':
            self.tip = a.get('for')
            self.text = ''
    def handle_data(self, data):
        if self.tip:
            self.text += data
    def handle_endtag(self, tag):
        if tag == 'tool-tip' and self.tip:
            match = re.match(r'\s*([\d,]+) contributions?\b', self.text)
            if match:
                self.counts[self.tip] = int(match[1].replace(',', ''))
            elif self.text.strip().startswith('No contributions'):
                self.counts[self.tip] = 0
            self.tip = None
    def result(self):
        if len(self.days) < 350 or any(k not in self.counts for k in self.days):
            raise RuntimeError('Incomplete calendar response; preserving previous art.')
        days = sorted((dict(v, count=self.counts[k]) for k, v in self.days.items()), key=lambda d: d['date'])
        if any(not 0 <= d['level'] <= 4 for d in days):
            raise RuntimeError('Unexpected contribution level')
        return days

def svg(width, height, body, title):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img"><title>{html.escape(title)}</title><rect width="100%" height="100%" rx="14" fill="#0d1117"/>{body}</svg>\n'

def text(x, y, value, size=14, color='#c9d1d9'):
    return f'<text x="{x}" y="{y}" fill="{color}" font-family="monospace" font-size="{size}">{html.escape(str(value))}</text>'

def generate(days):
    palette = ['#161b22', '#0e4429', '#006d32', '#26a641', '#39d353']
    first = dt.date.fromisoformat(days[0]['date'])
    start = first - dt.timedelta(days=(first.weekday()+1)%7)
    body = text(25, 32, f'{USERNAME}@github ~ $ ./contributions.sh', 16, '#7ee787')
    last_month = None
    for day in days:
        date = dt.date.fromisoformat(day['date'])
        week, row = divmod((date-start).days, 7)
        x, y = 42+week*15, 68+row*15
        if date.month != last_month:
            body += text(x, 58, date.strftime('%b'), 11, '#8b949e')
            last_month = date.month
        body += f'<rect x="{x}" y="{y}" width="11" height="11" rx="2" fill="{palette[day["level"]]}"><title>{date}: {day["count"]} contributions</title><animate attributeName="opacity" values="0;1" dur="0.25s" begin="{(week+row)*0.018:.3f}s" fill="freeze"/></rect>'
    for row, label in [(1,'M'),(3,'W'),(5,'F')]:
        body += text(23, 77+row*15, label, 10, '#8b949e')
    total = sum(d['count'] for d in days)
    body += text(25, 207, f'{total:,} contributions · {days[0]["date"]} → {days[-1]["date"]}', 12)
    body += text(690, 207, 'Less', 10, '#8b949e')
    for i,c in enumerate(palette):
        body += f'<rect x="{720+i*15}" y="198" width="11" height="11" rx="2" fill="{c}"/>'
    body += text(800,207,'More',10,'#8b949e')
    (ROOT/'contrib-heatmap.svg').write_text(svg(860,230,body,'GitHub contribution calendar'), encoding='utf-8')
    pattern = [' # # ',' # # ',' ### ',' ### ','#####','#####','# # #']
    body = text(22,30,'$ cat avatar.txt',14,'#7ee787')
    for i,line in enumerate(pattern):
        chars = ''.join('@@@@' if c=='#' else '    ' for c in line)
        body += f'<text x="45" y="{75+i*23}" xml:space="preserve" fill="#7fb86b" font-family="monospace" font-size="22">{chars}<animate attributeName="opacity" values="0;1" dur="0.2s" begin="{i*0.1}s" fill="freeze"/></text>'
    body += text(45,260,USERNAME,16)
    (ROOT/'avi-ascii.svg').write_text(svg(370,290,body,'ASCII version of warren4real GitHub identicon'),encoding='utf-8')
    body = text(24,30,'$ whoami',14,'#7ee787')+text(24,77,USERNAME,25,'#f0f6fc')
    rows = [('Profile','github.com/'+USERNAME),('Builds','Swift · HTML'),('Style','Terminal-inspired'),('Activity','Updated daily')]
    for i,(label,value) in enumerate(rows):
        body += f'<g>{text(24,119+i*34,label,14,"#7ee787")}{text(133,119+i*34,value,14)}<animate attributeName="opacity" values="0;1" dur="0.3s" begin="{0.2+i*0.12}s" fill="freeze"/></g>'
    (ROOT/'info-card.svg').write_text(svg(490,290,body,'warren4real developer info card'),encoding='utf-8')

if __name__ == '__main__':
    request = urllib.request.Request(f'https://github.com/users/{USERNAME}/contributions', headers={'User-Agent':'profile-art-generator','Accept':'text/html'})
    with urllib.request.urlopen(request, timeout=30) as response:
        source = response.read().decode('utf-8')
    parser = Calendar()
    parser.feed(source)
    days = parser.result()
    generate(days)
    (ROOT/'data').mkdir(exist_ok=True)
    (ROOT/'data/contributions.json').write_text(json.dumps({'username':USERNAME,'days':days},indent=2)+'\n',encoding='utf-8')
    print(f'Generated artwork from {len(days)} days and {sum(d["count"] for d in days)} contributions.')
