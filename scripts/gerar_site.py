# -*- coding: utf-8 -*-
"""Gera o site estático do Projeto Democracia Brasil a partir da pasta dados/.

Uso:  python3 scripts/gerar_site.py      (rodar na raiz do site)
Entradas: dados/pesquisas.json (cadastro das pesquisas e dos seus arquivos de dados), temas.json, posts.json, novidades.json, videos.json
Saídas:   index.html, acervo.html, votacoes.html, entenda.html, compartilhar.html, baixar.html, resumo.html, como-usar.html
"""
import functools, json, os, html, unicodedata
from urllib.parse import quote
from datetime import date

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def dados(n):
    return json.load(open(os.path.join(RAIZ, "dados", n + ".json"), encoding="utf-8"))

POSTS, NOV, TEMAS = dados("posts"), dados("novidades"), dados("temas")
CFG = dados("config")
_CAD = dados("pesquisas")
PESQ = _CAD["pesquisas"]
NT = len(TEMAS)   # o projeto cobre todos os temas de temas.json; nenhum tema é a identidade do site
def num_tema(p):
    for i, (t, _) in enumerate(TEMAS, 1):
        if t.startswith(p["tema"]):
            return i
    raise SystemExit(f"O tema da pesquisa {p['id']} ({p['tema']}) não está em temas.json.")
def rotulo_tema(p):
    return f"Tema {num_tema(p)} de {NT}"
if _CAD.get("total_temas") != NT:
    raise SystemExit(f"pesquisas.json diz total_temas={_CAD.get('total_temas')}, mas temas.json tem {NT} temas.")
for _p in PESQ:
    if _p.get("numero_tema") != num_tema(_p):
        raise SystemExit(f"pesquisas.json: numero_tema de {_p['id']} deveria ser {num_tema(_p)}.")
_CACHE = {}
def carregar(p):
    """Dados de uma pesquisa do cadastro: atos, mosaico, lacunas e meta."""
    if p["id"] not in _CACHE:
        _CACHE[p["id"]] = {k: json.load(open(os.path.join(RAIZ, "dados", arq), encoding="utf-8")) for k, arq in p["dados"].items()}
    return _CACHE[p["id"]]
def _dma(d):
    dd, mm, aa = d.split("/"); return (aa, mm, dd)
# data da atualização mais recente entre as pesquisas publicadas (aparece no topo de todas as páginas)
ATUALIZADO = max((carregar(p)["meta"]["atualizado"] for p in PESQ), key=_dma)
VIDEOS = dados("videos")
_VM = dados("video") if os.path.exists(os.path.join(RAIZ, "dados", "video.json")) else {}
# só entram na página os vídeos já gravados (com duração e tamanho em dados/video.json)
VID = {v["id"]: dict(v, **_VM[v["id"]]) for v in VIDEOS["videos"] if isinstance(_VM.get(v["id"]), dict)}
def duracao(seg):
    m, s = divmod(round(seg), 60)
    return f"{m} min {s} s" if m and s else (f"{m} min" if m else f"{s} s")
def mb(b):
    return f"{b / 1024 / 1024:.1f} MB".replace(".", ",")
URL = CFG.get("url_site", "").rstrip("/")
def milhar(n):
    return f"{n:,}".replace(",", ".")
e = lambda s: html.escape(str(s or ""), quote=True)
MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
def br(d):
    y, m, dd = d[:10].split("-"); return f"{dd}/{m}/{y}"
def extenso(d):
    y, m, dd = d[:10].split("-"); return f"{int(dd)} de {MESES[int(m)-1]} de {y}"
def norm(s):
    return unicodedata.normalize("NFD", s or "").encode("ascii", "ignore").decode().lower()

SIT = {"nominal": ("Voto nominal registrado", "s-nominal"),
       "simbolica": ("Votação simbólica", "s-simbolica"),
       "comissoes": ("Decidida nas comissões", "s-comissoes"),
       "sem-registro": ("Sem registro nas bases abertas", "s-sem-registro")}
MENU = [("index.html", "Início"), ("acervo.html", "Acervo"), ("votacoes.html", "Votações"), ("entenda.html", "Entenda"),
        ("compartilhar.html", "Compartilhar"), ("baixar.html", "Baixar")]

# Orientação mostrada no topo de cada página (o topo é igual em todas as páginas)
NOMES = dict(MENU, **{"como-usar.html": "Como usar", "resumo.html": "Resumo"})
DICAS = {
    "index.html": "Os 12 temas do projeto e o resultado da pesquisa mais recente, com achado, números e downloads.",
    "pesquisa": "Resultado completo da pesquisa: achado, números, assuntos, linha do tempo, decisões e votações.",
    "acervo.html": "Busque, escolha os itens (um a um ou “Selecionar todos”) e toque em “Resumo visual” para ver e baixar o painel.",
    "votacoes.html": "Veja como cada lei foi votada e o placar por partido.",
    "entenda.html": "O caminho de uma lei e os termos usados no site, em linguagem simples.",
    "compartilhar.html": "Copie um texto pronto, sempre com a fonte oficial.",
    "baixar.html": "Baixe o resumo em PDF, a planilha, os dados e os vídeos.",
    "como-usar.html": "Orientações de acesso, vídeos curtos e onde está cada coisa.",
    "resumo.html": "Resumo de uma pesquisa, também disponível em PDF.",
}

def versao(rel):
    """Marca de versão do arquivo (8 letras do hash), para o navegador não usar estilo ou script antigos depois de uma atualização."""
    import hashlib
    return hashlib.md5(open(os.path.join(RAIZ, rel), "rb").read()).hexdigest()[:8]

def pagina(arquivo, titulo, descricao, corpo, js=False):
    atual = ' aria-current="page"'
    menu = "".join(f'<a href="{h}"{atual if h == arquivo else ""}>{n}</a>' for h, n in MENU)
    ajuda = f'<a class="ajuda" href="como-usar.html"{atual if arquivo == "como-usar.html" else ""}><span aria-hidden="true">?</span>Como usar</a>'
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(titulo)}</title>
<meta name="description" content="{e(descricao)}">
<meta property="og:title" content="{e(titulo)}">
<meta property="og:description" content="{e(descricao)}">
<meta name="theme-color" content="#084a3d">
<link rel="icon" href="assets/icone.svg" type="image/svg+xml">
<link rel="stylesheet" href="assets/estilo.css?v={versao('assets/estilo.css')}">
</head>
<body>
<a class="pular" href="#conteudo">Pular para o conteúdo</a>
<header class="topo">
<div class="topo-marca"><div class="coluna">
<a class="marca-site" href="index.html">Projeto Democracia Brasil<span class="marca-sub">Políticas públicas desde 1985 · {NT} temas</span></a>
{ajuda}
</div></div>
<nav class="menu" aria-label="Seções"><div class="coluna">{menu}</div></nav>
<div class="orientacao"><div class="coluna"><span class="voce">Você está em <strong>{NOMES.get(arquivo, "Resumo" if arquivo.startswith("resumo") else ("Resultado da pesquisa" if arquivo.startswith("pesquisa-") else ""))}</strong>.</span> {DICAS.get(arquivo, DICAS["resumo.html"] if arquivo.startswith("resumo") else (DICAS["pesquisa"] if arquivo.startswith("pesquisa-") else ""))}{"" if arquivo == "como-usar.html" else ' <a href="como-usar.html#videos">Ver os vídeos de ajuda</a>'}</div></div>
<div class="aviso"><div class="coluna">Versão preliminar. Os dados publicados ainda passam por checagem final. Atualizado em {ATUALIZADO}.</div></div>
</header>
<main id="conteudo"><div class="coluna">
{corpo}
</div></main>
<footer class="rodape"><div class="coluna">
<p>O Projeto Democracia Brasil levanta as políticas públicas federais de {NT} temas desde 1985, com o mesmo método. Cada tema é publicado quando a sua pesquisa termina. <a href="index.html#temas">Veja a situação de cada tema</a>.</p>
<p>Dados de fontes oficiais: Planalto, Câmara dos Deputados, Senado Federal e Supremo Tribunal Federal. Cada item traz o link para a sua fonte.</p>
<p>Ao reutilizar, cite o Projeto Democracia Brasil e a fonte original. Encontrou um erro? <a href="como-usar.html#erro">Veja como avisar</a>.</p>
<p><a href="como-usar.html">Como usar o site: orientações de acesso e vídeos</a></p>
</div></footer>
{f'<script src="assets/app.js?v={versao("assets/app.js")}" defer></script>' if js else ''}
</body>
</html>
"""

def carimbo(sit):
    if not sit:
        return ""
    rot, cls = SIT[sit]
    return f'<span class="carimbo"><i class="{cls}" aria-hidden="true"></i>{rot}</span>'

def legenda():
    itens = "".join(f'<li><i class="{c}" aria-hidden="true"></i>{r}</li>' for k, (r, c) in SIT.items())
    return f'<ul class="legenda">{itens}</ul>'

# ---------------------------------------------------------------- index
def cartao_video(v):
    """Um vídeo de ajuda: só baixa quando a pessoa abre e toca (preload=none, capa carregada ao abrir)."""
    passos = "".join(f"<li><strong>{e(c['pagina'])}.</strong> {e(c['texto'])}</li>" for c in v["cenas"])
    vid = v["id"]
    return f"""<details class="video-tutorial" id="video-{vid}">
