# -*- coding: utf-8 -*-
"""Grava os vídeos de ajuda do site (assets/video-<id>.mp4, com capa e miniatura).

Cada vídeo é montado quadro a quadro: o site é aberto num navegador sem janela (Playwright),
em tela de celular, e cada quadro recebe uma faixa de legenda. Os vídeos não têm som.
Legendas e textos: dados/videos.json. Duração e tamanho de cada vídeo: dados/video.json.
Requer: playwright (Chromium), Pillow e ffmpeg.
Uso:   python3 scripts/gerar_video.py              (grava todos)
       python3 scripts/gerar_video.py nova-busca   (grava só um)
Rodar depois de gerar_site.py e rodar gerar_site.py de novo no fim (atualiza duração e tamanho na página).
"""
import asyncio, functools, html, http.server, json, os, shutil, subprocess, sys, tempfile, threading
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from playwright.async_api import async_playwright

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FPS = 15
W, H = 720, 1280             # quadro final (9:16)
FAIXA = 236                  # altura da faixa de legenda
VW = 390                     # largura da tela de celular (px CSS)
ESC = W / VW
VH = round((H - FAIXA) / ESC)
PORTA = 8765
BASE = f"http://127.0.0.1:{PORTA}/"

FONTES = "/usr/share/fonts/opentype/inter/"
def fonte(nome, tam):
    return ImageFont.truetype(FONTES + nome, tam)
F_ROT, F_LEG = fonte("Inter-SemiBold.otf", 26), fonte("Inter-Medium.otf", 35)
VERDE, VERDE_ESC, AMARELO, BRANCO = (11, 107, 87), (8, 74, 61), (255, 228, 92), (255, 255, 255)

CFG = json.load(open(os.path.join(RAIZ, "dados", "videos.json"), encoding="utf-8"))
MOSAICO = json.load(open(os.path.join(RAIZ, "dados", "mosaico.json"), encoding="utf-8"))

# ---------------------------------------------------------------- quadros
class Filme:
    def __init__(self, video, pasta):
        self.v, self.pasta, self.quadros, self.leg, self.ini, self.t = video, pasta, [], None, 0.0, 0.0
        self.cenas = {c["id"]: c for c in video["cenas"]}
        for c in video["cenas"]:      # a faixa comporta três linhas de legenda
            if len(quebrar(c["texto"], F_LEG, W - 80)) > 3:
                raise SystemExit(f"Legenda longa demais ({video['id']}/{c['id']}): encurte em dados/videos.json")

    def faixa(self):
        img = Image.new("RGB", (W, FAIXA), VERDE)
        d = ImageDraw.Draw(img)
        if self.leg:
            d.text((40, 30), self.leg["pagina"].upper(), font=F_ROT, fill=AMARELO)
            y = 74
            for linha in quebrar(self.leg["texto"], F_LEG, W - 80):
                d.text((40, y), linha, font=F_LEG, fill=BRANCO)
                y += 46
        d.rectangle([0, FAIXA - 6, W, FAIXA], fill=VERDE_ESC)
        return img

    def add(self, tela, dur):
        q = Image.new("RGB", (W, H), BRANCO)
        q.paste(self.faixa(), (0, 0))
        q.paste(tela if tela.size == (W, H - FAIXA) else tela.resize((W, H - FAIXA)), (0, FAIXA))
        self.add_img(q, dur)

    def add_img(self, img, dur):
        caminho = os.path.join(self.pasta, f"q{len(self.quadros):05d}.png")
        img.save(caminho)
        self.quadros.append((caminho, dur))
        self.t += dur

    def legenda(self, cid):
        self.leg, self.ini = self.cenas[cid], self.t

    def tempo_leitura(self):
        """Tempo que falta para ler a legenda atual (13 caracteres por segundo, mais 1,2 s)."""
        if not self.leg:
            return 0
        return max(0.0, len(self.leg["texto"]) / 13 + 1.2 - (self.t - self.ini))

    def montar(self, saida):
        lista = os.path.join(self.pasta, "lista.txt")
        with open(lista, "w") as f:
            for c, d in self.quadros:
                f.write(f"file '{c}'\nduration {d:.4f}\n")
            f.write(f"file '{self.quadros[-1][0]}'\n")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lista,
                        "-vf", f"fps={FPS},format=yuv420p", "-c:v", "libx264", "-preset", "slow", "-crf", "30",
                        "-tune", "stillimage", "-movflags", "+faststart", "-an", saida], check=True)

