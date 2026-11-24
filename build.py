# ლექციების ბიბლიოთეკის ბილდი.
#   python3 build.py              → ყველა ლექცია + მთავარი გვერდი → რეპოს root (index.html, <კურსი>/<ლექცია>/)
#   python3 build.py efcore/03    → მხოლოდ ის ლექციები, რომელთა გზაც ამას შეიცავს (მთავარი გვერდის გარეშე)
#
# courses/<კურსი>/course.json — {"title", "order"}: ერთი კურსი = ერთი ჩანართი მთავარ გვერდზე (C#, EF Core, ASP.NET, SQL, DevOps)
# ლექციის საქაღალდე courses/<კურსი>/<NN-slug>/:
#   deck.html       სლაიდები
#   study.md        სტუდენტის კონსპექტი (study.en.md — ინგლისურად)
#   lecture.json    {"title", "why", "outcomes": [...], "review": [{"q", "a"}, ...], "starts_series": true?}
#   classwork.md    კლასში დავალება            homework.md    საშინაო (+ "## ამოხსნა" — ჩანს მხოლოდ შემდეგ ლექციაზე)
#   materials/      ფაილები ჩამოსატვირთად
#
# ყველა HTML გვერდი იშიფრება კოდით (.access-code ან LECTURES_CODE) — engine/gate.html კოდს ერთხელ ითხოვს.
#
# deck.html-ში ლექციის ნაწილები ცხადად იწერება (build მათ სლაიდებად აქცევს):
#   <lecture-review/>            გამეორება — წინა ლექციის review კითხვები
#   <lecture-homework-review/>   წინა ლექციის საშინაო + ამოხსნა
#   <lecture-intro/>             დღის თემა — why + outcomes
#   <lecture-classwork/>         კლასში დავალება (classwork.md)
#   <lecture-check/>             შევამოწმოთ — ამ ლექციის review კითხვები
#   <lecture-homework/>          საშინაო (homework.md, ამოხსნის გარეშე)
import base64, html, json, os, pathlib, re, shutil, sys
import markdown
from pygments.lexers import get_lexer_by_name
from pygments.token import STANDARD_TYPES
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

ROOT = pathlib.Path(__file__).parent
ENGINE = ROOT / 'engine'
# LECTURES_OUT=dist → separate output folder (Vercel); default: repo root (GitHub Pages serves main/root)
OUT = (ROOT / os.environ['LECTURES_OUT']).resolve() if os.environ.get('LECTURES_OUT') else ROOT
GENERATED = '.generated'   # list of folders build.py created — only these are ever deleted
CSS = (ENGINE / 'engine.css').read_text() + '\n' + (ENGINE / 'theme-light.css').read_text() + '\n' + (ENGINE / 'theme-dark.css').read_text()
JS = (ENGINE / 'engine.js').read_text()
TOKEN_CSS = '\n'.join(l for l in (ENGINE / 'theme-light.css').read_text().split('\n') if l.startswith('.code .'))
FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+Georgian:wght@400;600;700;800'
         '&family=JetBrains+Mono:wght@400;600;700;800&display=swap" rel="stylesheet">')
THEME_HEAD = ('<script>(()=>{const d=document.documentElement,K="lectures:theme";'
              'try{d.dataset.theme=localStorage.getItem(K)||"light"}catch(e){d.dataset.theme="light"}'
              'window.toggleTheme=()=>{const t=d.dataset.theme==="dark"?"light":"dark";d.dataset.theme=t;try{localStorage.setItem(K,t)}catch(e){}};'
              'document.addEventListener("click",e=>{const b=e.target.closest(".themebtn");if(b){b.blur();toggleTheme()}});'
              'addEventListener("storage",e=>{if(e.key===K)d.dataset.theme=e.newValue||"light"})})()</script>')
PAGE_THEME = (ENGINE / 'page-theme.css').read_text()
esc = html.escape

# ---------- access code ----------
# Every published HTML page is AES-GCM encrypted with a key derived from the access code; engine/gate.html asks for
# the code once, remembers it in the browser and decrypts the page. The code lives in .access-code (not in git).
CODE_FILE = ROOT / '.access-code'
PBKDF2_ITERATIONS = 200_000
_key = None

def access_key():
    global _key
    if _key is None:
        code = os.environ.get('LECTURES_CODE') or (CODE_FILE.read_text().strip() if CODE_FILE.exists() else '')
        if not code:
            sys.exit('⚠ კოდი არ არის: შექმენი .access-code ფაილი (ერთი ხაზი — კოდი) ან LECTURES_CODE ცვლადი')
        salt = os.urandom(16)
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=PBKDF2_ITERATIONS)
        _key = (salt, kdf.derive(code.encode()))
    return _key

LECTURER_FILE = ROOT / '.lecturer-code'

def lecturer_code():
    return os.environ.get('LECTURER_CODE') or (LECTURER_FILE.read_text().strip() if LECTURER_FILE.exists() else '')

def write_locked(path, page, code, key_name, heading):
    """ცალკე კოდით დაშიფრული გვერდი (ლექტორისთვის) — სტუდენტის გვერდები ამაზე არ არის დამოკიდებული"""
    salt, iv = os.urandom(16), os.urandom(12)
    key = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=PBKDF2_ITERATIONS).derive(code.encode())
    b = lambda x: base64.b64encode(x).decode()
    payload = {'s': b(salt), 'i': b(iv), 'n': PBKDF2_ITERATIONS, 'c': b(AESGCM(key).encrypt(iv, page.encode(), None))}
    gate = (ENGINE / 'gate.html').read_text().replace("const KEY = 'lectures:code';", f"const KEY = '{key_name}';")
    gate = gate.replace('<h1>ლექციები</h1>', f'<h1>{heading}</h1>').replace('<title>ლექციები</title>', f'<title>{heading}</title>')
    path.write_text(gate.replace('/*PAYLOAD*/{}', json.dumps(payload)))

def has_code():
    return bool(os.environ.get('LECTURES_CODE') or (CODE_FILE.exists() and CODE_FILE.read_text().strip()))

def write_page(path, page):
    if not has_code():   # კოდი არ არის → გვერდი ღიად ქვეყნდება
        path.write_text(page)
        return
    salt, key = access_key()
    iv = os.urandom(12)
    b = lambda x: base64.b64encode(x).decode()
    payload = {'s': b(salt), 'i': b(iv), 'n': PBKDF2_ITERATIONS, 'c': b(AESGCM(key).encrypt(iv, page.encode(), None))}
    path.write_text((ENGINE / 'gate.html').read_text().replace('/*PAYLOAD*/{}', json.dumps(payload)))

# ---------- code highlighting ----------
def _short(tt):
    while tt not in STANDARD_TYPES:
        tt = tt.parent
    return STANDARD_TYPES[tt]

def highlight(code, lang):
    lines = code.strip('\n').split('\n')
    ind = min((len(l) - len(l.lstrip()) for l in lines if l.strip()), default=0)
    code = '\n'.join(l[ind:] for l in lines)
    toks = [(None, code)] if lang in ('plain', 'text', '') else list(get_lexer_by_name(lang, stripnl=False, ensurenl=False).get_tokens(code))
    out = [[]]
    for tt, val in toks:
        cls = _short(tt) if tt is not None else ''
        for n, part in enumerate(val.split('\n')):
            if n:
                out.append([])
            if part:
                e = esc(part, quote=False)
                if lang.startswith('aspx') or lang == 'asp':
                    e = re.sub(r'(&lt;%[=#:]?|%&gt;)', r'<span class="asp-delim">\1</span>', e)
                out[-1].append(f'<span class="{cls}">{e}</span>' if cls else e)
    while out and not ''.join(out[-1]).strip():
        out.pop()
    return ''.join(f'<span class="ln">{"".join(l) or " "}</span>' for l in out)

def code_block(m):
    a = dict(re.findall(r'(\w+)="([^"]*)"', m.group(1)))
    idattr = f' id="{a["id"]}"' if 'id' in a else ''
    style = f' style="{a["style"]}"' if 'style' in a else ''
    ttl = f'<span class="ttl">{a["title"]}</span>' if 'title' in a else ''
    w = ' data-with' if 'data-with' in m.group(1) else ''
    cls = ('code ' + a.get('cls', '')).strip()
    return f'<pre class="{cls}"{idattr}{style}{w}>{ttl}<code>{highlight(m.group(2), a.get("lang", "plain"))}</code></pre>'