<summary><img src="assets/video-{vid}-mini.jpg" alt="" width="64" height="64"><span><strong>{e(v['titulo'])}</strong><br><span class="pequeno">{e(v['chamada'])} {duracao(v['duracao_s'])}, sem som.</span></span></summary>
<div class="video-caixa">
<video controls preload="none" playsinline data-poster="assets/video-{vid}-capa.jpg" width="540" height="960" aria-describedby="roteiro-{vid}">
<source src="assets/video-{vid}.mp4" type="video/mp4">
Seu navegador não toca este vídeo. <a href="assets/video-{vid}.mp4">Baixe o vídeo</a>.
</video>
<p class="pequeno"><a href="assets/video-{vid}.mp4" download>Baixar o vídeo</a> ({mb(v['bytes'])}). Sem som, com legendas.</p>
<details class="mais" id="roteiro-{vid}"><summary>Ler o que o vídeo mostra</summary><ol>{passos}</ol></details>
</div>
</details>"""

def bloco_videos(publico=None):
    vs = [v for v in VID.values() if publico is None or v["publico"] == publico]
    return f'<div class="videos">{"".join(cartao_video(v) for v in vs)}</div>' if vs else ""

def contagem_mosaico(d):
    return {k: sum(1 for m in d["mosaico"] if m["situacao"] == k) for k in SIT}

def texto_resumo(p, d):
    """Texto para compartilhar (até 500 caracteres), montado a partir dos dados. Um fato, sem opinião, com fonte oficial."""
    n, lac = contagem_mosaico(d), d["lacunas"]
    url = url_pesquisa(p)
    return (f"{cabecalho_texto(p)}\n\n"
            f"Desde 1985, das {lac['total']} leis, leis complementares e emendas constitucionais sobre o tema, "
            f"só {lac['com_nominal']} tiveram o voto de cada parlamentar registrado no texto principal. "
            f"As outras: votação simbólica ({n['simbolica']}), só nas comissões ({n['comissoes']}) "
            f"ou sem registro nas bases abertas ({n['sem-registro']}).\n\n"
            f"Fonte: {p.get('fonte_congresso', 'https://dadosabertos.camara.leg.br')}\n"
            f"Resumo: {url}")

def cabecalho_texto(p, sub=None):
    """Primeira linha de todo texto para compartilhar: o projeto, o número do tema e a situação."""
    return f"Projeto Democracia Brasil · {rotulo_tema(p)}: {p['tema']} ({p['situacao'].lower()})" + (f" — {sub}." if sub else ".")

def bloco_mosaico(p, d, toque=True):
    mos = d["mosaico"]
    acervo = p["paginas"]["acervo"]
    celulas = "".join(f'<a class="{SIT[m["situacao"]][1]}" href="{acervo}#{e(m["id"])}" title="{e(m["ato"])}: {e(SIT[m["situacao"]][0].lower())}" aria-label="{e(m["ato"])}, {e(SIT[m["situacao"]][0].lower())}"></a>' for m in mos)
    anos = [m["ano"] for m in mos]
    n = contagem_mosaico(d)
    return f"""<p>Cada quadrado é uma lei, lei complementar ou emenda constitucional aprovada desde {min(anos)}, em ordem de data.{" Toque em um quadrado para ver a lei." if toque else ""}</p>
<div class="mosaico" role="list" aria-label="Leis em ordem de data">{celulas}</div>
<div class="eixo" aria-hidden="true"><span>{min(anos)}</span><span>{max(anos)}</span></div>
{legenda()}
<p class="destaque-num">Só {d['lacunas']['com_nominal']} das {d['lacunas']['total']} tiveram o voto de cada parlamentar registrado no texto principal.</p>
<p>As outras foram aprovadas por votação simbólica ({n['simbolica']}), decididas nas comissões ({n['comissoes']}) ou não têm registro nas bases abertas ({n['sem-registro']}). Nesses casos, não é possível saber como cada deputado ou senador votou.</p>"""

def slug(t):
    return "-".join("".join(c if c.isalnum() else " " for c in norm(t)).split())

SELO_TIPO = {"STF": ("Decisão do STF", "stf"), "Decreto": ("Decreto", "outro"), "Constituição": ("Constituinte", "outro")}
def selo(x):
    sit = x.get("situacao")
    if sit:
        return f'<span class="selo {SIT[sit][1][2:]}">{e(SIT[sit][0])}</span>'
    rot, cls = SELO_TIPO.get(x["tipo"], (x["tipo"], "outro"))
    if x.get("escopo") == "Tratado internacional":
        rot = "Tratado internacional"
    return f'<span class="selo {cls}">{e(rot)}</span>'

def url_pesquisa(p):
    return f"{URL}/pesquisa-{p['id']}.html" if URL else f"pesquisa-{p['id']}.html"

def texto_assunto(p, d, sub):
    """Texto curto para compartilhar um assunto da pesquisa (até 500 caracteres), gerado dos dados."""
    atos = [a for a in d["atos"] if a["subtema"] == sub]
    leis = [a for a in atos if a.get("situacao")]
    nom = sum(1 for a in leis if a["situacao"] == "nominal")
    ano = min(a["ano"] for a in atos)
    t = (f"{cabecalho_texto(p, sub)}\n\n"
         f"O levantamento reúne {len(atos)} atos federais sobre o assunto desde {ano}. ")
    if leis:
        quantas = "nenhuma teve" if nom == 0 else (f"{nom} teve" if nom == 1 else f"{nom} tiveram")
        t += (f"Das {len(leis)} leis aprovadas no Congresso, {quantas} o voto de cada parlamentar registrado "
              f"na votação do texto principal.")
    t += f"\n\nFonte: {p.get('fonte_congresso', 'https://dadosabertos.camara.leg.br')}\nResumo: {url_pesquisa(p)}#assunto-{slug(sub)}"
    return t

def botoes_compartilhar(id_texto, texto):
    zap = "https://wa.me/?text=" + quote(texto)
    return (f'<div class="acoes"><a class="botao zap" href="{e(zap)}" target="_blank" rel="noopener">Enviar no WhatsApp</a>'
            f'<button type="button" data-copiar="{id_texto}">Copiar</button></div>')

def resultado_completo(p, nivel_titulo="h1"):
    """Resultado completo de uma pesquisa, gerado só a partir dos dados: abertura, faixa das últimas normas,
    principal achado, números, assuntos, linha do tempo, STF, votações nominais, downloads e limites."""
    d = carregar(p)
    atos, meta, lac = d["atos"], d["meta"], d["lacunas"]
    vot = d.get("votacoes", [])
    pg = p["paginas"]
    n = contagem_mosaico(d)
    pid = p["id"]
    anos = [a["ano"] for a in atos]
    texto = texto_resumo(p, d)
    if len(texto) > 500:
        raise SystemExit(f"Texto para compartilhar de {pid} tem {len(texto)} caracteres (máximo 500).")

    # faixa: as normas mais recentes
    recentes = sorted(atos, key=lambda a: a["data"], reverse=True)[:12]
    itens = "".join(f'<a href="{pg["acervo"]}#{e(a["id"])}"><i class="{e(a.get("situacao") or "outro")}" aria-hidden="true"></i><b>{br(a["data"])[3:]}</b>{e(a["ato"])} · {e(a["resumo"][:70] + ("…" if len(a["resumo"]) > 70 else ""))}</a>' for a in recentes)
    faixa = f'<div class="faixa" role="region" aria-label="Normas mais recentes da pesquisa"><div class="trilho">{itens}<span aria-hidden="true" style="display:contents">{itens.replace("<a ", "<a tabindex=\"-1\" ")}</span></div></div>'

    # números
    n_stf = sum(1 for a in atos if a["tipo"] == "STF")
    n_dec = sum(1 for a in atos if a["tipo"] == "Decreto")
    numeros = [
        (milhar(meta["total_atos"]), "atos federais no levantamento", "Planalto, Câmara, Senado e STF"),
        (lac["total"], "leis aprovadas no Congresso", "Planalto"),
        (lac["com_nominal"], "com o voto de cada parlamentar registrado", "Dados abertos da Câmara e do Senado"),
        (milhar(meta["total_votacoes"]), "votações em Plenário", "Dados abertos da Câmara e do Senado"),
        (milhar(meta["total_votos"]), "votos individuais de parlamentares", "Dados abertos da Câmara e do Senado"),
        (n_stf, "decisões do STF", "Supremo Tribunal Federal"),
    ]
    if n_dec:
        numeros.append((n_dec, "decretos", "Planalto"))
    lis_num = "".join(f"<li><strong>{v}</strong><span>{e(r)}</span><em>Fonte: {e(f)}</em></li>" for v, r, f in numeros[:6])

    # assuntos
    subs = sorted({a["subtema"] for a in atos}, key=lambda s_: -sum(1 for a in atos if a["subtema"] == s_))
    cards = []
    for sub in subs:
        da = sorted([a for a in atos if a["subtema"] == sub], key=lambda a: a["data"], reverse=True)
        leis = [a for a in da if a.get("situacao")]
        nom = sum(1 for a in leis if a["situacao"] == "nominal")
        tx = texto_assunto(p, d, sub)
        if len(tx) > 500:
            raise SystemExit(f"Texto do assunto {sub} tem {len(tx)} caracteres (máximo 500).")
        ult = da[0]
        fatos = "".join(f'<li><a href="{pg["acervo"]}#{e(a["id"])}">{e(a["ato"])}</a> ({a["ano"]}): {e(a["resumo"])} <a href="{e(a["link"])}" rel="noopener">texto oficial</a></li>' for a in da[:5])
        if leis:
            dado = f'<div class="dado"><span class="n">{nom} de {len(leis)}</span>leis do assunto aprovadas no Congresso tiveram o voto de cada parlamentar registrado.<span class="fonte">Fonte: dados abertos da Câmara e do Senado ↗</span></div>'
        else:
            dado = f'<div class="dado"><span class="n">{len(da)}</span>atos, nenhum deles lei votada no Congresso.<span class="fonte">Fonte: Planalto e STF</span></div>'
        sid = f"t-assunto-{slug(sub)}"
        cards.append(f"""<article class="ccard" id="assunto-{slug(sub)}">