def quebrar(texto, f, largura):
    linhas, atual = [], ""
    for p in texto.split():
        teste = (atual + " " + p).strip()
        if f.getlength(teste) <= largura:
            atual = teste
        else:
            linhas.append(atual); atual = p
    return linhas + [atual]

def cartao(titulo, sub, rodape):
    """Cartão de abertura e de encerramento, com o mosaico real das leis."""
    img = Image.new("RGB", (W, H), VERDE_ESC)
    d = ImageDraw.Draw(img)
    d.text((56, 150), "PROJETO DEMOCRACIA BRASIL", font=fonte("Inter-SemiBold.otf", 28), fill=AMARELO)
    y, ft = 210, fonte("InterDisplay-Bold.otf", 76 if len(titulo) > 26 else 84)
    for linha in quebrar(titulo, ft, W - 112):
        d.text((56, y), linha, font=ft, fill=BRANCO); y += int(ft.size * 1.14)
    y += 24
    for linha in quebrar(sub, fonte("Inter-Regular.otf", 36), W - 112):
        d.text((56, y), linha, font=fonte("Inter-Regular.otf", 36), fill=(214, 236, 228)); y += 50
    cor = {"nominal": (92, 200, 168), "simbolica": (74, 106, 96), "comissoes": (224, 168, 74), "sem-registro": None}
    lado, gap, cols = 30, 6, 17
    x0, y0 = 56, max(y + 60, 760)
    for i, m in enumerate(MOSAICO):
        x, yy = x0 + (i % cols) * (lado + gap), y0 + (i // cols) * (lado + gap)
        c = cor[m["situacao"]]
        if c:
            d.rounded_rectangle([x, yy, x + lado, yy + lado], 4, fill=c)
        else:
            d.rounded_rectangle([x, yy, x + lado, yy + lado], 4, outline=(168, 182, 176), width=2)
    f_rod = fonte("Inter-Medium.otf", 28)
    linhas = [rodape] if f_rod.getlength(rodape) <= W - 112 else [rodape[:rodape.index("/") + 1], rodape[rodape.index("/") + 1:]]
    for i, linha in enumerate(linhas):
        d.text((56, H - 70 - 40 * (len(linhas) - i)), linha, font=f_rod, fill=(214, 236, 228))
    return img

def miniatura(icone):
    """Miniatura quadrada para o cartão do vídeo: um desenho simples por vídeo e o símbolo de play."""
    m = Image.new("RGB", (240, 240), VERDE_ESC)
    d = ImageDraw.Draw(m)
    claro, medio = (214, 236, 228), (92, 200, 168)
    if icone == "lupa":
        d.ellipse([46, 40, 150, 144], outline=claro, width=14)
        d.line([(138, 132), (196, 190)], fill=claro, width=22)
    elif icone == "ficha":
        d.rounded_rectangle([58, 34, 182, 206], 10, fill=claro)
        for i, w in enumerate((90, 70, 90, 54)):
            d.rounded_rectangle([78, 66 + i * 28, 78 + w, 78 + i * 28], 4, fill=VERDE)
        d.ellipse([140, 150, 206, 216], fill=medio)
        d.line([(156, 184), (170, 198), (192, 168)], fill=VERDE_ESC, width=9)
    else:
        lado, gap = 22, 6
        for i, m_ in enumerate(MOSAICO[:64]):
            x, y = 12 + (i % 8) * (lado + gap), 12 + (i // 8) * (lado + gap)
            c = {"nominal": medio, "simbolica": (74, 106, 96), "comissoes": (224, 168, 74)}.get(m_["situacao"])
            if c:
                d.rounded_rectangle([x, y, x + lado, y + lado], 3, fill=c)
            else:
                d.rounded_rectangle([x, y, x + lado, y + lado], 3, outline=(168, 182, 176), width=2)
    if icone == "play":
        d.ellipse([78, 78, 162, 162], fill=BRANCO)
        d.polygon([(108, 96), (108, 144), (148, 120)], fill=VERDE)
    else:
        d.ellipse([10, 168, 66, 224], fill=BRANCO)
        d.polygon([(30, 182), (30, 210), (54, 196)], fill=VERDE)
    return m

# ---------------------------------------------------------------- ações no navegador
async def tela(pg):
    return Image.open(BytesIO(await pg.screenshot())).convert("RGB")

async def quadro(pg, f, dur=1 / FPS):
    f.add(await tela(pg), dur)

async def segurar(pg, f, s):
    f.add(await tela(pg), s)

async def ler(pg, f):
    s = f.tempo_leitura()
    if s > 0:
        await segurar(pg, f, s)

async def rolar_ate(pg, f, alvo_y, passos=14):
    ini = await pg.evaluate("scrollY")
    for i in range(1, passos + 1):
        k = i / passos
        k = k * k * (3 - 2 * k)
        await pg.evaluate(f"window.scrollTo(0,{ini + (alvo_y - ini) * k})")
        await quadro(pg, f)

async def rolar_para(pg, f, seletor, margem=12, passos=14):
    y = await pg.evaluate(f"(() => {{const r=document.querySelector({json.dumps(seletor)}).getBoundingClientRect(); return r.top + scrollY - {margem};}})()")
    maxy = await pg.evaluate("document.documentElement.scrollHeight - innerHeight")
    await rolar_ate(pg, f, max(0, min(y, maxy)), passos)

async def toque(pg, f, loc, clicar=True):
    await loc.scroll_into_view_if_needed()
    b = await loc.bounding_box()
    x, y = b["x"] + b["width"] / 2, b["y"] + b["height"] / 2
    for s in (0.55, 0.7, 0.85, 1.0, 1.0, 1.0, 1.0):
        await pg.evaluate(f"""(() => {{let t=document.getElementById('toque-video');
          if(!t){{t=document.createElement('div');t.id='toque-video';document.body.appendChild(t);}}
          t.style.cssText='position:fixed;left:{x - 24}px;top:{y - 24}px;width:48px;height:48px;border-radius:50%;'+
            'background:rgba(31,95,191,.28);border:3px solid rgba(31,95,191,.9);z-index:99999;pointer-events:none;transform:scale({s})';}})()""")
        await quadro(pg, f)
    await pg.evaluate("document.getElementById('toque-video')?.remove()")
    if clicar:
        await loc.click()
        await pg.wait_for_load_state("load")
        await pg.wait_for_timeout(150)

async def digitar(pg, f, loc, texto):
    for ch in texto:
        await loc.type(ch)
        await pg.wait_for_timeout(40)
        await quadro(pg, f, 1 / 10)
    await pg.wait_for_timeout(300)

async def menu(pg, f, nome):
    await rolar_ate(pg, f, 0, 10)
    await toque(pg, f, pg.locator("nav.menu a", has_text=nome))

async def palco(pg, corpo):
    """Tela própria do vídeo (fora do site), com o estilo do site."""
    await pg.goto(BASE + "index.html")
    await pg.set_content(f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<link rel="stylesheet" href="{BASE}assets/estilo.css"><style>
body{{background:var(--papel)}} .palco{{padding:1.2rem 1rem}} .palco h2{{margin-top:.2rem}}
.caixa{{border:2px solid var(--verde);border-radius:12px;background:var(--superficie);padding:.9rem 1rem;min-height:9.5rem;
  font-size:1.05rem;line-height:1.5;white-space:pre-wrap}}
.cursor{{display:inline-block;width:2px;height:1.1em;background:var(--tinta);vertical-align:-.15em}}
ol.grandes{{padding-left:1.4rem;font-size:1.12rem}} ol.grandes li{{margin:.7rem 0}}
ul.checagem{{list-style:none;padding:0;font-size:1.05rem}} ul.checagem li{{display:flex;gap:.6rem;align-items:flex-start;margin:.65rem 0}}
ul.checagem b{{flex:none;width:1.6rem;height:1.6rem;border-radius:50%;background:var(--verde);color:#fff;display:grid;place-items:center;font-size:.95rem}}
ul.checagem b.pend{{background:var(--ambar)}}
</style></head><body><div class="palco">{corpo}</div></body></html>""")
    await pg.wait_for_timeout(200)

# ---------------------------------------------------------------- vídeo 1: como usar o site
async def video_como_usar(pg, f):
    v = f.v
    await pg.goto(BASE + "index.html"); await pg.wait_for_load_state("load")
    f.legenda("inicio")
    await segurar(pg, f, 1.6)
    await rolar_para(pg, f, ".mosaico", margem=150)
    await ler(pg, f)
    f.legenda("cores")
    await rolar_para(pg, f, ".legenda", margem=230, passos=8)
    await ler(pg, f)
    # abre o primeiro quadrado verde (regra fixa, sem escolha de tema)
    f.legenda("quadrado")
    await segurar(pg, f, 1.2)
    await toque(pg, f, pg.locator(".mosaico a.s-nominal").first)
    await segurar(pg, f, 0.8)
    f.legenda("ficha")
    await segurar(pg, f, 1.5)
    aberto = "#lista li details[open]"
    await rolar_para(pg, f, aberto + " dl.ficha dt:nth-of-type(7)", margem=260, passos=24)
    await segurar(pg, f, 1.6)
    await rolar_para(pg, f, aberto + " p.fontes", margem=300, passos=16)
    await ler(pg, f)
    f.legenda("busca")
    await menu(pg, f, "Acervo")
    campo = pg.locator("#q")
    await toque(pg, f, campo)
    await digitar(pg, f, campo, v["exemplo_busca"])
    await segurar(pg, f, 0.6)
    await rolar_para(pg, f, "#contagem", margem=200, passos=10)
    await ler(pg, f)
    f.legenda("filtros")
    await rolar_para(pg, f, "form.busca", margem=16, passos=8)
    await toque(pg, f, pg.locator("#nova-busca"))
    await quadro(pg, f, 0.4)
    await toque(pg, f, pg.locator("details.filtros > summary"))
    await rolar_para(pg, f, "details.filtros", margem=20, passos=10)
    sel = pg.locator('select[data-filtro="data-sit"]')
    await toque(pg, f, sel, clicar=False)
    await sel.select_option("nominal"); await pg.wait_for_timeout(300)
    await quadro(pg, f, 0.5)
    await rolar_para(pg, f, "#contagem", margem=260, passos=8)
    await ler(pg, f)
    f.legenda("selecao")
    await pg.evaluate("document.querySelector('details.filtros').open=false")
    await rolar_para(pg, f, "#lista > li:not([hidden])", margem=40, passos=10)
    botoes = pg.locator("#lista > li:not([hidden]) [data-selecionar]")
    await toque(pg, f, botoes.nth(0))
    await quadro(pg, f, 0.5)
    await toque(pg, f, botoes.nth(1))
    await quadro(pg, f, 0.6)
    await toque(pg, f, pg.locator("#pdf-selecao"), clicar=False)
    await ler(pg, f)
    await pg.evaluate("localStorage.clear()")
    f.legenda("votacoes")
    await menu(pg, f, "Votações")
    await rolar_para(pg, f, ".cartao", margem=20, passos=14)
    await toque(pg, f, pg.locator(".cartao details.mais > summary").first)
    await rolar_para(pg, f, ".cartao details.mais", margem=200, passos=10)
    await ler(pg, f)
    f.legenda("entenda")
    await menu(pg, f, "Entenda")
    await rolar_para(pg, f, "#caminho", margem=16, passos=14)
    await ler(pg, f)
    f.legenda("compartilhar")
    await menu(pg, f, "Compartilhar")
    await rolar_para(pg, f, ".cartao", margem=16, passos=12)
    await toque(pg, f, pg.locator(".cartao [data-copiar]").first, clicar=False)
    await ler(pg, f)
    f.legenda("baixar")
    await menu(pg, f, "Baixar")
    await ler(pg, f)

# ---------------------------------------------------------------- vídeo 2: busca nova
async def video_nova_busca(pg, f):
    v = f.v
    await pg.goto(BASE + "index.html"); await pg.wait_for_load_state("load")
    f.legenda("abrir")
    await segurar(pg, f, 1.4)
    await toque(pg, f, pg.locator("nav.menu a", has_text="Acervo"))
    await segurar(pg, f, 0.8)
    await ler(pg, f)
    f.legenda("digitar")
    await rolar_para(pg, f, "form.busca", margem=16, passos=10)
    campo = pg.locator("#q")
    await toque(pg, f, campo)
    await digitar(pg, f, campo, v["exemplo_busca"])
    await ler(pg, f)
    f.legenda("resultado")
    await rolar_para(pg, f, "#contagem", margem=150, passos=10)
    await ler(pg, f)
    f.legenda("ficha")
    primeiro = "#lista > li:not([hidden])"
    await rolar_para(pg, f, primeiro, margem=20, passos=10)
    await toque(pg, f, pg.locator(primeiro + " details.mais > summary").first)
    await rolar_para(pg, f, primeiro + " p.fontes", margem=330, passos=16)
    await ler(pg, f)
    f.legenda("nova")
    await rolar_para(pg, f, "form.busca", margem=16, passos=12)
    await segurar(pg, f, 1.0)
    await toque(pg, f, pg.locator("#nova-busca"))
    await segurar(pg, f, 0.6)
    await rolar_para(pg, f, "#contagem", margem=180, passos=8)
    await ler(pg, f)
    f.legenda("numero")
    await rolar_para(pg, f, "form.busca", margem=16, passos=8)
    await toque(pg, f, campo)
    await digitar(pg, f, campo, v["exemplo_numero"])
    await segurar(pg, f, 0.4)
    await rolar_para(pg, f, "#contagem", margem=150, passos=10)
    await ler(pg, f)
    f.legenda("filtro")
    await rolar_para(pg, f, "form.busca", margem=16, passos=8)
    await toque(pg, f, pg.locator("#nova-busca"))
    await toque(pg, f, pg.locator("details.filtros > summary"))
    await rolar_para(pg, f, "details.filtros", margem=20, passos=10)
    sel = pg.locator('select[data-filtro="data-sub"]')
    await toque(pg, f, sel, clicar=False)
    await sel.select_option(v["exemplo_assunto"]); await pg.wait_for_timeout(300)
    await quadro(pg, f, 0.6)
    await rolar_para(pg, f, "#contagem", margem=300, passos=10)
    await ler(pg, f)

# ---------------------------------------------------------------- vídeo 3: pesquisa de um item novo
async def video_pesquisa(pg, f):
    v = f.v
    f.legenda("abrir")
    await palco(pg, """<h2>Antes de começar</h2>
<ol class="grandes"><li>Abra o <strong>app do Claude</strong> no computador.</li>
<li>Entre no projeto <strong>Projeto Democracia Brasil</strong>.</li>
<li>Comece uma <strong>conversa nova</strong>.</li></ol>
<p class="nota">Use o computador: a coleta das votações na Câmara e no Senado é feita pelo navegador do app.</p>""")
    await segurar(pg, f, 0.5)
    await ler(pg, f)
    f.legenda("pedido")
    texto = "\n".join(v["pedido"])
    await palco(pg, """<h2>O pedido</h2><p class="pequeno">Exemplo do que escrever:</p><div class="caixa"><span id="digitado"></span><span class="cursor"></span></div>
<p class="pequeno">Se tiver, inclua também o link da fonte ou dúvidas sobre o escopo.</p>""")
    await quadro(pg, f, 0.6)
    for i in range(2, len(texto) + 2, 2):
        await pg.evaluate(f"document.getElementById('digitado').textContent = {json.dumps(texto[:i])}")
        await quadro(pg, f, 1 / 15)
    await segurar(pg, f, 1.0)
    await ler(pg, f)
    f.legenda("ficha")
    await pg.goto(BASE + "acervo.html#MUL-2013-002"); await pg.wait_for_load_state("load"); await pg.wait_for_timeout(300)
    await segurar(pg, f, 1.2)
    aberto = "#lista li details[open]"
    await rolar_para(pg, f, aberto + " dl.ficha dt:nth-of-type(3)", margem=120, passos=20)
    await ler(pg, f)
    f.legenda("votacoes")
    await pg.goto(BASE + "votacoes.html"); await pg.wait_for_load_state("load")
    await rolar_para(pg, f, ".linha-casa", margem=16, passos=4)
    await segurar(pg, f, 1.6)
    await rolar_para(pg, f, ".cartao", margem=20, passos=14)
    await pg.evaluate("document.querySelector('.cartao details.mais').open=true")
    await rolar_para(pg, f, ".cartao details.mais", margem=210, passos=10)
    await ler(pg, f)
    f.legenda("saidas")
    await pg.goto(BASE + "baixar.html"); await pg.wait_for_load_state("load")
    await segurar(pg, f, 0.8)
    await rolar_para(pg, f, "main ul", margem=40, passos=10)
    await segurar(pg, f, 2.0)
    await pg.goto(BASE + "index.html"); await pg.wait_for_load_state("load")
    await rolar_para(pg, f, "#novidades", margem=16, passos=4)
    await ler(pg, f)
    f.legenda("conferir")
    await palco(pg, """<h2>Ao final da resposta</h2><p class="pequeno">A resposta termina com a lista das saídas:</p>
<ul class="checagem">
<li><b>✓</b><span>Planilha-mestre atualizada</span></li>
<li><b>✓</b><span>Site, com o item no acervo e em Novidades</span></li>
<li><b>✓</b><span>PDF resumido e textos para redes</span></li>
<li><b>✓</b><span>Histórico de versões do guia</span></li>
<li><b class="pend">!</b><span>O que ficou pendente, com o motivo</span></li></ul>
<p class="nota">Tudo fica marcado como versão preliminar até a checagem final.</p>""")
    await segurar(pg, f, 0.5)
    await ler(pg, f)

ROTEIROS = {"como-usar": video_como_usar, "nova-busca": video_nova_busca, "pesquisa-item-novo": video_pesquisa}

# ---------------------------------------------------------------- execução
def servidor():
    class Silencioso(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass
    s = http.server.ThreadingHTTPServer(("127.0.0.1", PORTA), functools.partial(Silencioso, directory=RAIZ))
    threading.Thread(target=s.serve_forever, daemon=True).start()
    return s

async def gravar(filmes):
    async with async_playwright() as p:
        nav = await p.chromium.launch()
        for f in filmes:
            ctx = await nav.new_context(viewport={"width": VW, "height": VH}, device_scale_factor=ESC, is_mobile=True,
                                        color_scheme="light", locale="pt-BR", permissions=["clipboard-read", "clipboard-write"])
            pg = await ctx.new_page()
            await ROTEIROS[f.v["id"]](pg, f)
            await ctx.close()
        await nav.close()

def main():
    ids = sys.argv[1:] or [v["id"] for v in CFG["videos"]]
    meta_p = os.path.join(RAIZ, "dados", "video.json")
    meta = json.load(open(meta_p, encoding="utf-8")) if os.path.exists(meta_p) else {}
    meta = {k: x for k, x in meta.items() if isinstance(x, dict)}
    pastas, filmes = [], []
    for v in CFG["videos"]:
        if v["id"] not in ids:
            continue
        pasta = tempfile.mkdtemp(prefix="video-"); pastas.append(pasta)
        f = Filme(v, pasta)
        f.abertura = cartao(v["titulo"], v["subtitulo"], "Vídeo sem som, com legendas")
        f.add_img(f.abertura, 3.2)
        filmes.append(f)
    s = servidor()
    try:
        asyncio.run(gravar(filmes))
    finally:
        s.shutdown()
    for f in filmes:
        v = f.v
        f.add_img(cartao(v["fim_titulo"], v["fim_texto"], CFG["endereco"]), 4.5)
        mp4 = os.path.join(RAIZ, "assets", f"video-{v['id']}.mp4")
        f.montar(mp4)
        f.abertura.resize((540, 960), Image.LANCZOS).save(os.path.join(RAIZ, "assets", f"video-{v['id']}-capa.jpg"), quality=78, optimize=True, progressive=True)
        miniatura(v["icone"]).save(os.path.join(RAIZ, "assets", f"video-{v['id']}-mini.jpg"), quality=80, optimize=True)
        meta[v["id"]] = {"duracao_s": round(f.t, 1), "bytes": os.path.getsize(mp4)}
        print(f"{v['id']}: {f.t:.1f} s, {os.path.getsize(mp4) / 1024 / 1024:.2f} MB")
    for p in pastas:
        shutil.rmtree(p)
    json.dump(meta, open(meta_p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

if __name__ == "__main__":
    main()