LIGHT_MAP = [  # dark-theme SVG colours → light theme (all decks use the light theme)
    ('#151935', '#ffffff'), ('#1b1f3d', '#f1ece3'), ('#0a0c16', '#fbf8f3'), ('#0d1024', '#ffffff'), ('#e8ecff', '#dbeafe'),
    ('#1d1640', '#f3effe'), ('#2a1d4d', '#ede7fd'), ('#0e2a33', '#eaf2fe'), ('#33240b', '#fef5e4'), ('#123321', '#eaf8ef'),
    ('#272c52', '#e6dfd2'), ('#353b6b', '#cfc6b6'),
    ('#22d3ee', '#2563eb'), ('#3b82f6', '#2563eb'), ('#22c55e', '#16a34a'), ('#f5a524', '#d97706'), ('#8b6cff', '#6d28d9'),
    ('#ec4899', '#db2777'), ('#f43f5e', '#dc2626'), ('#a78bfa', '#0d9488'),
    ('rgba(34,211,238,', 'rgba(37,99,235,'), ('rgba(59,130,246,', 'rgba(37,99,235,'), ('rgba(34,197,94,', 'rgba(22,163,74,'),
    ('rgba(245,165,36,', 'rgba(217,119,6,'), ('rgba(244,63,94,', 'rgba(220,38,38,'), ('rgba(167,139,250,', 'rgba(13,148,136,'),
    ('rgba(139,108,255,', 'rgba(109,40,217,'),
]

# ---------- study markdown ----------
LANG = 'ka'   # study text language: 'en' while rendering study.en.html (study.en.md, lecture.en.json, *.en.md)
def L(ka, en): return en if LANG == 'en' else ka
# Fenced blocks:  ```csharp Title   ```prompt Title   ```check (? კითხვა / = პასუხი)   ```terms (ტერმინი — ახსნა)   ```note / ```warn
def md_inline(text):
    h = markdown.markdown(text.strip(), extensions=['sane_lists'])
    return re.sub(r'^<p>(.*)</p>$', r'\1', h, flags=re.S)

def render_fence(kind, arg, body):
    body = body.strip('\n')
    if kind == 'prompt':
        return (f'<div class="prompt"><div class="ph"><span>🤖 {esc(arg or L("AI-სთვის — დააკოპირე და ჰკითხე", "For an AI — copy it and ask"))}</span>'
                f'<button class="copy" type="button">{L("კოპირება", "Copy")}</button></div><div class="pb">{esc(body)}</div></div>')
    if kind == 'check':
        # ? კითხვა · = პასუხი · ! ახსნა (არასავალდებულო — ლექტორისთვის: რატომ, დეტალები)
        items, cur, tgt = [], None, None
        for line in body.split('\n'):
            if line.startswith('?'):
                cur = [line[1:].strip(), [], []]; items.append(cur); tgt = None
            elif line.startswith('=') and cur:
                tgt = cur[1]; tgt.append(line[1:].strip())
            elif line.startswith('!') and cur:
                tgt = cur[2]; tgt.append(line[1:].strip())
            elif tgt is not None and line.strip():
                tgt.append(line.strip())
        def ans(a, w):
            if not w: return md_inline(" ".join(a))
            return (f'<div class="say"><b>💬 {L("უპასუხე", "Answer")}:</b> {md_inline(" ".join(a))}</div>'
                    f'<div class="why"><b>🧠 {L("ახსნა", "Why")}:</b> {md_inline(" ".join(w))}</div>')
        qs = ''.join(f'<details><summary>{md_inline(q)}</summary><div class="ans">{ans(a, w)}</div></details>' for q, a, w in items)
        return f'<div class="selfcheck"><div class="sh">✅ {L("შეამოწმე თავი", "Check yourself")} <small>{L("დაფიქრდი, მერე გახსენი პასუხი", "think first, then open the answer")}</small></div>{qs}</div>'
    if kind == 'terms':
        rows = [l.split('—', 1) for l in body.split('\n') if '—' in l]
        dl = ''.join(f'<dt>{md_inline(t)}</dt><dd>{md_inline(d)}</dd>' for t, d in rows)
        return f'<div class="terms"><div class="th">📘 {L("ტერმინები", "Terms")}</div><dl>{dl}</dl></div>'
    if kind in ('note', 'warn', 'tip'):
        ico = {'note': '💡', 'warn': '⚠️', 'tip': '👉'}[kind]
        return f'<div class="callout {kind}"><span class="ci">{ico}</span><div>{markdown.markdown(body, extensions=["sane_lists"])}</div></div>'
    lang = kind or 'plain'
    arg = arg.rstrip('!').strip()   # '!' only marks the block shown on the homework-review slide
    title = esc(arg) if arg else esc(lang)
    return (f'<div class="codebox"><div class="ch"><span>{title}</span><button class="copy" type="button">{L("კოპირება", "Copy")}</button></div>'
            f'<pre class="code"><code>{highlight(body, lang)}</code></pre></div>')

FENCE = re.compile(r'^```(\w*)[ \t]*([^\n]*)\n(.*?)^```[ \t]*$', re.M | re.S)

def md(text):
    lines = text.strip('\n').split('\n')
    ind = min((len(l) - len(l.lstrip()) for l in lines if l.strip()), default=0)
    text = '\n'.join(l[ind:] for l in lines)
    blocks = []
    def keep(m):
        blocks.append(render_fence(m.group(1), m.group(2).strip(), m.group(3)))
        return f'\n\n@@B{len(blocks) - 1}@@\n\n'
    text = FENCE.sub(keep, text)
    h = markdown.markdown(text, extensions=['tables', 'sane_lists'])
    return re.sub(r'<p>@@B(\d+)@@</p>|@@B(\d+)@@', lambda m: blocks[int(m.group(1) or m.group(2))], h)

def md_doc(path):
    """# სათაური / შესავალი / ## სექციები → {'title', 'intro', 'parts': [(heading, md)]}"""
    if not path.exists():
        return None
    t = path.read_text()
    title = re.search(r'^# (.+)$', t, re.M).group(1).strip()
    t = re.sub(r'^# .+\n', '', t, count=1, flags=re.M)
    chunks = re.split(r'^## (.+)$', t, flags=re.M)
    return {'title': title, 'intro': chunks[0].strip(), 'parts': [(chunks[i].strip(), chunks[i + 1].strip()) for i in range(1, len(chunks), 2)]}

def part(doc, key):
    return next((b for h, b in doc['parts'] if key in h), '')

def slide_md(text):   # markdown → slide markup (deck classes)
    h = markdown.markdown(text, extensions=['sane_lists']).replace('<code>', '<code class="i">')
    return h.replace('<ul>', '<ul class="clean small">').replace('<ol>', '<ol class="clean small">')

def first_code(text):   # the code fence marked with a trailing "!" in its title, else the first code fence
    fences = [m for m in FENCE.finditer(text) if m.group(1) not in ('prompt', 'check', 'terms', 'note', 'warn', 'tip')]
    m = next((f for f in fences if f.group(2).strip().endswith('!')), fences[0] if fences else None)
    return (m.group(1), m.group(2).strip().rstrip('!').strip(), m.group(3)) if m else None

# ---------- generated slides ----------
def qa_rows(review):
    return ''.join(f'<div class="qa"><span class="n">{n}</span><span class="q">{md_inline(r["q"]).replace("<code>", "<code class=\"i\">")}</span>'
                   f'<span class="a step">{md_inline(r["a"]).replace("<code>", "<code class=\"i\">")}</span></div>' for n, r in enumerate(review, 1))

def check_md(review):
    return '```check\n' + '\n'.join(f'? {r["q"]}\n= {r["a"]}' for r in review) + '\n```'

def gen_review(prev):
    pm, num = prev['meta'], prev['num']
    return f'''<section class="slide" data-section="გამეორება">
  <div class="kicker">გამეორება · ლექცია {num}</div>
  <h2>გავიხსენოთ: <span class="grad">{esc(pm["title"])}</span></h2>
  {qa_rows(pm["review"])}
</section>'''