<p class="rotulo">{len(da)} atos · desde {min(a["ano"] for a in da)}</p>
<h3>{e(sub)}</h3>
<p class="chamada">Mais recente: {e(ult["ato"])}, de {br(ult["data"])}.</p>
{dado}
<div class="recente"><b>O que diz a mais recente</b>{e(ult["resumo"])}</div>
<details class="mais"><summary>Fatos e fontes</summary><ul class="fatos">{fatos}</ul>
<p class="pequeno"><a href="{pg['acervo']}?assunto={quote(sub)}">Ver os {len(da)} atos no acervo</a></p></details>
<p class="post" id="{sid}" hidden>{e(tx)}</p>
{botoes_compartilhar(sid, tx)}
<p class="status" role="status"></p>
</article>""")

    # linha do tempo
    marcos = [a for a in atos if a["ato"] in p.get("marcos", [])]
    marcos.sort(key=lambda a: a["data"])
    tempo = "".join(f'<li><time datetime="{a["data"]}">{br(a["data"])}</time><div><div class="t-ato"><a href="{pg["acervo"]}#{e(a["id"])}">{e(a["ato"])}</a></div><p>{e(a["resumo"])}</p>{selo(a)} <span class="pequeno">Governo {e(a["governo"])}</span></div></li>' for a in marcos)

    # STF
    stf = sorted([a for a in atos if a["tipo"] == "STF"], key=lambda a: a["data"], reverse=True)
    stf_cards = "".join(f"""<article class="ccard stf">
<p class="rotulo">STF · {e((a.get("stf") or {}).get("caso") or a["ato"])} · {a["ano"]}</p>
<h3>{e(a["resumo"])}</h3>
<div class="fato"><b>Situação: {e((a.get("stf") or {}).get("status") or "—")}</b>{e((a.get("stf") or {}).get("resultado") or "")}</div>
<p class="pequeno"><a href="{pg['acervo']}#{e(a['id'])}">Detalhes, posições e cronologia</a> · <a href="{e(a['link'])}" rel="noopener">Fonte</a></p>
</article>""" for a in stf)

    # votações nominais
    rank = "".join(f"""<li><div><div class="r-titulo">{e(v['ato'])}</div>
<div class="r-meta">{e(v['casa'])} · {br(v['data'])} · {v['sim']} sim · {v['nao']} não{f" · {v['abst']} abst." if v['abst'] else ""}{f" · {v['obst']} obstr." if v['obst'] else ""}</div>
{barra(v['sim'], v['nao'], v['abst'], v['obst'])}
{'<p class="nota">Esta lei alterou uma regra anterior (afastamento da gestante, Lei 14.151/2021). Votar sim aqui significa aprovar essa alteração.</p>' if v.get('revisar') else ''}
<div class="pequeno"><a href="{e(v['fonte'])}" rel="noopener">Tramitação oficial</a> · <a href="{e(v['dados_abertos'])}" rel="noopener">Dados abertos</a></div></div></li>""" for v in sorted(vot, key=lambda v: v["data"], reverse=True))

    H = nivel_titulo
    return f"""<section class="resultado" id="pesquisa-{pid}" aria-labelledby="titulo-{pid}">
<div class="r-abertura">
<div><p class="rotulo">{rotulo_tema(p)} · {e(p['situacao'])} · atualizada em {e(meta['atualizado'])}</p>
<{H} id="titulo-{pid}">{e(p['titulo'])}</{H}></div>
<div class="contador" aria-label="{meta['total_atos']} atos no levantamento"><strong>{meta['total_atos']}</strong><span>atos</span></div>
<p class="lead">{e(p['chamada'])}</p>
</div>
<nav class="sumario" aria-label="Partes do resultado"><a href="#achado-{pid}">Achado</a><a href="#numeros-{pid}">Números</a><a href="#assuntos-{pid}">Assuntos</a><a href="#tempo-{pid}">Linha do tempo</a>{f'<a href="#stf-{pid}">STF</a>' if stf else ''}{f'<a href="#votos-{pid}">Votações</a>' if vot else ''}<a href="#baixar-{pid}">Baixar</a></nav>
{faixa}

<div class="achado" id="achado-{pid}">
<p class="rotulo">Principal achado</p>
<p class="grande">{lac['com_nominal']} <small>de {lac['total']}</small></p>
<p>leis aprovadas no Congresso tiveram o voto de cada parlamentar registrado na votação do texto principal. As outras foram aprovadas por votação simbólica ({n['simbolica']}), decididas nas comissões ({n['comissoes']}) ou não têm registro nas bases abertas ({n['sem-registro']}). Sem registro nominal, não dá para saber como cada parlamentar votou, e isso não indica apoio nem oposição.</p>
<div class="painel">
<p class="pequeno">Cada quadrado é uma lei, em ordem de data, de {min(m["ano"] for m in d["mosaico"])} a {max(m["ano"] for m in d["mosaico"])}. Toque em um quadrado para ver a lei.</p>
<div class="mosaico" role="list" aria-label="Leis em ordem de data">{"".join(f'<a class="{SIT[m["situacao"]][1]}" href="{pg["acervo"]}#{e(m["id"])}" title="{e(m["ato"])}: {e(SIT[m["situacao"]][0].lower())}" aria-label="{e(m["ato"])}, {e(SIT[m["situacao"]][0].lower())}"></a>' for m in d["mosaico"])}</div>
<div class="eixo" aria-hidden="true"><span>{min(m["ano"] for m in d["mosaico"])}</span><span>{max(m["ano"] for m in d["mosaico"])}</span></div>
{legenda()}
<p class="pequeno"><a href="{pg['votacoes']}">Como o Congresso votou</a> · <a href="entenda.html#votacao">Votação nominal ou simbólica?</a></p>
</div>
</div>

