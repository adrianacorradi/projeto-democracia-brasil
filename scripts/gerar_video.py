# -*- coding: utf-8 -*-
"""Grava o vídeo "Como usar o site" (assets/tutorial.mp4 e assets/tutorial-capa.jpg).

O vídeo é montado quadro a quadro: o site é aberto num navegador sem janela (Playwright),
em tela de celular, e cada quadro recebe uma faixa de legenda. Não tem som.
Requer: playwright (Chromium), Pillow e ffmpeg.
Uso:   python3 scripts/gerar_video.py   (rodar depois de gerar_site.py; refaça quando o site mudar)
"""
import asyncio, json, os, shutil, subprocess, sys, tempfile, textwrap, threading, http.server, functools
from PIL import Image, ImageDraw, ImageFont
from playwright.async_api import async_playwright

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAIDA_MP4 = os.path.join(RAIZ, "assets", "tutorial.mp4")
SAIDA_CAPA = os.path.join(RAIZ, "assets", "tutorial-capa.jpg")
SAIDA_MINI = os.path.join(RAIZ, "assets", "tutorial-mini.jpg")
FPS = 15
W, H = 720, 1280             # quadro final (9:16)
FAIXA = 236                  # altura da faixa de legenda
VW = 390                     # largura da tela de celular (px CSS)
ESC = W / VW                 # escala de pixels
VH = round((H - FAIXA) / ESC)
PORTA = 8765

FONTES = "/usr/share/fonts/opentype/inter/"
def fonte(nome, tam):
    return ImageFont.truetype(FONTES + nome, tam)
F_ROT, F_LEG = fonte("Inter-SemiBold.otf", 26), fonte("Inter-Medium.otf", 35)
VERDE, VERDE_ESC, AMARELO, BRANCO = (11, 107, 87), (8, 74, 61), (255, 228, 92), (255, 255, 255)

# ---------------------------------------------------------------- roteiro (também vai para a página)
ROTEIRO = json.load(open(os.path.join(RAIZ, "dados", "tutorial.json"), encoding="utf-8"))
LEG = {c["id"]: c for c in ROTEIRO["cenas"]}

# ---------------------------------------------------------------- quadros
class Filme:
    def __init__(self, pasta):
        self.pasta, self.quadros, self.leg, self.ini, self.t = pasta, [], None, 0.0, 0.0

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
        q.paste(tela.resize((W, H - FAIXA)) if tela.size != (W, H - FAIXA) else tela, (0, FAIXA))
        self.add_img(q, dur)

    def add_img(self, img, dur):
        caminho = os.path.join(self.pasta, f"q{len(self.quadros):05d}.png")
        img.save(caminho)
        self.quadros.append((caminho, dur))
        self.t += dur

    def legenda(self, cid):
        """Troca a legenda, garantindo tempo de leitura para a anterior (13 caracteres por segundo)."""
        self.leg, self.ini = LEG[cid], self.t

    def tempo_leitura(self):
        if not self.leg:
            return 0
        return max(0.0, len(self.leg["texto"]) / 13 + 1.2 - (self.t - self.ini))

    def montar(self):
        lista = os.path.join(self.pasta, "lista.txt")
        with open(lista, "w") as f:
            for c, d in self.quadros:
                f.write(f"file '{c}'\nduration {d:.4f}\n")
            f.write(f"file '{self.quadros[-1][0]}'\n")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lista,
                        "-vf", f"fps={FPS},format=yuv420p", "-c:v", "libx264", "-preset", "slow", "-crf", "30",
                        "-tune", "stillimage", "-movflags", "+faststart", "-an", SAIDA_MP4], check=True)

def quebrar(texto, f, largura):
    linhas, atual = [], ""
    for p in texto.split():
        teste = (atual + " " + p).strip()
        if f.getlength(teste) <= largura:
            atual = teste
        else:
            linhas.append(atual); atual = p
    return linhas + [atual]

def cartao(titulo, sub, rodape, mosaico):
    """Cartão de abertura e de encerramento, com o mosaico real das leis."""
    img = Image.new("RGB", (W, H), VERDE_ESC)
    d = ImageDraw.Draw(img)
    d.text((56, 150), "PROJETO DEMOCRACIA BRASIL", font=fonte("Inter-SemiBold.otf", 28), fill=AMARELO)
    y = 210
    for linha in quebrar(titulo, fonte("InterDisplay-Bold.otf", 84), W - 112):
        d.text((56, y), linha, font=fonte("InterDisplay-Bold.otf", 84), fill=BRANCO); y += 96
    y += 24
    for linha in quebrar(sub, fonte("Inter-Regular.otf", 36), W - 112):
        d.text((56, y), linha, font=fonte("Inter-Regular.otf", 36), fill=(214, 236, 228)); y += 50
    # mosaico: 171 quadrados, mesmas cores do site
    cor = {"nominal": (92, 200, 168), "simbolica": (74, 106, 96), "comissoes": (224, 168, 74), "sem-registro": None}
    lado, gap, cols = 30, 6, 17
    x0, y0 = 56, max(y + 60, 760)
    for i, m in enumerate(mosaico):
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

def miniatura(abertura):
    """Recorte quadrado do mosaico da abertura, com o símbolo de play (para o botão da página inicial)."""
    caixa = Image.new("RGB", (240, 240), VERDE_ESC)
    caixa.paste(abertura.crop((46, 750, 678, 1166)).resize((240, 158), Image.LANCZOS), (0, 41))
    d = ImageDraw.Draw(caixa)
    d.ellipse([78, 78, 162, 162], fill=(255, 255, 255))
    d.polygon([(108, 96), (108, 144), (148, 120)], fill=VERDE)
    return caixa