def gen_homework_review(prev):
    hw = prev['homework']
    sol = part(hw, 'ამოხსნ')
    code = first_code(sol)
    if code and code[2].strip('\n').count('\n') >= 20:
        print(f'  ⚠ ლექცია {prev["num"]}-ის ამოხსნის კოდი სლაიდზე {code[2].strip(chr(10)).count(chr(10)) + 1} ხაზია — ≤20 ჯობია (მონიშნე სხვა ბლოკი "!"-ით)')
    right = (f'<code-block lang="{code[0]}" cls="sm" title="{esc(code[1])}">\n{code[2]}</code-block>' if code else '')   # code-block escapes itself
    return f'''<section class="slide" data-section="საშინაოს განხილვა">
  <div class="kicker">🏠 საშინაოს განხილვა · ლექცია {prev["num"]}</div>
  <h2>{esc(hw["title"])}</h2>
  <div class="grid2" style="grid-template-columns:1fr 1.25fr;align-items:start;gap:30px">
    <div class="card accent" style="--a:var(--mvc)"><h3><span class="ico">📝</span>რა უნდა გაგეკეთებინათ</h3>{slide_md(part(hw, "მოთხოვნ"))}</div>
    <div class="step">{right}</div>
  </div>
  <div class="callout step mt" data-with style="--a:var(--api)">შეადარეთ თქვენს კოდს. რა გამოგივიდათ სხვანაირად — და რატომ?</div>
</section>'''

def gen_intro(meta):
    outs = ''.join(f'<li>{md_inline(o).replace("<code>", "<code class=\"i\">")}</li>' for o in meta['outcomes'])
    return f'''<section class="slide" data-section="დღის თემა">
  <div class="kicker">დღის თემა</div>
  <h2><span class="grad">{esc(meta["title"])}</span></h2>
  <div class="grid2" style="grid-template-columns:1fr 1fr;align-items:start;gap:40px">
    <div class="card accent" style="--a:var(--asp)"><h3><span class="ico">🤔</span>რატომ გჭირდებათ</h3><p class="small">{md_inline(meta["why"]).replace("<code>", "<code class=\"i\">")}</p></div>
    <div class="card accent" style="--a:var(--mvc)"><h3><span class="ico">🎯</span>ლექციის ბოლოს შეძლებთ</h3><ul class="clean small">{outs}</ul></div>
  </div>
</section>'''

def gen_task(doc, section, kicker, ico, color, footer):
    bonus = part(doc, 'ბონუს')
    done = part(doc, 'მზადაა')
    steps = part(doc, 'ნაბიჯ') or part(doc, 'მოთხოვნ')
    right = f'<div class="card accent" style="--a:var(--asp)"><h3><span class="ico">⭐</span>ბონუსი</h3>{slide_md(bonus)}</div>' if bonus else ''
    cols = '1.5fr 1fr' if bonus else '1fr'
    return f'''<section class="slide" data-section="{section}">
  <div class="kicker">{kicker}</div>
  <h2>{esc(doc["title"])}</h2>
  <div class="grid2" style="grid-template-columns:{cols};align-items:start">
    <div class="card accent" style="--a:{color}">
      <h3><span class="ico">{ico}</span>{md_inline(doc["intro"]).replace("<code>", "<code class=\"i\">") if doc["intro"] else "დავალება"}</h3>
      {slide_md(steps)}
      {f'<p class="tiny" style="margin-top:14px">✓ მზადაა, როცა: {md_inline(done)}</p>' if done else ''}
    </div>
    {right}
  </div>
  <div class="callout mt" style="--a:var(--api)">{footer}</div>
</section>'''

def gen_check(meta):
    return f'''<section class="slide" data-section="შეჯამება">
  <div class="kicker">შევამოწმოთ</div>
  <h2>{len(meta["review"])} კითხვა</h2>
  {qa_rows(meta["review"])}
</section>'''

def expand(src, meta, ldir, prev):
    gen = {
        'lecture-review': lambda: gen_review(prev) if prev and prev['meta'].get('review') else None,
        'lecture-homework-review': lambda: gen_homework_review(prev) if prev and prev['homework'] else None,
        'lecture-intro': lambda: gen_intro(meta),
        'lecture-classwork': lambda: gen_task(md_doc(ldir / 'classwork.md'), 'პრაქტიკა', '🧑‍💻 თქვენ აკეთებთ · კლასში', '📝', 'var(--mvc)',
                                              'წესი: <b>ჯერ ცდი თვითონ</b> → გვერდით მჯდომს ჰკითხე → მერე მე'),
        'lecture-check': lambda: gen_check(meta),
        'lecture-homework': lambda: gen_task(md_doc(ldir / 'homework.md'), 'საშინაო', '🏠 საშინაო დავალება', '🏠', 'var(--net)',
                                             'შემდეგი ლექციის დასაწყისში ამ დავალებას <b>ერთად განვიხილავთ</b>'),
    }
    problems = []
    if '<lecture-intro/>' in src:   # new-format lecture: every part is required
        need = ['lecture-intro', 'lecture-classwork', 'lecture-check', 'lecture-homework']
        if prev and prev['meta'].get('review'): need.append('lecture-review')
        if prev and prev['homework']: need.append('lecture-homework-review')
        problems += [f'<{n}/> აკლია' for n in need if f'<{n}/>' not in src]
        for f in ('classwork.md', 'homework.md'):
            if not (ldir / f).exists(): problems.append(f'{f} აკლია')
        for k in ('why', 'outcomes', 'review'):
            if not meta.get(k): problems.append(f'lecture.json: "{k}" აკლია')
        if problems:
            return src, problems
    for tag, fn in gen.items():
        if f'<{tag}/>' in src:
            out = fn()
            src = src.replace(f'<{tag}/>', out or '')
    return src, problems

# ---------- one lecture ----------
HOME_CSS = '''#home{position:fixed;left:12px;top:10px;z-index:41;font:600 13px var(--mono);color:var(--muted);text-decoration:none;
padding:6px 10px;border-radius:8px;opacity:0;transition:opacity .25s}
#home:hover,#home:focus-visible{opacity:1;background:rgba(0,0,0,.05)}
:fullscreen #home{display:none}
#studybtn{position:fixed;right:16px;top:12px;z-index:41;display:flex;align-items:center;gap:6px;font:700 14px var(--font);color:#fff;
background:var(--net);border:0;border-radius:10px;padding:7px 13px;cursor:pointer;opacity:.9;box-shadow:0 4px 14px rgba(109,40,217,.25)}
#studybtn:hover{opacity:1}#studybtn kbd{font:600 11px var(--mono);background:rgba(255,255,255,.22);border-radius:5px;padding:1px 6px}
#lectbtn{position:fixed;right:170px;top:12px;z-index:41;display:flex;align-items:center;gap:6px;font:700 14px var(--font);color:var(--ink2);
background:var(--card);border:1px solid var(--line2);border-radius:10px;padding:7px 11px;cursor:pointer;opacity:.85}
#lectbtn:hover,#themebtn:hover,#langbtn:hover{opacity:1}
#themebtn,#langbtn{position:fixed;top:12px;z-index:41;font:700 14px var(--font);color:var(--ink2);background:var(--card);border:1px solid var(--line2);
border-radius:10px;padding:7px 10px;cursor:pointer;opacity:.85;line-height:1.25}
#themebtn{right:170px}#langbtn{right:222px;font-family:var(--mono)}
#themebtn{right:16px}#langbtn{right:68px}#help{right:124px;top:20px}
.themebtn .d{display:none}html[data-theme=dark] .themebtn .l{display:none}html[data-theme=dark] .themebtn .d{display:inline}
:fullscreen #themebtn,:fullscreen #langbtn{opacity:0}:fullscreen #themebtn:hover,:fullscreen #langbtn:hover{opacity:1}#lectbtn kbd{font:600 11px var(--mono);background:var(--bg2);border-radius:5px;padding:1px 6px}'''

def heading(sl):
    h = re.search(r'<h[12][^>]*>(.*?)</h[12]>', sl, re.S)
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', h.group(1)))).strip() if h else ''

# ---------- EN version of a deck ----------
# deck.en.json: {"ქართული ფრაგმენტი": "English", …, "_html": [[from, to], …], "_slides": {"7": {"ფრაგმენტი": "…"}}}
# ფრაგმენტი = ტეგებს შორის ტექსტი (trim), data-section/title/… ატრიბუტი ან სკრიპტის სტრიქონი. აკლია → build აჩვენებს.
GEO = re.compile(r'[Ⴀ-ჿ]')