<h2 id="numeros-{pid}">Em números</h2>
<ul class="grade-numeros">{lis_num}</ul>

<h2 id="assuntos-{pid}">Assuntos</h2>
<p class="pequeno">Um cartão por assunto, do que tem mais atos para o que tem menos. Deslize para o lado.</p>
<div class="carrossel">{"".join(cards)}</div>

<h2 id="tempo-{pid}">Linha do tempo</h2>
<p class="pequeno">Marcos da pesquisa, com a forma como cada um foi aprovado.</p>
<ol class="tempo">{tempo}</ol>

{f'<h2 id="stf-{pid}">No Supremo</h2><p class="pequeno">Decisões do STF ligadas ao tema, com a situação atual.</p><div class="carrossel">{stf_cards}</div>' if stf else ''}

{f'<h2 id="votos-{pid}">Votações com voto registrado</h2><p class="pequeno">Votações nominais do texto principal das leis do núcleo do tema, da mais recente para a mais antiga. Uma lei pode ter mais de uma votação (por exemplo, os dois turnos de uma emenda constitucional em cada Casa). Votar sim significa aprovar o texto que virou lei.</p><ol class="ranking">{rank}</ol>' if vot else ''}

<h2 id="baixar-{pid}" class="so-tela">Baixar e compartilhar</h2>
<div class="acoes-pesquisa">
<a class="botao cheio" href="{p['pdf']}" download>Resumo em PDF (texto) <span class="pequeno">({tamanho(p['pdf'])})</span></a>
<button type="button" data-imprimir="pesquisa-{pid}">Painel em PDF (visual)</button>
<a class="botao zap" href="{e('https://wa.me/?text=' + quote(texto))}" target="_blank" rel="noopener">Enviar no WhatsApp</a>
<button type="button" data-copiar="texto-{pid}" data-share>Compartilhar</button>
<button type="button" data-copiar="texto-{pid}">Copiar texto</button>
<a class="botao" href="{p['planilha']}" download>Planilha com todos os dados</a>
</div>
<p class="status" id="status-{pid}" role="status"></p>
<details class="mais"><summary>Ler o texto para compartilhar ({len(texto)} caracteres)</summary><p class="post" id="texto-{pid}">{e(texto)}</p></details>

<div class="limites"><strong>Limites.</strong>
<ul>
<li>Esta pesquisa trata de um dos {NT} temas do projeto ({e(p['tema'].lower())}). Os números valem só para este tema.</li>
<li>Versão preliminar: os dados ainda passam por checagem final.</li>
<li>A lista vem das ementas publicadas no Planalto; leis cuja ementa não cita o tema podem faltar.</li>
<li>A Câmara não tem votos individuais nas bases abertas antes de 2005.</li>
<li>Contar leis por governo não mede importância nem efeito; por isso não há ranking de governos.</li>
</ul>
<p class="pequeno">Fontes: Planalto (legislação), dados abertos da Câmara e do Senado, Supremo Tribunal Federal. Cada item tem o link da sua fonte no <a href="{pg['acervo']}">acervo</a>. Método completo no <a href="downloads/guia_metodologico.md">guia metodológico</a>.</p>
</div>
</section>"""

def pesquisa_destaque():
    return next((p for p in PESQ if p.get("destaque")), PESQ[0])

def gerar_pesquisa(p):
    corpo = resultado_completo(p) + '\n<p><a href="index.html">Voltar para o início</a></p>'
    return pagina(f"pesquisa-{p['id']}.html", f"{p['titulo']} — Projeto Democracia Brasil", p["chamada"], corpo, js=True)

def pesquisa_do_tema(t):
    return next((x for x in PESQ if t.startswith(x["tema"])), None)

def nota_temas():
    """Aviso das páginas de consulta: quais temas já foram publicados e quantos faltam."""
    pub = [p for p in PESQ]
    nomes = ", ".join(f"{e(p['tema'])} (tema {num_tema(p)})" for p in pub)
    falta = NT - len(pub)
    return (f'<p class="nota nota-tema"><strong>Temas publicados: {len(pub)} de {NT}.</strong> {nomes}. '
            f'{"Os outros " + str(falta) + " temas entram aqui quando as pesquisas forem publicadas. " if falta else ""}'
            f'<a href="index.html#temas">Ver os {NT} temas</a></p>')

def gerar_index():
    dest = pesquisa_destaque()
    outras = [p for p in PESQ if p is not dest]
    def cartao_tema(i, t):
        p = pesquisa_do_tema(t)
        if p:
            return (f'<li class="publicado"><a href="pesquisa-{p["id"]}.html"><span class="num">Tema {i:02d}</span>'
                    f'<span class="nome">{e(t)}</span><span class="situ">Publicado · {e(p["situacao"].lower())}</span></a></li>')
        return f'<li><span class="num">Tema {i:02d}</span><span class="nome">{e(t)}</span><span class="situ">A pesquisar</span></li>'
    temas = "".join(cartao_tema(i, t) for i, (t, st) in enumerate(TEMAS, 1))
    n_pub = len({p["tema"] for p in PESQ})
    # o cadastro segue a ordem de publicação; a primeira pesquisa marcada como piloto aparece como tal
    primeira = PESQ[0] if PESQ and "piloto" in PESQ[0]["situacao"].lower() else None
    novs = "".join(f"<li><strong>{br(x['data'])}</strong>: {e(x['texto'])}</li>" for x in NOV)
    bloco_outras = ""
    if outras:
        bloco_outras = '<h2>Outras pesquisas publicadas</h2><div class="outras">' + "".join(
            f'<a class="cartao" href="pesquisa-{p["id"]}.html"><span class="selo-pesquisa">{rotulo_tema(p)} · {e(p["situacao"])}</span><h3>{e(p["titulo"])}</h3><p>{e(p["chamada"])}</p></a>' for p in outras) + "</div>"
    corpo = f"""
<section class="projeto" id="temas" aria-labelledby="titulo-projeto">
<div class="r-abertura">
<div><p class="rotulo">O projeto · desde 15/03/1985</p>
<h1 id="titulo-projeto">Políticas públicas no Brasil, tema por tema</h1></div>
<div class="contador" aria-label="{n_pub} de {NT} temas publicados"><strong>{n_pub}/{NT}</strong><span>temas publicados</span></div>
<p class="lead">Um levantamento verificável das leis, decretos, tratados e decisões da Justiça, no âmbito federal, desde a volta da democracia. São {NT} temas, pesquisados com o mesmo método, um de cada vez. Cada informação tem link para a fonte oficial.</p>
</div>
<ol class="temas" aria-label="Os {NT} temas do projeto">{temas}</ol>
<p class="pequeno">Cada tema é publicado quando a sua pesquisa termina.{f" O primeiro foi {e(primeira['tema'].lower())}, usado como piloto para testar o método." if primeira else ""} O método é o mesmo para todos os temas e está no <a href="downloads/guia_metodologico.md">guia metodológico</a>.</p>
</section>

<div id="painel-selecao" hidden></div>
<div id="resultado-destaque">
<p class="divisor"><span>Última pesquisa publicada</span></p>
{resultado_completo(dest, "h2")}
</div>
{bloco_outras}

<h2 id="videos">Vídeos: como usar</h2>
{bloco_videos()}