# ---------------------------------------------------------------- ações no navegador
async def tela(pg):
    from io import BytesIO
    return Image.open(BytesIO(await pg.screenshot())).convert("RGB")

async def quadro(pg, f, dur=1 / FPS):
    f.add(await tela(pg), dur)

async def segurar(pg, f, s):
    f.add(await tela(pg), s)

async def ler(pg, f):
    """Segura a tela até dar tempo de ler a legenda."""
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

# ---------------------------------------------------------------- roteiro gravado
async def gravar(f):
    base = f"http://127.0.0.1:{PORTA}/"
    async with async_playwright() as p:
        nav = await p.chromium.launch()
        ctx = await nav.new_context(viewport={"width": VW, "height": VH}, device_scale_factor=ESC,
                                    is_mobile=True, has_touch=False, color_scheme="light", locale="pt-BR",
                                    permissions=["clipboard-read", "clipboard-write"])
        pg = await ctx.new_page()

        # 1. Início: o mosaico
        await pg.goto(base + "index.html"); await pg.wait_for_load_state("load")
        f.legenda("inicio")
        await segurar(pg, f, 1.6)
        await rolar_para(pg, f, ".mosaico", margem=150)
        await ler(pg, f)
        f.legenda("cores")
        await rolar_para(pg, f, ".legenda", margem=230, passos=8)
        await ler(pg, f)
        # 2. Abrir uma lei: o primeiro quadrado verde (regra fixa, sem escolha de tema)
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
        # 3. Acervo: busca
        f.legenda("busca")
        await menu(pg, f, "Acervo")
        campo = pg.locator("#q")
        await toque(pg, f, campo)
        await digitar(pg, f, campo, ROTEIRO["exemplo_busca"])
        await segurar(pg, f, 0.6)
        await rolar_para(pg, f, "#contagem", margem=200, passos=10)
        await ler(pg, f)
        # 4. Filtros
        f.legenda("filtros")
        await rolar_ate(pg, f, 0, 8)
        await campo.fill(""); await campo.dispatch_event("input"); await pg.wait_for_timeout(300)
        await quadro(pg, f, 0.4)
        await toque(pg, f, pg.locator("details.filtros > summary"))
        await rolar_para(pg, f, "details.filtros", margem=20, passos=10)
        sel = pg.locator('select[data-filtro="data-sit"]')
        await toque(pg, f, sel, clicar=False)
        await sel.select_option("nominal"); await pg.wait_for_timeout(300)
        await quadro(pg, f, 0.5)
        await rolar_para(pg, f, "#contagem", margem=260, passos=8)
        await ler(pg, f)
        # 5. Seleção e PDF
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
        # 6. Votações
        f.legenda("votacoes")
        await menu(pg, f, "Votações")
        await rolar_para(pg, f, ".cartao", margem=20, passos=14)
        await toque(pg, f, pg.locator(".cartao details.mais > summary").first)
        await rolar_para(pg, f, ".cartao details.mais", margem=200, passos=10)
        await ler(pg, f)
        # 7. Entenda
        f.legenda("entenda")
        await menu(pg, f, "Entenda")
        await rolar_para(pg, f, "#caminho", margem=16, passos=14)
        await ler(pg, f)
        # 8. Compartilhar
        f.legenda("compartilhar")
        await menu(pg, f, "Compartilhar")
        await rolar_para(pg, f, ".cartao", margem=16, passos=12)
        await toque(pg, f, pg.locator(".cartao [data-copiar]").first, clicar=False)
        await ler(pg, f)
        # 9. Baixar
        f.legenda("baixar")
        await menu(pg, f, "Baixar")
        await ler(pg, f)
        await nav.close()

def servidor():
    class Silencioso(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass
    s = http.server.ThreadingHTTPServer(("127.0.0.1", PORTA), functools.partial(Silencioso, directory=RAIZ))
    threading.Thread(target=s.serve_forever, daemon=True).start()
    return s

def main():
    mosaico = json.load(open(os.path.join(RAIZ, "dados", "mosaico.json"), encoding="utf-8"))
    pasta = tempfile.mkdtemp(prefix="video-")
    f = Filme(pasta)
    abertura = cartao(ROTEIRO["titulo"], ROTEIRO["subtitulo"], "Vídeo sem som, com legendas", mosaico)
    f.add_img(abertura, 3.2)
    s = servidor()
    try:
        asyncio.run(gravar(f))
    finally:
        s.shutdown()
    f.add_img(cartao(ROTEIRO["fim_titulo"], ROTEIRO["fim_texto"], ROTEIRO["endereco"], mosaico), 4.5)
    f.montar()
    capa = abertura.copy()
    capa.resize((540, 960), Image.LANCZOS).save(SAIDA_CAPA, quality=78, optimize=True, progressive=True)
    miniatura(abertura).save(SAIDA_MINI, quality=80, optimize=True)
    shutil.rmtree(pasta)
    json.dump({"duracao_s": round(f.t, 1), "bytes": os.path.getsize(SAIDA_MP4)},
              open(os.path.join(RAIZ, "dados", "video.json"), "w", encoding="utf-8"))
    print(f"Vídeo: {f.t:.1f} s, {os.path.getsize(SAIDA_MP4) / 1024 / 1024:.2f} MB -> {SAIDA_MP4}")

if __name__ == "__main__":
    main()