def translate_deck(src, ldir):
    f = ldir / 'deck.en.json'
    if not f.exists():
        return None
    tmap = json.loads(f.read_text())
    html_over, per_slide = tmap.pop('_html', []), tmap.pop('_slides', {})
    tmap.pop('_note', None)
    missing = []
    def tr(t, m):
        key = t.strip()
        if not GEO.search(key): return t
        v = m.get(key, tmap.get(key))
        if v is None:
            missing.append(key); return t
        lead, trail = t[:len(t) - len(t.lstrip())], t[len(t.rstrip()):]
        if v[:1] in '.,:;!?)': lead = ''   # „ ხედავს.“ → „.“ — წინა ჰარი პუნქტუაციის წინ არ რჩება
        return lead + v + trail
    def tr_markup(part, m):
        part = re.sub(r'>([^<]+)<', lambda x: '>' + tr(x.group(1), m) + '<', part)
        return re.sub(r'((?:data-section|title|placeholder|aria-label|data-t|data-l)=")([^"]*)(")', lambda x: x.group(1) + tr(x.group(2), m) + x.group(3), part)
    for a, b in html_over:
        src = src.replace(a, b)
    out, n = [], 0
    for chunk in re.split(r'(<script.*?</script>|<style.*?</style>|<section class="slide.*?</section>)', src, flags=re.S):
        if chunk.startswith('<style'):
            out.append(chunk)
        elif chunk.startswith('<script'):
            out.append(re.sub(r"'([^'\n]*)'", lambda x: "'" + tr(x.group(1), {}) + "'", chunk))
        elif chunk.startswith('<section'):
            n += 1
            out.append(tr_markup(chunk, per_slide.get(str(n), {})))
        else:
            out.append(tr_markup(chunk, {}))
    if missing:
        print(f'  ⚠ EN: {len(set(missing))} ფრაგმენტს თარგმანი აკლია ({ldir.name}/deck.en.json):')
        for k in list(dict.fromkeys(missing))[:12]: print('     ', k[:90])
    return ''.join(out)

def deck_page(src, title, has_study, has_lect, lang, has_en):
    en = lang == 'en'
    other = ('index.html', 'KA', 'ქართული ვერსია') if en else ('index.en.html', 'EN', 'English version')
    lang_btn = f'<button id="langbtn" type="button" data-href="{other[0]}" title="{other[2]}">{other[1]}</button>' if has_en else ''
    study_btn = (f'<button id="studybtn" type="button" title="კონსპექტი ცალკე ჩანართში — სლაიდებს მიჰყვება">📖 {"Notes" if en else "კონსპექტი"} <kbd>P</kbd></button>'
                 if has_study else '')
    return f'''<!doctype html>
<html lang="{lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
{FONTS}{THEME_HEAD}
<style>{CSS}
{HOME_CSS}</style></head>
<body{' data-study="1"' if has_study else ''}{' data-lect="1"' if has_lect else ''}>
<a id="home" href="../../" title="{"All lectures" if en else "ყველა ლექცია"}">← {"Lectures" if en else "ლექციები"}</a><button id="themebtn" class="themebtn" type="button" title="{"Light / dark theme" if en else "ღია / მუქი თემა"} (T)"><span class="l">🌙</span><span class="d">☀️</span></button>{lang_btn}
<div id="stage"><div id="deck">
{src}
<div id="hud"><span class="sec"></span><span class="dots"></span><span class="num"></span></div><div id="bar"></div>
</div></div>
<div id="overview"></div>
<div id="help">← → · F</div>
<script>{JS}</script>
</body></html>'''

def build_lecture(course, cdir, ldir, meta, prev):
    global LANG
    src, problems = expand((ldir / 'deck.html').read_text(), meta, ldir, prev)
    num = int(ldir.name.split('-', 1)[0])
    title = f'{course["title"]} · {num} — {meta["title"]}'   # also the BroadcastChannel key: must be unique
    out = OUT / cdir.name / ldir.name
    if problems:
        print(f'  {cdir.name}/{ldir.name}: ⚠ ' + '; '.join(problems))
        return None, problems

    slides = re.findall(r'<section class="slide.*?</section>', src, re.S)
    src = re.sub(r'\n?[ \t]*<aside class="(?:study|study-en|notes)">.*?</aside>', '', src, flags=re.S)   # old inline notes are never published
    for a, b in LIGHT_MAP:
        src = src.replace(a, b).replace(a.upper(), b)
    src = re.sub(r'<code-block([^>]*)>(.*?)</code-block>', code_block, src, flags=re.S)
    has_study = (ldir / 'study.md').exists()

    out.mkdir(parents=True, exist_ok=True)
    has_lect = (ldir / 'lecturer.md').exists()
    en_src = translate_deck(src, ldir)
    write_page(out / 'index.html', deck_page(src, title, has_study, has_lect, 'ka', bool(en_src)))
    if en_src:
        write_page(out / 'index.en.html', deck_page(en_src, title, has_study, has_lect, 'en', True))
    else:
        (out / 'index.en.html').unlink(missing_ok=True)
    for stale in ('script.html', 'study.html', 'study.en.html', 'lecturer.html'):
        (out / stale).unlink(missing_ok=True)

    materials = []
    if (ldir / 'materials').is_dir():
        shutil.copytree(ldir / 'materials', out / 'materials', dirs_exist_ok=True)
        materials = sorted(p.name for p in (ldir / 'materials').iterdir() if p.is_file())
    has_study_en = False
    if has_study:
        write_notes(out, course, meta, num, ldir, 'ka')
        if (ldir / 'study.en.md').exists():
            LANG = 'en'
            try:
                write_notes(out, course, meta, num, ldir, 'en')
                has_study_en = True
            finally:
                LANG = 'ka'
    has_lecturer = write_lecturer(out, course, meta, num, title, ldir)
    print(f'  {cdir.name}/{ldir.name}: {len(slides)} slides')
    return {'num': num, 'slug': ldir.name, 'title': meta['title'], 'slides': len(slides), 'materials': materials, 'study': has_study,
            'classwork': (ldir / 'classwork.md').exists(), 'homework': (ldir / 'homework.md').exists(), 'quiz': len(meta.get('quiz', [])), 'lecturer': has_lecturer, 'study_en': has_study_en, 'deck_en': (out / 'index.en.html').exists()}, []

def lect_heading(h):
    """'3 · ტოკენები · 15 წთ · 16–20' → (num, title, minutes, (from, to))"""
    num, mins, slides, rest = None, None, None, []
    for i, x in enumerate(p.strip() for p in h.split(' · ')):
        if i == 0 and x.isdigit(): num = int(x)
        elif re.fullmatch(r'(\d+) წთ', x): mins = int(x.split()[0])
        elif re.fullmatch(r'\d+(?:[–-]\d+)?', x):
            a, _, b = x.replace('–', '-').partition('-'); slides = (int(a), int(b or a))
        else: rest.append(x)
    return num, ' · '.join(rest), mins, slides

def lect_split(text):
    """### ბლოკებად: [(None, intro), (heading, body), …]"""
    ch = re.split(r'^### (.+)$', text, flags=re.M)
    return [(None, ch[0])] + [(ch[i].strip(), ch[i + 1]) for i in range(1, len(ch), 2)]

# ლექტორის გვერდი. lecturer.md:
#   ## 🎯 მთავარი                          ზოგადი ბარათი (### 📌 / ### ✅ მომზადება — ჩეკლისტი)
#   ## 3 · ტოკენები · 11 წთ · 12–16        თემა: ნომერი · სათაური · დრო · სლაიდები → ლექციის გეგმაში ჩადის
#   - სათქმელი (სია ბარათის თავში)
#   ### 🙋 ჰკითხე / ### 💡 მაგალითი / ### 🗣️ … / ### 📋 …   ხილული ბლოკები
#   ### 🆘 თუ ვერ გაიგეს                    დაკეცილი
# ბოლოს ავტომატურად: კლასის დავალების და საშინაოს სრული ტექსტი (ამოხსნით), შემოწმების კითხვები — დაკეცილი.
PLAN_KINDS = {'🙋': 'ask', '💡': 'ex', '🗣': 'how', '📌': 'must', '✅': 'prep', '📋': 'plain'}