<h2 id="novidades">Novidades</h2>
<ul>{novs}</ul>
"""
    return pagina("index.html", "Projeto Democracia Brasil", f"Levantamento verificável das políticas públicas federais no Brasil desde 1985, em {NT} temas, com fontes oficiais.", corpo, js=True)

# ---------------------------------------------------------------- acervo
def todos_os_atos():
    """Atos de todas as pesquisas publicadas, cada um com o tema da sua pesquisa."""
    out = []
    for p in PESQ:
        out += [dict(a, _tema=p["tema"]) for a in carregar(p)["atos"]]
    ids = [a["id"] for a in out]
    if len(ids) != len(set(ids)):
        raise SystemExit("Há atos com o mesmo id em pesquisas diferentes: use prefixos diferentes no cadastro.")
    return out

def item_acervo(x):
    sit = x.get("situacao")
    linhas = []
    def add(rot, val):
        if val:
            linhas.append(f"<dt>{rot}</dt><dd>{val}</dd>")
    add("Tipo", e(x["tipo"]))
    add("Escopo", e(x["escopo"]))
    add("Origem", e(x.get("origem")))
    add("Autor do projeto", e(x.get("autor")))
    add("Projeto", e(x.get("projeto")))
    add("Papel do governo", e(x.get("papel")))
    if x.get("camara"):
        add("Na Câmara", e(x["camara"]) + (f"<br>Placar: {e(x['camara_placar'])}" if x.get("camara_placar") else ""))
    if x.get("senado"):
        add("No Senado", e(x["senado"]) + (f"<br>Placar: {e(x['senado_placar'])}" if x.get("senado_placar") else ""))
    add("Veto", e(x.get("veto")))
    stf = x.get("stf") or {}
    if stf:
        add("Quem propôs", e(stf.get("autor")))
        add("Relator", e(stf.get("relator")))
        add("O que se discute", e(stf.get("objeto")))
        add("Cronologia", e(stf.get("cronologia")))
        add("Resultado", e(stf.get("resultado")))
        add("Posições em disputa", e(stf.get("posicoes")))
        add("Situação", e(stf.get("status")))
    fontes = [f'<a href="{e(x["link"])}" rel="noopener">{"Texto oficial" if x["tipo"] != "STF" else "Fonte da decisão"}</a>']
    if x.get("link_camara"):
        fontes.append(f'<a href="{e(x["link_camara"])}" rel="noopener">Tramitação na Câmara</a>')
    if x.get("link_senado"):
        fontes.append(f'<a href="{e(x["link_senado"])}" rel="noopener">Tramitação no Senado</a>')
    nota = f'<p class="nota">{e(x["nota"])}</p>' if x.get("nota") else ""
    mp = '<span class="etq">Alteração da Lei Maria da Penha</span>' if x.get("maria_da_penha") else ""
    busca = x["ato"].replace(".", "") + (" " + x["projeto"].replace(".", "") if x.get("projeto") else "")
    tema = f'<span class="etq tema">{e(x["_tema"])}</span>' if len(PESQ) > 1 else ""
    return f"""<li id="{e(x['id'])}" data-tema="{e(x['_tema'])}" data-tipo="{e(x['tipo'])}" data-gov="{e(x['governo'].replace(' (referência)', ''))}" data-esc="{e(x['escopo'])}" data-sit="{e(sit or 'nao-se-aplica')}" data-sub="{e(x['subtema'])}" data-mp="{'sim' if x.get('so_historico') else 'nao'}" data-txt="{e(busca)}">
<article>
<h3>{e(x['ato'])}</h3>
<p class="quando">{extenso(x['data'])}. Governo {e(x['governo'])}.</p>
<p>{e(x['resumo'])}</p>
<div class="etiquetas">{carimbo(sit)}{tema}<span class="etq">{e(x['subtema'])}</span>{mp}</div>
<details class="mais"><summary>Detalhes e fontes</summary>
{nota}
<dl class="ficha">{''.join(linhas)}</dl>
<p class="fontes">{''.join(fontes)}</p>
</details>
<div class="acoes"><button type="button" data-selecionar aria-pressed="false">Adicionar à seleção</button><button type="button" data-compartilhar="{e(x['id'])}">Compartilhar</button></div>
</article>
</li>"""

def opcoes(valores):
    return "".join(f'<option value="{e(v)}">{e(v)}</option>' for v in valores)

def gerar_acervo():
    lista = sorted(todos_os_atos(), key=lambda x: x["data"])
    temas = [p["tema"] for p in PESQ]
    tipos = sorted({x["tipo"] for x in lista})
    govs = []
    for x in lista:
        g = x["governo"].replace(" (referência)", "")
        if g not in govs:
            govs.append(g)
    escs = ["Núcleo", "Dispositivo em lei geral", "Relacionado", "Tratado internacional", "Judiciário"]
    subs = sorted({x["subtema"] for x in lista})
    sits = "".join(f'<option value="{k}">{e(r)}</option>' for k, (r, c) in SIT.items())
    itens = "\n".join(item_acervo(x) for x in lista)
    corpo = f"""
<h1>Acervo</h1>
<p class="lead">Leis, decretos, tratados e decisões do STF reunidos pelas pesquisas publicadas do projeto, desde 1985. Toque em "Detalhes e fontes" para ver como cada lei foi aprovada e abrir o texto oficial.</p>
{nota_temas()}
<noscript><p class="nota">A busca precisa de JavaScript. Todos os itens estão abaixo, em ordem de data. Você também pode <a href="baixar.html">baixar a lista completa</a>.</p></noscript>
<form class="busca so-tela" role="search" onsubmit="return false">
<label for="q">Buscar por palavra, número da lei ou ano</label>
<div class="linha-busca"><input id="q" type="search" placeholder="Ex.: feminicídio, 11.340, 2006" autocomplete="off"><button type="button" id="nova-busca">Nova busca</button></div>
<details class="filtros"><summary>Filtrar</summary><div class="grade">
<label>Tema<select data-filtro="data-tema"><option value="">Todos os temas publicados ({len(temas)})</option>{opcoes(temas)}</select></label>
<label>Tipo de ato<select data-filtro="data-tipo"><option value="">Todos</option>{opcoes(tipos)}</select></label>
<label>Governo na data<select data-filtro="data-gov"><option value="">Todos</option>{opcoes(govs)}</select></label>
<label>Assunto<select data-filtro="data-sub"><option value="">Todos</option>{opcoes(subs)}</select></label>
<label>Como foi aprovada<select data-filtro="data-sit"><option value="">Todas</option>{sits}</select></label>
<label>Escopo<select data-filtro="data-esc"><option value="">Todos</option>{opcoes(escs)}</select></label>
{'<label style="display:flex;align-items:center;gap:.5rem"><input type="checkbox" data-filtro="data-mp" checked> Mostrar alterações da Lei Maria da Penha</label>' if any(x.get("so_historico") for x in lista) else ''}
</div></details>
<div class="linha-contagem"><p class="contagem" id="contagem" aria-live="polite"></p><button type="button" id="selecionar-todos" class="pequeno-botao">Selecionar todos</button></div>
<p class="status" id="status-busca" role="status"></p>
</form>
<div class="so-impressao"><h2>Minha seleção</h2><p>Projeto Democracia Brasil. Gerado em <span id="data-impressao"></span>. Versão preliminar.</p></div>
<ol class="acervo" id="lista">
{itens}
</ol>
<p class="status so-tela" id="status" role="status"></p>
<p class="pequeno so-tela">Monte o seu resumo: toque em "Adicionar à seleção" nos itens que interessam, ou em "Selecionar todos" para pegar a lista inteira. Depois toque em "Resumo visual" para ver o painel da sua seleção, baixar em PDF ou enviar no WhatsApp. "Fichas" gera um PDF com a ficha de cada item. A seleção fica guardada só neste navegador.</p>
<div class="barra-selecao so-tela" id="barra-selecao" hidden><div class="coluna">
<strong>Seleção: <span id="n-selecao">0</span></strong>
<button type="button" id="ver-selecao">Ver</button>
<button type="button" id="pdf-selecao" title="PDF com a ficha de cada item">Fichas</button>
<button type="button" id="limpar-selecao">Limpar</button>
<a class="botao cheio" id="resumo-selecao" href="index.html#painel">Resumo visual</a>
</div></div>
"""
    return pagina("acervo.html", "Acervo — Projeto Democracia Brasil", "Busque leis, decretos e decisões reunidos pelas pesquisas do projeto desde 1985, com links para as fontes oficiais.", corpo, js=True)

# ---------------------------------------------------------------- votações
def barra(sim, nao, abst, obst):
    tot = max(sim + nao + abst + obst, 1)
    partes = [("b-sim", sim), ("b-nao", nao), ("b-abst", abst), ("b-obst", obst)]
    return '<div class="barra" aria-hidden="true">' + "".join(f'<span class="{c}" style="width:{v*100/tot:.2f}%"></span>' for c, v in partes if v) + "</div>"

def linha_casa(nome, cont):
    ordem = ["Plenário, votação nominal", "Plenário, votação simbólica", "Só nas comissões", "Sem registro nas bases abertas"]
    cls = ["s-nominal", "s-simbolica", "s-comissoes", "s-sem-registro"]
    tot = sum(cont.values())
    seg = "".join(f'<span class="{c}" style="width:{cont.get(o,0)*100/tot:.2f}%"></span>' for o, c in zip(ordem, cls) if cont.get(o))
    txt = "".join(f"<li>{e(o)}: <strong>{cont.get(o,0)}</strong> ({cont.get(o,0)*100/tot:.0f}%)</li>" for o in ordem)
    return f'<div class="linha-casa"><h3>{nome}</h3><div class="barra" aria-hidden="true">{seg}</div><ul>{txt}</ul></div>'

def gerar_votacoes():
    blocos = []
    for p in PESQ:
        d = carregar(p)
        lac, meta = d["lacunas"], d["meta"]
        cards = []
        for v in d.get("votacoes", []):
            pres = v["sim"] + v["nao"] + v["abst"] + v["obst"]
            linhas = "".join(f'<tr><td>{e(x["partido"])}</td><td class="n">{x["sim"]}</td><td class="n">{x["nao"]}</td><td class="n">{x["abst"]}</td><td class="n">{x["obst"]}</td></tr>' for x in v["partidos"])
            rev = '<p class="nota">Esta lei alterou a regra de afastamento da gestante criada pela Lei 14.151/2021. Votar "sim" aqui significa aprovar essa alteração. A leitura do voto deve considerar esse contexto.</p>' if v.get("revisar") else ""
            cards.append(f"""<div class="cartao">