def write_lecturer(out, course, meta, num, deck_title, ldir):
    """lecturer.md (+ დავალებები, კითხვები) → lecturer.html, ცალკე კოდით"""
    src = ldir / 'lecturer.md'
    code = lecturer_code()
    if not src.exists():
        return False
    if not code:
        print('  ⚠ ლექტორის გვერდი არ აიწყო: .lecturer-code ფაილი ან LECTURER_CODE ცვლადი არ არის')
        return False
    t = re.sub(r'^# .+\n', '', src.read_text(), count=1, flags=re.M)
    chunks = re.split(r'^## (.+)$', t, flags=re.M)
    parts = []
    for i in range(1, len(chunks), 2):
        n, title, mins, slides = lect_heading(chunks[i].strip())
        html_ = []
        for h, b in lect_split(chunks[i + 1]):
            if not b.strip(): continue
            if h is None:
                html_.append(md(b))
            elif h.startswith('🆘'):
                html_.append(f'<details class="blk"><summary>{esc(h)}</summary><div>{md(b)}</div></details>')
            else:
                k = next((v for e, v in PLAN_KINDS.items() if h.startswith(e)), 'plain')
                html_.append(f'<div class="blk k-{k}"><div class="bl">{esc(h)}</div><div>{md(b)}</div></div>')
        parts.append({'num': n, 'title': title, 'mins': mins, 'slides': slides, 'html': ''.join(html_)})
    clock = 0
    for p in parts:
        if p['mins']: p['start'] = clock; clock += p['mins']
    total = clock
    fmt = lambda m: f'{m // 60}:{m % 60:02d}'
    rows, cards = [], []
    for i, p in enumerate(parts, 1):
        pid, badge, title = f'p-{i}', str(p['num']) if p['num'] else '', p['title']
        em = re.match(r'^([^\w\s]+)\s+(.+)$', title)
        if not badge and em: badge, title = em.group(1), em.group(2)
        meta_bits, attrs = [], ''
        if p['mins']:
            meta_bits.append(f'<span class="tm">⏱ {p["mins"]} წთ · {fmt(p["start"])}–{fmt(p["start"] + p["mins"])}</span>')
            attrs += f' data-start="{p["start"]}" data-min="{p["mins"]}"'
        sl = ''
        if p['slides']:
            a, b = p['slides']
            sl = f'სლაიდ{"ები " + str(a) + "–" + str(b) if b != a else "ი " + str(a)}'
            meta_bits.append(f'<a class="sl" href="index.html#/{a}" target="_blank" data-go="{a}">▶ {sl}</a>')
            attrs += f' data-from="{a}" data-to="{b}"'
        if p['mins']:
            rows.append(f'<a class="row{" brk" if not p["num"] and badge == "☕" else ""}" href="#{pid}"><span class="t">{fmt(p["start"])}–{fmt(p["start"] + p["mins"])}</span>'
                        f'<span class="n">{badge}</span><span>{esc(title)}</span><span class="s">{sl}</span></a>')
        body = f'<div class="cb">{p["html"]}</div>' if p['html'].strip() else ''
        cards.append(f'<section class="card" id="{pid}"{attrs}><header><span class="num">{badge or "•"}</span><h2>{esc(title)}</h2>'
                     f'<div class="meta">{"".join(meta_bits)}</div></header>{body}</section>')
    plan = ''
    if rows:
        plan = (f'<div class="plan-t"><div class="ph"><b>🗓️ ლექციის გეგმა</b><span>{total} წთ</span></div>{"".join(rows)}'
                f'<div class="foot">ლექცია 120 წთ: დაწყება ~5–10 წთ აგვიანებს, 5 წთ ადრე ამთავრებ. დარჩენილი ~{max(0, 120 - 10 - 5 - total)} წთ რეზერვია: '
                'სუსტ ჯგუფთან კითხვებსა და 🆘-ზე იხარჯება, ძლიერთან ბოლოს „⭐ თუ დრო დარჩა“.</div></div>')
    # გეგმა პირველი ზოგადი ბარათის (🎯) შემდეგ
    first_timed = next((k for k, p in enumerate(parts) if p['mins']), len(parts))
    cards.insert(first_timed, plan)
    def doc_md(path):
        return re.sub(r'^# (.+)$', r'### \1', path.read_text(), count=1, flags=re.M).replace('\n## ', '\n#### ')
    mat = []
    if (ldir / 'classwork.md').exists(): mat.append(('📝 კლასის დავალება — სტუდენტის ტექსტი', doc_md(ldir / 'classwork.md')))
    if (ldir / 'homework.md').exists(): mat.append(('🏠 საშინაო — ტექსტი და ამოხსნა', doc_md(ldir / 'homework.md')))
    if meta.get('review'): mat.append(('❓ შემოწმების კითხვები — პასუხებით', check_md(meta['review'])))
    if mat:
        cards.append('<section class="card"><header><span class="num">📎</span><h2>სრული ტექსტები</h2></header><div class="cb">'
                     + ''.join(f'<details class="mat"><summary>{esc(h)}</summary>{md(b)}</details>' for h, b in mat) + '</div></section>')
    page = (ENGINE / 'lecturer.html').read_text()
    for k, v in {'{{TITLE}}': esc(meta['title']), '{{COURSE}}': esc(course['title']), '{{NUM}}': str(num),
                 '{{DECK_TITLE_JSON}}': json.dumps(deck_title, ensure_ascii=False), '{{BODY}}': '\n'.join(cards), '{{TOTAL}}': str(total),
                 '{{CODE_BTN}}': (f'<a class="btn ico" href="../project/{num:02d}.html" target="_blank" title="ლექციის კოდი" aria-label="ლექციის კოდი">💻</a>'
                                  if (ldir.parent / 'project' / f'{num:02d}.md').exists() else ''),
                 '{{TOKEN_CSS}}': TOKEN_CSS, '{{FONTS}}': FONTS + THEME_HEAD, '{{PAGE_THEME}}': PAGE_THEME}.items():
        page = page.replace(k, v)
    write_locked(out / 'lecturer.html', page, code, 'lectures:lecturer', 'ლექტორის გვერდი')
    return True

# კონსპექტი (study.md, study.en.md):
#   ## ⚡ მთავარი                      5 მთავარი აზრი (სია)
#   ## 3 · ტოკენები · 12–16            თემა: ნომერი · სათაური · სლაიდები; ტექსტი, ```check, ```terms, კოდი
# ჩანართები: მთავარი · თემები · დავალებები (homework.md, classwork.md — ამოხსნის გარეშე) · ტესტი (lecture.json → quiz)
def write_notes(out, course, meta, num, ldir, lang):
    en = lang == 'en'
    if en:
        meta = {**meta, **meta['_en'], 'quiz': [{**k, **e} for k, e in zip(meta.get('quiz', []), meta['_en'].get('quiz', []))]}
    sfx = '.en' if en else ''
    deck = f'index{sfx}.html' if (out / f'index{sfx}.html').exists() else 'index.html'
    text = re.sub(r'^# .+\n', '', (ldir / f'study{sfx}.md').read_text(), count=1, flags=re.M)
    ch = re.split(r'^## (.+)$', text, flags=re.M)
    summary, topics, raw = [], [], ''
    for i in range(1, len(ch), 2):
        h, body = ch[i].strip(), ch[i + 1]
        if h.startswith('⚡'):
            summary = [l[2:].strip() for l in body.strip().split('\n') if l.startswith('- ')]
            continue
        n, title, _, slides = lect_heading(h)
        raw += body
        sl = ''
        if slides:
            a, b = slides
            sl = f'<a class="sl" href="{deck}#/{a}" target="_blank">▶ {L("სლაიდ", "Slide")}{(L("ები ", "s ") + f"{a}–{b}") if b != a else " " + str(a)}</a>'
        topics.append(f'<section class="topic"><header><span class="num">{n or "•"}</span><h2>{esc(title)}</h2>{sl}</header><div class="tb">{md(body)}</div></section>')
    mins = max(1, round(len(re.findall(r'\w+', raw)) / 110))   # text and code together
    def task(name):
        p = ldir / f'{name}{sfx}.md'
        if not p.exists(): return ''
        s = re.split(r'^## (?:ამოხსნა|Solution)\b', p.read_text(), flags=re.M)[0]
        s = re.sub(r'^# (.+)$', r'### \1', s, count=1, flags=re.M).replace('\n## ', '\n#### ')
        return f'<div class="box task">{md(s)}</div>'
    hw, cw = task('homework'), task('classwork')
    quiz = meta.get('quiz', [])
    qhtml = re.sub(r'href="#s-(\d+)"', lambda m: f'href="{deck}#/{m.group(1)}" target="_blank"', render_quiz_items(quiz)) if quiz else ''
    links = ''.join(f'<li><a href="{esc(r["url"])}" target="_blank" rel="noopener">{esc(r["title"])}</a>'
                    f'{" — " + md_inline(r["note"]) if r.get("note") else ""}</li>' for r in meta.get('resources', []))
    path = [L(f'<li><a href="{deck}" target="_blank">ნახე პრეზენტაცია</a>: სლაიდები ლექციის მთელ გზას აჩვენებს</li>',
              f'<li><a href="{deck}" target="_blank">Go through the presentation</a>: the slides show the whole lecture</li>'),
            L(f'<li><a href="#topics">წაიკითხე თემები</a>: ~{mins} წთ, თითოს ბოლოს „შეამოწმე თავი“</li>',
              f'<li><a href="#topics">Read the topics</a>: ~{mins} min, each ends with “Check yourself”</li>')]
    if quiz: path.append(L(f'<li><a href="#quiz">გაიარე ტესტი</a>: {len(quiz)} კითხვა</li>', f'<li><a href="#quiz">Take the quiz</a>: {len(quiz)} questions</li>'))
    if hw or cw: path.append(L('<li><a href="#tasks">გააკეთე დავალებები</a></li>', '<li><a href="#tasks">Do the assignments</a></li>'))
    main = (f'<div class="box"><h2>🎯 {L("ამ ლექციის შემდეგ შეძლებ", "After this lecture you can")}</h2><ul>{"".join(f"<li>{md_inline(x)}</li>" for x in meta.get("outcomes", []))}</ul></div>'
            + (f'<div class="box key"><h2>⚡ {L("მთავარი", "Key points")}</h2><ol>{"".join(f"<li>{md_inline(x)}</li>" for x in summary)}</ol></div>' if summary else '')
            + f'<div class="box"><h2>📍 {L("ლექცია გააცდინე?", "Missed the lecture?")}</h2><ol class="path">{"".join(path)}</ol></div>'
            + (f'<div class="box"><h2>🔗 {L("ბმულები", "Links")}</h2><ul>{links}</ul></div>' if links else ''))
    tabs = [('main', L('მთავარი', 'Overview'), '', main),
            ('topics', L('თემები', 'Topics'), str(len(topics)), ''.join(topics))]
    if hw or cw:
        tabs.append(('tasks', L('დავალებები', 'Assignments'), '',
                     (f'<h2>🏠 {L("საშინაო", "Homework")}</h2>{hw}' if hw else '') + (f'<h2>📝 {L("კლასის დავალება", "Classwork")}</h2>{cw}' if cw else '')))
    if quiz:
        tabs.append(('quiz', L('ტესტი', 'Quiz'), str(len(quiz)), f'<p class="hint">{L("აირჩიე პასუხი და მაშინვე ნახავ, სწორია თუ არა და რატომ.", "Pick an answer and you will see right away whether it is correct and why.")}</p>{qhtml}'))
    tabs_html = ''.join(f'<button type="button" data-t="{k}">{esc(name)}{f"<small>{c}</small>" if c else ""}</button>' for k, name, c, _ in tabs)
    panels = ''.join(f'<section class="panel" id="tab-{k}">{body}</section>' for k, _, _, body in tabs)
    has_en = (ldir / 'study.en.md').exists()
    langbtn = (f'<a class="btn lang" href="{"study.html" if en else "study.en.html"}" title="{"ქართულად" if en else "English"}">{"KA" if en else "EN"}</a>' if has_en else '')
    i18n = {'copy': L('კოპირება', 'Copy'), 'copied': L('✓ დაკოპირდა', '✓ Copied'),
            'review': L('გაიმეორე ეს კითხვები: ', 'Review these questions: '), 'allright': L('ყველაფერი სწორია! 🎉', 'All correct! 🎉')}
    page = (ENGINE / 'study.html').read_text()
    if en:
        page = page.replace('content:"✓ სწორია."', 'content:"✓ Correct."').replace('content:"✗ არა."', 'content:"✗ No."')
    for k, v in {'{{LANG}}': lang, '{{TITLE}}': esc(meta['title']), '{{COURSE}}': esc(course.get('title_en', course['title']) if en else course['title']),
                 '{{NUM}}': str(num), '{{DECK}}': deck, '{{TABS}}': tabs_html, '{{PANELS}}': panels, '{{LANGBTN}}': langbtn,
                 '{{I18N}}': json.dumps(i18n, ensure_ascii=False), '{{T_NOTES}}': L('კონსპექტი', 'study notes'), '{{T_BACK}}': L('← ლექციები', '← Lectures'),
                 '{{T_LECTURE}}': L('ლექცია', 'Lecture'), '{{T_THEME}}': L('ღია / მუქი თემა', 'Light / dark theme'), '{{T_DECK}}': L('პრეზენტაცია', 'Presentation'),
                 '{{TOKEN_CSS}}': TOKEN_CSS, '{{FONTS}}': FONTS + THEME_HEAD, '{{PAGE_THEME}}': PAGE_THEME}.items():
        page = page.replace(k, v)
    write_page(out / f'study{sfx}.html', page)

def render_quiz_items(quiz):
    """lecture.json → quiz: [{"q", "options": [...], "answer": index, "explain", "slide"?}] → ინტერაქტიული ტესტი"""
    items = []
    for n, x in enumerate(quiz, 1):
        opts = ''.join(f'<button type="button" class="opt" data-i="{i}">{md_inline(o)}</button>' for i, o in enumerate(x['options']))
        back = f' <a class="chip" href="#s-{x["slide"]}">{L("გაიმეორე · სლაიდი", "Review · slide")} {x["slide"]}</a>' if x.get('slide') else ''
        items.append(f'<div class="qq" data-answer="{x["answer"]}"><div class="qt"><span class="qn">{n}</span><div>{md_inline(x["q"])}</div></div>'
                     f'<div class="opts">{opts}</div><div class="qe"><span class="verdict"></span> {md_inline(x.get("explain", ""))}{back}</div></div>')
    if LANG == 'en':
        return (f'<div class="qscore"><span id="qs">0</span> / {len(quiz)} correct · <span id="qd">0</span> / {len(quiz)} answered'
                f'<button type="button" class="btn qreset">Start over</button></div>{"".join(items)}<div class="qsum" id="qsum"></div>')
    return (f'<div class="qscore"><span id="qs">0</span> / {len(quiz)} სწორი · <span id="qd">0</span> / {len(quiz)} პასუხი'
            f'<button type="button" class="btn qreset">თავიდან</button></div>{"".join(items)}<div class="qsum" id="qsum"></div>')

# ---------- პროექტის გვერდები: courses/<კურსი>/project/NN.md → /<კურსი>/project/NN.html (ლექტორის კოდით) ----------
# NN.md: markdown (მიმოხილვა: რას ვწერთ ერთად, რა მზადაა წინასწარ, NuGet, ბრძანებები) + ფაილების ბლოკები:
#   ```csharp Ai/RestaurantTools.cs    — ფაილის სრული შიგთავსი ამ ლექციის შემდეგ (ფაილი მთლიანად ამ მოდულისაა)
#   ```csharp +Program.cs              — ლექტორის საკუთარი ფაილი: მხოლოდ AI-ის ნაწილი, როგორიც ამ ლექციის შემდეგაა
#   🗑 Path/File.cs                    — ფაილი წაიშალა
#   "## ⭐ …" და მის ქვემოთ ყველაფერი — ფაილების შემდეგ (თუ დრო დარჩა; პროექტის მდგომარეობაში არ შედის)
# ფაილების მდგომარეობა იკრიბება 01..NN-ით: ახალი / შეცვლილი; ახალი და შეცვლილი ხაზები მონიშნულია.
import difflib
FILE_FENCE = re.compile(r'^```(\w+) +(\+?)(\S+\.\w+)[ \t]*\n(.*?)^```[ \t]*$', re.M | re.S)

EXPLAIN_FENCE = re.compile(r'^```explain +(\S+)[ \t]*\n(.*?)^```[ \t]*$', re.M | re.S)

def parse_explain(body):
    """```explain Path: "@ start" (auto end) · "@ start .. end" · "@! line" (one line), then 🧠 what it does / 🔧 why"""
    items, cur, key = [], None, None
    for line in body.split('\n'):
        if line.startswith('@'):
            one = line.startswith('@!')
            spec = line[2:].strip()
            start, _, end = spec.partition(' .. ')
            cur = {'start': start.strip(), 'end': end.strip() or None, 'one': one, 'what': [], 'why': []}
            items.append(cur); key = None
        elif cur is not None and line.startswith('🧠'):
            key = 'what'; cur[key].append(line[1:].strip())
        elif cur is not None and line.startswith('🔧'):
            key = 'why'; cur[key].append(line[1:].strip())
        elif cur is not None and key:
            cur[key].append(line)
    return items

def _code_only(line):
    return re.sub(r'\s+//.*$', '', line).rstrip()