<h4>{e(v['ato'])}</h4>
<p class="quando">{e(v['casa'])}, {extenso(v['data'])}</p>
<p>{e(v['objeto'])}</p>
{barra(v['sim'], v['nao'], v['abst'], v['obst'])}
<p><strong>{v['sim']}</strong> sim, <strong>{v['nao']}</strong> não{f", <strong>{v['abst']}</strong> abstenções" if v['abst'] else ""}{f", <strong>{v['obst']}</strong> obstruções" if v['obst'] else ""}. {pres} presentes.</p>
{rev}
<details class="mais"><summary>Votos por partido</summary>
<table><thead><tr><th>Partido na data</th><th class="n">Sim</th><th class="n">Não</th><th class="n">Abst.</th><th class="n">Obstr.</th></tr></thead><tbody>{linhas}</tbody></table>
</details>
<p class="fontes"><a href="{e(v['fonte'])}" rel="noopener">Tramitação oficial</a><a href="{e(v['dados_abertos'])}" rel="noopener">Dados abertos da votação</a></p>
</div>""")
        blocos.append(f"""<section class="tema-bloco" id="votacoes-{p['id']}" aria-labelledby="vt-{p['id']}">
<p class="rotulo">{rotulo_tema(p)} · {e(p['situacao'])}</p>
<h2 id="vt-{p['id']}">{e(p['tema'])}</h2>
{linha_casa("Câmara dos Deputados", lac["camara"])}
{linha_casa("Senado Federal", lac["senado"])}
<p class="pequeno">Base: {lac['total']} leis, leis complementares e emendas constitucionais sobre {e(p['assunto'])} aprovadas desde 1985. Fonte: dados abertos da Câmara e do Senado, consultados em {e(meta['atualizado'])}. A Câmara não tem votos individuais nas bases abertas antes de 2005.</p>
<h3>As votações com voto registrado</h3>
<p>São as votações nominais do texto principal das leis do núcleo do tema. Votar "sim" significa aprovar o texto que virou lei. Isso mede apoio ao texto aprovado, não a posição de cada parlamentar sobre {e(p['assunto'])} em geral.</p>
{''.join(cards)}
<p>Quer ver o voto de cada deputado e senador? <a href="baixar.html#baixar-{p['id']}">Baixe a lista de votos nominais deste tema</a>.</p>
</section>""")
    corpo = f"""
<h1>Como o Congresso votou</h1>
<p class="lead">Uma lei pode ser aprovada com o voto de cada parlamentar registrado (votação nominal) ou sem esse registro (votação simbólica ou decisão nas comissões). Só no primeiro caso é possível saber quem votou a favor ou contra.</p>
{nota_temas()}
{legenda()}
{''.join(blocos)}
"""
    return pagina("votacoes.html", "Como o Congresso votou — Projeto Democracia Brasil", "Quantas leis de cada tema publicado tiveram voto nominal e como cada partido votou.", corpo)

# ---------------------------------------------------------------- entenda
def exemplo_votacao():
    """Exemplo com dados da primeira pesquisa publicada, identificado como exemplo de um tema."""
    if not PESQ:
        return ""
    p = PESQ[0]; lac = carregar(p)["lacunas"]
    return (f'<p class="pequeno">Exemplo: na pesquisa do tema {num_tema(p)}, {e(p["tema"].lower())}, só {lac["com_nominal"]} das {lac["total"]} leis aprovadas no Congresso '
            f'tiveram o voto de cada parlamentar registrado no texto principal. <a href="pesquisa-{p["id"]}.html#achado-{p["id"]}">Ver o resultado</a></p>')

def gerar_entenda():
    gloss = [
        ("Lei ordinária", "A lei mais comum. É aprovada pela maioria dos parlamentares presentes."),
        ("Lei complementar", "Lei que trata de temas que a Constituição manda regular assim. Precisa da maioria absoluta: mais da metade de todos os deputados e de todos os senadores."),
        ("Emenda constitucional (PEC)", "Muda a Constituição. Precisa de três quintos dos votos, em dois turnos, na Câmara e no Senado. Não passa pela Presidência: é promulgada pelo próprio Congresso."),
        ("Medida provisória (MP)", "Ato da Presidência que vale como lei imediatamente, por até 120 dias. Para continuar valendo, precisa ser aprovado pelo Congresso."),
        ("Decreto", "Ato da Presidência que regulamenta uma lei ou organiza o governo. Não pode criar obrigações que a lei não prevê."),
        ("Sanção e veto", "Depois de aprovado no Congresso, o projeto vai para a Presidência, que pode aprovar (sancionar) ou recusar (vetar), no todo ou em parte. O Congresso pode derrubar o veto."),
        ("Votação nominal", "Cada parlamentar registra o voto no painel eletrônico. Fica público quem votou sim, não, se absteve ou estava ausente."),
        ("Votação simbólica", "O presidente da sessão pede que quem é contra se manifeste e anuncia o resultado. Não há registro do voto de cada parlamentar."),
        ("Caráter conclusivo e decisão terminativa", "Alguns projetos são decididos só pelas comissões da Câmara (caráter conclusivo) ou do Senado (decisão terminativa), sem ir ao Plenário, se ninguém recorrer."),
        ("Destaque", "Pedido para votar separadamente um trecho do projeto ou uma emenda."),
        ("Requerimento de urgência", "Pedido para que o projeto seja votado mais rápido, pulando prazos."),
        ("ADI, ADC e ADPF", "Ações no Supremo Tribunal Federal que pedem para decidir se uma lei ou ato está de acordo com a Constituição."),
        ("Tratado internacional", "Acordo entre países. Para valer no Brasil, precisa ser aprovado pelo Congresso e promulgado por decreto."),
        ("Núcleo, dispositivo em lei geral e relacionado", "Como classificamos os atos neste site. Núcleo: trata diretamente do tema. Dispositivo em lei geral: lei ampla com um trecho específico sobre o tema. Relacionado: lei geral que afeta o tema, explicada na nota de cada item."),
    ]
    dl = "".join(f"<dt>{e(t)}</dt><dd>{e(d)}</dd>" for t, d in gloss)
    corpo = f"""
<h1>Entenda</h1>
<p class="lead">Como uma lei é feita, o que significam os termos usados neste site e como trabalhamos.</p>

<h2 id="caminho">O caminho de uma lei</h2>
<ol class="passos">
<li><strong>Alguém apresenta o projeto.</strong> Pode ser um deputado ou deputada, um senador ou senadora, uma comissão, a Presidência da República, tribunais ou os próprios cidadãos, com assinaturas (iniciativa popular).</li>
<li><strong>As comissões analisam.</strong> Grupos de parlamentares estudam o projeto e dão parecer. Às vezes, a decisão termina aqui.</li>
<li><strong>O Plenário vota.</strong> Todos os parlamentares da Casa votam, de forma nominal ou simbólica.</li>
<li><strong>A outra Casa revisa.</strong> O que a Câmara aprova vai ao Senado, e o contrário. Se houver mudanças, o texto volta para a Casa onde começou.</li>
<li><strong>A Presidência sanciona ou veta.</strong> Tem 15 dias úteis para decidir.</li>
<li><strong>O Congresso analisa os vetos.</strong> Pode manter ou derrubar.</li>
<li><strong>A lei é publicada</strong> no Diário Oficial da União e passa a valer na data que ela mesma indicar.</li>
</ol>

<h2 id="votacao">Votação nominal ou simbólica: por que isso importa</h2>
<p>Na votação nominal, fica registrado como cada parlamentar votou. Na simbólica, só o resultado. Muitas leis são aprovadas sem registro nominal. Para essas leis, não dá para dizer quem votou a favor ou contra. A falta de registro não significa apoio nem oposição.</p>
{exemplo_votacao()}

<h2>Glossário</h2>
<dl class="glossario">{dl}</dl>

<h2 id="metodo">Como este site trabalha</h2>
<ul>
<li>Toda informação vem de fonte oficial (Planalto, Câmara, Senado, STF, IBGE) ou de pesquisa citada, com link.</li>
<li>Uma lei é atribuída ao governo que estava no poder na data em que foi assinada. Quem propôs aparece separado.</li>
<li>Os textos descrevem fatos, sem adjetivos de valor. Em temas controversos, mostramos as principais posições.</li>
<li>Contar leis não mede a importância nem o efeito de um governo. Por isso não fazemos rankings.</li>
<li>O método completo está no <a href="downloads/guia_metodologico.md">guia metodológico</a>.</li>
</ul>
"""
    return pagina("entenda.html", "Entenda — Projeto Democracia Brasil", "Como uma lei é feita, glossário e método do projeto, em linguagem simples.", corpo)

# ---------------------------------------------------------------- compartilhar
def cartao_post(p):
    fontes = "\n".join(f"Fonte: {u}" for _, u in p["fontes"][:1])
    texto = p["texto"] + "\n\n" + fontes
    if len(texto) > 500:
        raise SystemExit(f"Texto {p['id']} tem {len(texto)} caracteres (máximo 500).")
    links = "".join(f'<a href="{e(u)}" rel="noopener">{e(n)}</a>' for n, u in p["fontes"])
    return f"""<div class="cartao" id="{e(p['id'])}">
<h3>{e(p['titulo'])}</h3>
<p class="post" id="t-{e(p['id'])}">{e(texto)}</p>
<p class="pequeno">{len(texto)} caracteres</p>
<p class="fontes">{links}</p>
<div class="acoes"><button type="button" data-copiar="t-{e(p['id'])}">Copiar texto</button><button type="button" class="cheio" data-copiar="t-{e(p['id'])}" data-share>Compartilhar</button></div>
</div>"""

def gerar_compartilhar():
    blocos = []
    for pq in PESQ:
        dq = carregar(pq)
        texto = texto_resumo(pq, dq)
        blocos.append(f"""<section class="tema-bloco" id="compartilhar-{pq['id']}" aria-labelledby="ct-{pq['id']}">
<p class="rotulo">{rotulo_tema(pq)} · {e(pq['situacao'])}</p>
<h2 id="ct-{pq['id']}">{e(pq['tema'])}</h2>
<div class="cartao" id="resumo-{pq['id']}">
<h3>Resumo da pesquisa</h3>
<p class="post" id="t-resumo-{pq['id']}">{e(texto)}</p>
<p class="pequeno">{len(texto)} caracteres</p>
<p class="fontes"><a href="pesquisa-{pq['id']}.html">Ver o resultado da pesquisa</a><a href="{pq['pdf']}" download>Baixar o resumo em PDF</a></p>
<div class="acoes"><button type="button" data-copiar="t-resumo-{pq['id']}">Copiar texto</button><button type="button" class="cheio" data-copiar="t-resumo-{pq['id']}" data-share>Compartilhar</button></div>
</div>""")
        subs = sorted({a["subtema"] for a in dq["atos"]}, key=lambda s_: -sum(1 for a in dq["atos"] if a["subtema"] == s_))
        itens = "".join(f"""<div class="cartao"><h3>{e(sub)}</h3><p class="post" id="t-{pq['id']}-{slug(sub)}">{e(texto_assunto(pq, dq, sub))}</p>
<p class="pequeno">{len(texto_assunto(pq, dq, sub))} caracteres</p>{botoes_compartilhar(f"t-{pq['id']}-{slug(sub)}", texto_assunto(pq, dq, sub))}<p class="status" role="status"></p></div>""" for sub in subs)
        blocos.append(f'<details class="mais"><summary>Textos por assunto ({len(subs)})</summary>{itens}</details>')
        blocos.append("".join(cartao_post(p) for p in POSTS if p.get("pesquisa") == pq["id"]))
        blocos.append("</section>")
    gerais = [p for p in POSTS if p.get("pesquisa") not in {q["id"] for q in PESQ}]
    if gerais:
        blocos.append('<h2>Sobre o projeto</h2>' + "".join(cartao_post(p) for p in gerais))
    corpo = f"""
<h1>Compartilhar</h1>
<p class="lead">Textos curtos, com fatos verificados e a fonte oficial, prontos para redes sociais e grupos de mensagem. Cada texto é de um tema.</p>
{nota_temas()}
<p class="nota">Versão preliminar. Confira a fonte antes de publicar e, se possível, inclua o link deste site.</p>
{''.join(blocos)}
<p class="status" id="status" role="status"></p>
"""
    return pagina("compartilhar.html", "Compartilhar — Projeto Democracia Brasil", "Textos prontos com fatos verificados de cada tema publicado, sempre com a fonte oficial.", corpo, js=True)

# ---------------------------------------------------------------- como usar
def gerar_como_usar():
    secoes = [(h, n) for h, n in MENU]
    desc = {"index.html": f"Os {NT} temas do projeto, com a situação de cada um, o resultado completo da pesquisa mais recente e as novidades.",
            "acervo.html": "Todas as leis, decretos, tratados e decisões do STF dos temas já publicados, com busca, filtros (inclusive por tema) e a ficha de cada item. Escolha itens (ou “Selecionar todos”) e toque em “Resumo visual” para ver o painel da sua seleção, baixar em PDF ou enviar no WhatsApp com o link para editar.",
            "votacoes.html": "Como o Congresso votou, tema por tema: votações nominais, placar e votos por partido.",
            "entenda.html": "O caminho de uma lei, um glossário e o método do projeto, em linguagem simples.",
            "compartilhar.html": "Textos curtos com a fonte oficial, separados por tema, prontos para redes sociais e grupos de mensagem.",
            "baixar.html": "Por tema: o resumo em PDF, a planilha completa e as listas em CSV. Para todo o projeto: o guia metodológico e os vídeos."}
    onde = "".join(f'<dt><a href="{h}">{n}</a></dt><dd>{desc[h]}</dd>' for h, n in secoes)
    repo = "https://github.com/adrianacorradi/projeto-democracia-brasil"
    corpo = f"""
<h1>Como usar o site</h1>
<p class="lead">Orientações de acesso, vídeos curtos e onde encontrar cada coisa.</p>

<h2 id="acesso">Acesso</h2>
<ul class="acesso">
<li><strong>Endereço:</strong> <a href="{URL}/">{e(URL.replace('https://', ''))}</a></li>
<li><strong>Aberto e gratuito.</strong> Não precisa de cadastro nem de senha.</li>
<li><strong>No celular ou no computador.</strong> Funciona em qualquer navegador atualizado, mesmo com internet lenta. Os vídeos só baixam quando você toca neles.</li>
<li><strong>Sem rastreamento.</strong> O site não usa cookies nem contador de visitas. A sua seleção de itens fica guardada só no seu navegador. A hospedagem é do GitHub Pages.</li>
<li><strong>Acessibilidade.</strong> O site foi feito para funcionar com teclado, com leitores de tela e no modo escuro do aparelho. Os vídeos não têm som e trazem legendas e o roteiro em texto.</li>
<li><strong>Versão preliminar.</strong> Os dados ainda passam por checagem final. Cada informação tem link para a fonte oficial: confira antes de divulgar.</li>
</ul>

<h2 id="videos">Vídeos</h2>
<h3>Para quem consulta o site</h3>
{bloco_videos("consulta")}
<h3>Para a equipe do projeto</h3>
{bloco_videos("equipe")}