def find_region(lines, it, path, after=0):
    """ახსნები ფაილის რიგით იწერება: ხაზი იძებნება წინა ახსნის დასაწყისის შემდეგ (ასე „messages =“ ყოველ მეთოდში თავისას პოულობს)"""
    hits = [i for i, l in enumerate(lines) if i >= after and l.strip().startswith(it['start'])]
    if not hits:
        sys.exit(f'⚠ explain {path}: ხაზი ვერ მოიძებნა (ან წინა ახსნაზე ზემოთაა): "{it["start"]}"')
    i = hits[0]
    if it['one']:
        return i, i
    if it['end']:
        for j in range(i, len(lines)):
            if it['end'] in lines[j] and (j > i or it['end'] not in it['start']):
                return i, j
        sys.exit(f'⚠ explain {path}: ბოლო ხაზი ვერ მოიძებნა: "{it["end"]}"')
    depth = 0
    for j in range(i, len(lines)):
        c = _code_only(lines[j])
        depth += sum(c.count(x) for x in '({[') - sum(c.count(x) for x in ')}]')
        if depth <= 0 and c.endswith((';', '}', '},')):
            return i, j
    return i, len(lines) - 1

def write_project_pages(cdir, course, briefs, titles, built):
    out_dir = OUT / cdir.name / 'project'
    src_dir = cdir / 'project'
    code = lecturer_code()
    if not briefs:
        return
    if not code:
        print('  ⚠ პროექტის გვერდები არ აიწყო: .lecturer-code ფაილი ან LECTURER_CODE ცვლადი არ არის')
        return
    out_dir.mkdir(parents=True, exist_ok=True)
    nums = sorted(briefs)
    state, own = {}, set()
    for i, num in enumerate(nums):
        f = src_dir / f'{num:02d}.md'
        text = f.read_text() if f.exists() else ''
        b = briefs[num]
        proj = b.get('project', 'პროექტი')
        parts = [f'<div class="k">{esc(course["title"])} · ლექცია {num:02d}</div><h1>{md_inline(titles.get(num, ""))}</h1>']
        slug = built.get(num)
        if slug:
            parts.append(f'<div class="links"><a href="../{slug}/" target="_blank">▶ პრეზენტაცია</a>'
                         + (f'<a href="../{slug}/lecturer.html" target="_blank">🎓 ლექტორის გვერდი</a>' if (OUT / cdir.name / slug / 'lecturer.html').exists() else '')
                         + (f'<a href="../{slug}/study.html" target="_blank">📖 კონსპექტი</a>' if (OUT / cdir.name / slug / 'study.html').exists() else '') + '</div>')
        if b.get('learn'):
            parts.append('<div class="box"><h3>🎯 რას ისწავლის სტუდენტი</h3><ul>' + ''.join(f'<li>{md_inline(x)}</li>' for x in b['learn']) + '</ul></div>')
        if b.get('build'):
            parts.append(f'<div class="box"><h3>🛠 რას ვწერთ {esc(proj)}-ში</h3><ul>' + ''.join(f'<li>{md_inline(x)}</li>' for x in b['build']) + '</ul></div>')
        explains = {}
        for m in EXPLAIN_FENCE.finditer(text):
            explains.setdefault(m.group(1).lstrip('+'), []).extend(parse_explain(m.group(2)))
        text = EXPLAIN_FENCE.sub('', text)
        files = [(m.group(1), m.group(3), bool(m.group(2)), m.group(4).rstrip('\n')) for m in FILE_FENCE.finditer(text)]
        unknown = set(explains) - {f[1] for f in files}
        if unknown:
            sys.exit(f'⚠ project/{num:02d}.md: explain ფაილისთვის, რომელიც ამ ლექციაში არ არის: {", ".join(sorted(unknown))}')
        deleted = re.findall(r'^🗑\s+(\S+)', text, re.M)
        prose = FILE_FENCE.sub('', re.sub(r'^🗑.*$', '', text, flags=re.M))
        extra = ''
        m = re.search(r'^## ⭐', prose, re.M)
        if m:
            prose, extra = prose[:m.start()], prose[m.start():]
        if prose.strip():
            parts.append('<h2>მიმოხილვა</h2>' + md(prose))
        if not files and not deleted:
            parts.append(f'<div class="empty">ამ ლექციაზე {esc(proj)}-ში კოდი არ იწერება</div>')
        else:
            parts.append('<h2>ფაილები</h2><p class="legend"><span class="tag new">ახალი</span><span class="tag mod">შეცვლილი</span>'
                         '<span class="tag own">შენი ფაილი · AI-ის ნაწილი</span><span class="tag del">წაშლილი</span> · <i></i>ახალი / შეცვლილი ხაზი{" · <span class=xhint>ⓘ მიიტანე მაუსი კოდზე — ახსნა; დააჭირე — დამაგრება</span>" if explains else ""}</p>')
            toc, boxes = [], []
            for k, (lang, path, is_own, body) in enumerate(files):
                prev = state.get(path)
                lines = body.split('\n')
                add = set()
                if prev is None:
                    tag = '' if is_own else '<span class="tag new">ახალი</span>'
                else:
                    tag = '<span class="tag mod">შეცვლილი</span>'
                    for op, a1, a2, b1, b2 in difflib.SequenceMatcher(None, prev.split('\n'), lines, autojunk=False).get_opcodes():
                        if op in ('replace', 'insert'):
                            add.update(range(b1, b2))
                if is_own:
                    tag += '<span class="tag own">შენი ფაილი</span>'
                html_code = highlight(body, lang)
                # ახსნები: ყოველ ხაზს — ყველაზე შიდა რეგიონი, რომელშიც ის შედის
                owner, starts, xps = {}, set(), []
                regions = []
                after = 0
                for x, it in enumerate(explains.get(path, [])):
                    a, z = find_region(lines, it, f'{num:02d}/{path}', after)
                    regions.append((a, z, x, it)); after = a
                for a, z, x, it in sorted(regions, key=lambda r: -(r[1] - r[0])):   # wide first → narrow overrides
                    for idx in range(a, z + 1):
                        owner[idx] = x
                for a, z, x, it in regions:
                    starts.add(a)
                    changed = [idx for idx in range(a, z + 1) if idx in add]
                    if prev is not None and not changed:
                        print(f'  ⚠ {num:02d}/{path}: ახსნა უცვლელ კოდზე — "{it["start"]}"')
                    if prev is None or len(changed) == z - a + 1:
                        why_h = 'რატომ ვამატებთ'
                    else:
                        why_h = 'რა შეიცვალა და რატომ'
                    badge = ('<span class="tag new">ახალი</span>' if (prev is None and not is_own) or len(changed) == z - a + 1
                             else '<span class="tag mod">შეცვლილი</span>' if changed else '')
                    what = markdown.markdown('\n'.join(it['what']).strip(), extensions=['sane_lists'])
                    why = markdown.markdown('\n'.join(it['why']).strip(), extensions=['sane_lists']) if it['why'] else ''
                    xps.append(f'<template data-x="{x}"><div class="xh">{badge}<span>{f"ხაზი {a + 1}" if a == z else f"ხაზები {a + 1}–{z + 1}"}</span></div>'
                               f'<div class="xs"><b>🧠 რას აკეთებს</b>{what}</div>'
                               + (f'<div class="xs why"><b>🔧 {why_h}</b>{why}</div>' if why else '') + '</template>')
                n = [0]
                def mark(mm):
                    idx = n[0]; n[0] += 1
                    cls = 'ln' + (' add' if idx in add else '') + (' xs0' if idx in starts else '')
                    return f'<span class="{cls}"' + (f' data-x="{owner[idx]}"' if idx in owner else '') + '>'
                html_code = re.sub(r'<span class="ln">', mark, html_code)
                note = ('<div class="note">ეს ფაილი შენს პროექტში უკვე არსებობს (API კურსიდან). აქ მხოლოდ ის ნაწილია, რაც AI-ის მოდულში დაემატა — '
                        'დანარჩენი შენი კოდი უცვლელია.</div>') if is_own else ''
                fid = f'f{k}'
                toc.append(f'<a href="#{fid}">{tag}{esc(path)}</a>')
                boxes.append(f'<div class="codebox" id="{fid}"><div class="ch"><span>{tag}{esc(path)}</span><button class="copy" type="button">კოპირება</button></div>'
                             f'{note}<pre class="code"><code>{html_code}</code></pre>{"".join(xps)}</div>')
                state[path] = body
                if is_own: own.add(path)
            for path in deleted:
                state.pop(path, None); own.discard(path)
                toc.append(f'<a><span class="tag del">წაშლილი</span>{esc(path)}</a>')
            parts.append('<div class="toc">' + '<br>'.join(toc) + '</div>' + ''.join(boxes))
        if extra.strip():
            parts.append(md(extra.replace('## ⭐', '## ⭐', 1)))
        if state:
            tree = '\n'.join(p + ('   ← შენი ფაილი, AI-ის ნაწილი' if p in own else '') for p in sorted(state))
            parts.append(f'<h2>{esc(proj)}: AI-ის ფაილები ამ ლექციის შემდეგ</h2><div class="tree">{esc(tree)}</div>')
        prev_n = nums[i - 1] if i else None
        next_n = nums[i + 1] if i + 1 < len(nums) else None
        nav = (f'<a href="{prev_n:02d}.html">← {prev_n:02d}</a>' if prev_n else '') + (f'<a href="{next_n:02d}.html">{next_n:02d} →</a>' if next_n else '')
        page = (ENGINE / 'project.html').read_text()
        for key, v in {'{{TITLE}}': f'{num:02d} · ' + esc(titles.get(num, '')), '{{NUM}}': str(num), '{{NAV}}': nav,
                       '{{BODY}}': '\n'.join(parts), '{{FONTS}}': FONTS + THEME_HEAD, '{{PAGE_THEME}}': PAGE_THEME, '{{TOKEN_CSS}}': TOKEN_CSS}.items():
            page = page.replace(key, v)
        write_locked(out_dir / f'{num:02d}.html', page, code, 'lectures:lecturer', 'ლექტორის გვერდი')
    print(f'  {cdir.name}/project: {len(nums)} pages')