<h2 id="onde">Onde está cada coisa</h2>
<dl class="glossario">{onde}</dl>

<h2 id="erro">Encontrou um erro?</h2>
<p>Avise com o link da fonte correta. Quem tem conta no GitHub pode abrir um aviso (issue) no <a href="{repo}/issues">repositório do projeto</a>. As correções são registradas em Novidades.</p>
"""
    return pagina("como-usar.html", "Como usar — Projeto Democracia Brasil", "Orientações de acesso, vídeos curtos e onde encontrar cada informação no site.", corpo, js=bool(VID))

# ---------------------------------------------------------------- baixar
def tamanho(rel):
    p = os.path.join(RAIZ, rel)
    if not os.path.exists(p):
        return ""
    b = os.path.getsize(p)
    return f"{b/1024/1024:.1f} MB" if b > 1024 * 1024 else f"{max(b//1024,1)} KB"

def gerar_baixar():
    def lista(arqs):
        return "<ul>" + "".join(f'<li><a href="{a}" download>{e(t)}</a> <span class="pequeno">({tamanho(a)})</span><br>{e(d)}</li>' for a, t, d in arqs) + "</ul>"
    blocos = []
    for p in PESQ:
        arqs = [(p["pdf"], "Resumo em PDF", "Os principais achados, o mosaico das leis e as fontes, em poucas páginas.")] + [tuple(x) for x in p.get("arquivos", [])]
        blocos.append(f"""<section class="tema-bloco" id="baixar-{p['id']}" aria-labelledby="bt-{p['id']}">
<p class="rotulo">{rotulo_tema(p)} · {e(p['situacao'])}</p>
<h2 id="bt-{p['id']}">{e(p['tema'])}</h2>
{lista(arqs)}
</section>""")
    gerais = [("downloads/guia_metodologico.md", "Guia metodológico", f"As regras do projeto, iguais para os {NT} temas: fontes, atribuição a governos, votações e linguagem.")]
    for v in VID.values():
        gerais.append((f"assets/video-{v['id']}.mp4", f"Vídeo: {v['titulo'].lower()} (MP4)", f"{duracao(v['duracao_s'])}, sem som, com legendas. Pode ser enviado por aplicativos de mensagem."))
    exemplos = "".join(f"<li>Projeto Democracia Brasil. {e(p['titulo'])} ({rotulo_tema(p).lower()}; {e(p['situacao'].lower())}). Atualizado em {e(carregar(p)['meta']['atualizado'])}. Disponível em: {e(url_pesquisa(p))}.</li>" for p in PESQ)
    corpo = f"""
<h1>Baixar</h1>
<p class="lead">Todo o acervo está disponível para pesquisa, aula e reutilização. Os arquivos estão separados por tema.</p>
{nota_temas()}
{''.join(blocos)}
<h2 id="baixar-projeto">Para todo o projeto</h2>
{lista(gerais)}
<p>Prefere montar o seu próprio resumo? No <a href="acervo.html">acervo</a>, toque em "Adicionar à seleção" nos itens que interessam (ou em "Selecionar todos") e depois em "Resumo visual".</p>
<h2>Como citar</h2>
<p>Cite o projeto, o tema e a data de atualização. Cite também a fonte oficial de cada dado.</p>
<ul>{exemplos}</ul>
"""
    return pagina("baixar.html", "Baixar — Projeto Democracia Brasil", "Downloads de cada tema publicado (resumo em PDF, planilha e listas em CSV) e o guia metodológico do projeto.", corpo)

# ---------------------------------------------------------------- resumo (vira PDF)
def gerar_resumo(p):
    d = carregar(p)
    ATOS, LAC, META = d["atos"], d["lacunas"], d["meta"]
    marcos = [a for a in ATOS if a["ato"] in p.get("marcos", [])]
    lin = "".join(f'<tr><td>{br(a["data"])}</td><td><strong>{e(a["ato"])}</strong><br>{e(a["resumo"])}</td><td>{e(a["governo"])}</td></tr>' for a in marcos)
    stf = [a for a in ATOS if a["tipo"] == "STF"]
    lstf = "".join(f'<li><strong>{e(a["ato"])}</strong> ({br(a["data"])}): {e(a["resumo"])}</li>' for a in stf)
    cam, sen = LAC["camara"], LAC["senado"]
    corpo = f"""
<h1>{e(p['titulo'])}</h1>
<p class="lead">{rotulo_tema(p)} do Projeto Democracia Brasil. {e(p['situacao'])}, atualizada em {e(META['atualizado'])}.</p>
<p>O projeto levanta, com o mesmo método, as políticas públicas federais de {NT} temas desde 1985. Este resumo trata só de um deles: {e(p['tema'].lower())}.</p>
<h2>O que levantamos</h2>
<ul>
<li>{META['total_atos']} atos federais: leis, decretos, tratados internacionais e decisões do STF.</li>
<li>A tramitação de {LAC['total']} leis, leis complementares e emendas na Câmara e no Senado.</li>
<li>{milhar(META['total_votacoes'])} votações e {milhar(META['total_votos'])} votos individuais de parlamentares.</li>
</ul>
<h2>Principal achado</h2>
<h3>Como as {LAC['total']} leis passaram pelo Congresso</h3>
{bloco_mosaico(p, d, toque=False)}
<p>O voto nominal foi registrado em pelo menos uma das Casas. Por Casa:</p>
<ul>
<li>Câmara: {cam.get('Plenário, votação simbólica',0)} aprovadas por votação simbólica, {cam.get('Só nas comissões',0)} só nas comissões, {cam.get('Plenário, votação nominal',0)} com votação nominal.</li>
<li>Senado: {sen.get('Plenário, votação simbólica',0)} aprovadas por votação simbólica, {sen.get('Só nas comissões',0)} só nas comissões, {sen.get('Plenário, votação nominal',0)} com votação nominal.</li>
</ul>
<p>Sem registro nominal, não é possível dizer como cada parlamentar votou. Isso não indica apoio nem oposição.</p>
<h2>Alguns marcos</h2>
<table><thead><tr><th>Data</th><th>Ato</th><th>Governo na data</th></tr></thead><tbody>{lin}</tbody></table>
<h2>Decisões do STF</h2>
<ul>{lstf}</ul>
<h2>Limites desta versão</h2>
<ul>
<li>Os números valem só para este tema. Os outros temas do projeto são publicados à parte.</li>
<li>A lista foi montada a partir das ementas publicadas no Planalto; leis cuja ementa não cita o tema podem faltar.</li>
<li>A Câmara não tem votos individuais nas bases abertas antes de 2005.</li>
<li>Contar leis por governo não mede importância nem efeito; por isso não há ranking.</li>
</ul>
<h2>Fontes</h2>
<ul>
<li>Legislação: <a href="https://www4.planalto.gov.br/legislacao">www4.planalto.gov.br/legislacao</a></li>
<li>Câmara dos Deputados, dados abertos: <a href="https://dadosabertos.camara.leg.br">dadosabertos.camara.leg.br</a></li>
<li>Senado Federal, dados abertos: <a href="https://legis.senado.leg.br/dadosabertos">legis.senado.leg.br/dadosabertos</a></li>
<li>Decisões do STF: fontes indicadas em cada item do acervo.</li>
</ul>
{f'<p>Resultado completo, com a fonte de cada item: <a href="{url_pesquisa(p)}">{url_pesquisa(p)}</a></p>' if URL else ''}
"""
    return pagina(p["paginas"]["resumo"], f"Resumo: {p['titulo']} — Projeto Democracia Brasil", f"Resumo dos principais achados: {p['titulo']}.", corpo)

if __name__ == "__main__":
    for nome, f in (("index.html", gerar_index), ("acervo.html", gerar_acervo), ("votacoes.html", gerar_votacoes), ("entenda.html", gerar_entenda),
                    ("compartilhar.html", gerar_compartilhar), ("baixar.html", gerar_baixar),
                    ("como-usar.html", gerar_como_usar)) + tuple((p["paginas"]["resumo"], functools.partial(gerar_resumo, p)) for p in PESQ) \
                 + tuple((f"pesquisa-{p['id']}.html", functools.partial(gerar_pesquisa, p)) for p in PESQ):
        open(os.path.join(RAIZ, nome), "w", encoding="utf-8").write(f())
        print(f"{nome}: {os.path.getsize(os.path.join(RAIZ, nome))//1024} KB")