# კურსის სილაბუსი: courses/<კურსი>/syllabus.md → /<კურსი>/syllabus.html
#   "### 01. სათაური" = ლექცია; თუ ეს ლექცია აწყობილია, გვერდით ჩნდება ბმულები პრეზენტაციასა და კონსპექტზე
#   "📚 …" = რას ისწავლის სტუდენტი, "🛠 [პროექტი |] …" = რას ვწერთ პროექტში (ერთი ხაზი = ერთი პუნქტი) → 💻 პროექტის გვერდი (სილაბუსზე არ ჩანს)
def write_syllabus(cdir, course):
    src = cdir / 'syllabus.md'
    out = OUT / cdir.name / 'syllabus.html'
    if not src.exists():
        out.unlink(missing_ok=True)
        return False
    built = {int(d.name.split('-', 1)[0]): d.name for d in cdir.iterdir() if (d / 'deck.html').exists() and d.name[:2].isdigit()}
    briefs, cur, lines = {}, None, []
    for line in src.read_text().splitlines():
        m = re.match(r'### (\d+)\.', line)
        if m:
            cur = int(m.group(1))
        if cur is not None and line.startswith(('📚', '🛠')):
            kind, body = ('learn' if line.startswith('📚') else 'build'), line[1:].strip()
            if kind == 'build' and '|' in body:
                briefs.setdefault(cur, {})['project'], body = [x.strip() for x in body.split('|', 1)]
            briefs.setdefault(cur, {}).setdefault(kind, []).append(body)
            continue
        lines.append(line)
    h = markdown.markdown('\n'.join(lines), extensions=['tables', 'sane_lists'])
    has_proj = bool(briefs) and bool(lecturer_code())
    def lec(m):
        num, title, desc = int(m.group(1)), m.group(2), m.group(3) or ''
        slug = built.get(num)
        proj = (f'<a class="proj" href="project/{num:02d}.html" title="რას ისწავლის სტუდენტი და რას ვწერთ პროექტში — სრული კოდით (ლექტორის კოდით)">💻 კოდი</a>'
                if has_proj and num in briefs else '')
        links = ((f'<a href="{slug}/">▶ პრეზენტაცია</a>'
                  + (f'<a href="{slug}/study.html">📖 კონსპექტი</a>' if (OUT / cdir.name / slug / 'study.html').exists() else '')) if slug else '') + proj
        go = f'<span class="go">{links}</span>' if links else ''
        return f'<div class="lec{" ready" if slug else ""}" id="l-{num}"><h3>{m.group(1)}. {title}{go}</h3>{desc}</div>'
    h = re.sub(r'<h3>(\d+)\.\s*(.*?)</h3>\s*(<p>.*?</p>)?', lec, h, flags=re.S)
    titles = {int(a): b_ for a, b_ in re.findall(r'^### (\d+)\.\s*(.+)$', src.read_text(), re.M)}
    write_project_pages(cdir, course, briefs, titles, built)
    page = (ENGINE / 'syllabus.html').read_text()
    for k, v in {'{{TITLE}}': esc(course['title']), '{{COUNT}}': str(len(re.findall(r'class="lec', h))), '{{BODY}}': h,
                 '{{FONTS}}': FONTS + THEME_HEAD, '{{PAGE_THEME}}': PAGE_THEME}.items():
        page = page.replace(k, v)
    write_page(out, page)
    return True

# ---------- everything ----------
def syllabus_parts(cdir):
    """syllabus.md: `## ნაწილი (N ლექცია)` + `### NN. …` → {NN: 'ნაწილი'} — მთავარ გვერდზე ლექციები ნაწილებად ჯგუფდება"""
    f = cdir / 'syllabus.md'
    if not f.exists():
        return {}
    out, cur = {}, ''
    for line in f.read_text().splitlines():
        if line.startswith('## '):
            cur = re.sub(r'\s*\(\d+ ლექცია\)\s*$', '', line[3:]).strip()
        m = re.match(r'### (\d+)\.', line)
        if m:
            out[int(m.group(1))] = cur
    return out

def main(filters):
    OUT.mkdir(parents=True, exist_ok=True)
    marker = OUT / GENERATED
    if not filters and marker.exists():
        for d in marker.read_text().split():
            if (OUT / d).is_dir() and d not in ('courses', 'engine', '.git', '.github'):
                shutil.rmtree(OUT / d)
    if (ENGINE / 'assets').is_dir():   # საერთო ფაილები (თუ არის) → /assets/
        shutil.copytree(ENGINE / 'assets', OUT / 'assets', dirs_exist_ok=True)
    catalog, problems = [], []
    for cdir in sorted((ROOT / 'courses').iterdir()):
        if not (cdir / 'course.json').exists():
            continue
        course = json.loads((cdir / 'course.json').read_text())
        lectures, prev = [], None
        for ldir in sorted(p for p in cdir.iterdir() if (p / 'deck.html').exists()):
            meta = json.loads((ldir / 'lecture.json').read_text())
            if (ldir / 'lecture.en.json').exists():
                meta['_en'] = json.loads((ldir / 'lecture.en.json').read_text())
            if meta.get('starts_series'):   # e.g. a guest lecture for another group: no review of the previous lecture
                prev = None
            rel = f'{cdir.name}/{ldir.name}'
            if not filters or any(f in rel for f in filters):
                info, errs = build_lecture(course, cdir, ldir, meta, prev)
                problems += errs
                if info: lectures.append(info)
            prev = {'meta': meta, 'num': int(ldir.name.split('-', 1)[0]), 'homework': md_doc(ldir / 'homework.md'), 'href': f'../{ldir.name}/'}
        parts = syllabus_parts(cdir)
        for l in lectures:
            l['part'] = parts.get(l['num'], '')
        has_syl = write_syllabus(cdir, course)
        catalog.append({'slug': cdir.name, 'title': course['title'], 'order': course.get('order', 99), 'lectures': lectures, 'syllabus': has_syl})
    catalog.sort(key=lambda c: c['order'])
    if not filters:
        page = (ENGINE / 'index.html').read_text().replace('/*CATALOG*/[]', json.dumps(catalog, ensure_ascii=False)).replace('<!--THEME-->', THEME_HEAD + '<style>' + PAGE_THEME + '</style>')
        write_page(OUT / 'index.html', page)
        (OUT / '.nojekyll').write_text('')
        marker.write_text('\n'.join([c['slug'] for c in catalog] + ['assets']) + '\n')
        print(f'index: {sum(len(c["lectures"]) for c in catalog)} lectures in {len(catalog)} courses')
    if problems:
        sys.exit('⚠ ლექციის სტრუქტურა არასრულია — იხ. ზემოთ')

if __name__ == '__main__':
    main(sys.argv[1:])
