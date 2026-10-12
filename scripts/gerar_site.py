# -*- coding: utf-8 -*-
"""Gera o site estático do Projeto Democracia Brasil a partir da pasta dados/.

Uso:  python3 scripts/gerar_site.py      (rodar na raiz do site)
Entradas: dados/atos.json, mosaico.json, lacunas.json, votacoes_indice.json, meta.json, posts.json, novidades.json, temas.json
Saídas:   index.html, acervo.html, votacoes.html, entenda.html, compartilhar.html, baixar.html, resumo.html, como-usar.html
"""
import json, os, html, unicodedata
from datetime import date

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def dados(n):
    return json.load(open(os.path.join(RAIZ, "dados", n + ".json"), encoding="utf-8"))

ATOS, MOS, LAC, VOT, META = dados("atos"), dados("mosaico"), dados("lacunas"), dados("votacoes_indice"), dados("meta")
POSTS, NOV, TEMAS = dados("posts"), dados("novidades"), dados("temas")
CFG = dados("config")
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
<meta name="theme-color" content="#0b6b57">
<link rel="icon" href="assets/icone.svg" type="image/svg+xml">
<link rel="stylesheet" href="assets/estilo.css">
</head>
<body>
<a class="pular" href="#conteudo">Pular para o conteúdo</a>
<header class="topo"><div class="coluna">
<a class="marca-site" href="index.html">Projeto Democracia Brasil</a>
{ajuda}
<nav class="menu" aria-label="Seções">{menu}</nav>
</div></header>
<div class="aviso"><div class="coluna">Versão preliminar. Os dados do piloto ainda passam por checagem final. Atualizado em {META['atualizado']}.</div></div>
<main id="conteudo"><div class="coluna">
{corpo}
</div></main>
<footer class="rodape"><div class="coluna">
<p>Dados de fontes oficiais: Planalto, Câmara dos Deputados, Senado Federal e Supremo Tribunal Federal. Cada item traz o link para a sua fonte.</p>
<p>Ao reutilizar, cite o Projeto Democracia Brasil e a fonte original. Encontrou um erro? <a href="como-usar.html#erro">Veja como avisar</a>.</p>
<p><a href="como-usar.html">Como usar o site: orientações de acesso e vídeos</a></p>
</div></footer>
{'<script src="assets/app.js" defer></script>' if js else ''}
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

def gerar_index():
    n = {k: sum(1 for m in MOS if m["situacao"] == k) for k in SIT}
    celulas = "".join(f'<a class="{SIT[m["situacao"]][1]}" href="acervo.html#{e(m["id"])}" title="{e(m["ato"])}: {e(SIT[m["situacao"]][0].lower())}" aria-label="{e(m["ato"])}, {e(SIT[m["situacao"]][0].lower())}"></a>' for m in MOS)
    anos = [m["ano"] for m in MOS]
    piloto = ' — <a href="acervo.html">piloto em andamento</a>'
    temas = "".join(f'<li>{e(t)}{piloto if s == "piloto" else " — em preparação"}</li>' for t, s in TEMAS)
    novs = "".join(f"<li><strong>{br(x['data'])}</strong>: {e(x['texto'])}</li>" for x in NOV)
    corpo = f"""
<h1>O que mudou nos direitos da população brasileira desde 1985</h1>
<p class="lead">Lei por lei, com a fonte oficial de cada informação. Começamos pelos direitos das mulheres.</p>
{bloco_videos()}

<h2>Como 171 leis sobre direitos das mulheres passaram pelo Congresso</h2>
<p>Cada quadrado é uma lei, lei complementar ou emenda constitucional aprovada desde 1985, em ordem de data. Toque em um quadrado para ver a lei.</p>
<div class="mosaico" role="list" aria-label="Leis em ordem de data">{celulas}</div>
<div class="eixo" aria-hidden="true"><span>{min(anos)}</span><span>{max(anos)}</span></div>
{legenda()}
<p class="destaque-num">Só {LAC['com_nominal']} das {LAC['total']} tiveram o voto de cada parlamentar registrado no texto principal.</p>
<p>As outras foram aprovadas por votação simbólica ({n['simbolica']}), decididas nas comissões ({n['comissoes']}) ou não têm registro nas bases abertas ({n['sem-registro']}). Nesses casos, não é possível saber como cada deputado ou senador votou.</p>
<p><a href="votacoes.html">Veja as votações com voto registrado</a> ou <a href="entenda.html#votacao">entenda a diferença entre votação nominal e simbólica</a>.</p>

<h2>Comece por aqui</h2>
<ul>
<li><a href="acervo.html">Pesquise no acervo</a>: {META['total_atos']} leis, decretos, tratados e decisões do STF.</li>
<li><a href="entenda.html">Entenda como uma lei é feita</a>, em linguagem simples.</li>
<li><a href="downloads/resumo_piloto_direitos_mulheres.pdf">Baixe o resumo em PDF</a> do piloto.</li>
<li><a href="compartilhar.html">Textos prontos para compartilhar</a>, com as fontes.</li>
</ul>

<h2>Temas do projeto</h2>
<ul>{temas}</ul>

<h2 id="novidades">Novidades</h2>
<ul>{novs}</ul>
"""
    return pagina("index.html", "Projeto Democracia Brasil", "Levantamento verificável das políticas públicas no Brasil desde 1985, com fontes oficiais.", corpo, js=bool(VID))

# ---------------------------------------------------------------- acervo
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
    return f"""<li id="{e(x['id'])}" data-tipo="{e(x['tipo'])}" data-gov="{e(x['governo'].replace(' (referência)', ''))}" data-esc="{e(x['escopo'])}" data-sit="{e(sit or 'nao-se-aplica')}" data-sub="{e(x['subtema'])}" data-mp="{'sim' if x.get('so_historico') else 'nao'}" data-txt="{e(busca)}">
<article>
<h3>{e(x['ato'])}</h3>
<p class="quando">{extenso(x['data'])}. Governo {e(x['governo'])}.</p>
<p>{e(x['resumo'])}</p>
<div class="etiquetas">{carimbo(sit)}<span class="etq">{e(x['subtema'])}</span>{mp}</div>
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
    lista = sorted(ATOS, key=lambda x: x["data"])
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
<p class="lead">Leis, decretos, tratados e decisões do STF sobre direitos das mulheres, de 1985 a 2026. Toque em "Detalhes e fontes" para ver como cada lei foi aprovada e abrir o texto oficial.</p>
<noscript><p class="nota">A busca precisa de JavaScript. Todos os itens estão abaixo, em ordem de data. Você também pode <a href="baixar.html">baixar a lista completa</a>.</p></noscript>
<form class="busca so-tela" role="search" onsubmit="return false">
<label for="q">Buscar por palavra, número da lei ou ano</label>
<div class="linha-busca"><input id="q" type="search" placeholder="Ex.: trabalho doméstico, 9.504, 1997" autocomplete="off"><button type="button" id="nova-busca">Nova busca</button></div>
<details class="filtros"><summary>Filtrar</summary><div class="grade">
<label>Tipo de ato<select data-filtro="data-tipo"><option value="">Todos</option>{opcoes(tipos)}</select></label>
<label>Governo na data<select data-filtro="data-gov"><option value="">Todos</option>{opcoes(govs)}</select></label>
<label>Assunto<select data-filtro="data-sub"><option value="">Todos</option>{opcoes(subs)}</select></label>
<label>Como foi aprovada<select data-filtro="data-sit"><option value="">Todas</option>{sits}</select></label>
<label>Escopo<select data-filtro="data-esc"><option value="">Todos</option>{opcoes(escs)}</select></label>
<label style="display:flex;align-items:center;gap:.5rem"><input type="checkbox" data-filtro="data-mp" checked> Mostrar alterações da Lei Maria da Penha</label>
</div></details>
<p class="contagem" id="contagem" aria-live="polite"></p>
</form>
<div class="so-impressao"><h2>Minha seleção</h2><p>Projeto Democracia Brasil. Gerado em <span id="data-impressao"></span>. Versão preliminar.</p></div>
<ol class="acervo" id="lista">
{itens}
</ol>
<p class="status so-tela" id="status" role="status"></p>
<p class="pequeno so-tela">Monte o seu resumo: toque em "Adicionar à seleção" nos itens que interessam e depois em "PDF". Na janela que abrir, escolha "Salvar como PDF". A seleção fica guardada só neste navegador.</p>
<div class="barra-selecao so-tela" id="barra-selecao" hidden><div class="coluna">
<strong>Seleção: <span id="n-selecao">0</span></strong>
<button type="button" id="ver-selecao">Ver</button>
<button type="button" class="cheio" id="pdf-selecao">PDF</button>
<button type="button" id="limpar-selecao">Limpar</button>
</div></div>
"""
    return pagina("acervo.html", "Acervo — Projeto Democracia Brasil", "Busque leis, decretos e decisões sobre direitos das mulheres desde 1985, com links para as fontes oficiais.", corpo, js=True)

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
    cards = []
    for v in VOT:
        pres = v["sim"] + v["nao"] + v["abst"] + v["obst"]
        linhas = "".join(f'<tr><td>{e(p["partido"])}</td><td class="n">{p["sim"]}</td><td class="n">{p["nao"]}</td><td class="n">{p["abst"]}</td><td class="n">{p["obst"]}</td></tr>' for p in v["partidos"])
        rev = '<p class="nota">Esta lei alterou a regra de afastamento da gestante criada pela Lei 14.151/2021. Votar "sim" aqui significa aprovar essa alteração. A leitura do voto deve considerar esse contexto.</p>' if v.get("revisar") else ""
        cards.append(f"""<div class="cartao">
<h3>{e(v['ato'])}</h3>
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
    corpo = f"""
<h1>Como o Congresso votou</h1>
<p class="lead">Uma lei pode ser aprovada com o voto de cada parlamentar registrado (votação nominal) ou sem esse registro (votação simbólica ou decisão nas comissões). Só no primeiro caso é possível saber quem votou a favor ou contra.</p>
{legenda()}
{linha_casa("Câmara dos Deputados", LAC["camara"])}
{linha_casa("Senado Federal", LAC["senado"])}
<p class="pequeno">Base: {LAC['total']} leis, leis complementares e emendas constitucionais sobre direitos das mulheres aprovadas desde 1985. Fonte: dados abertos da Câmara e do Senado, consultados em {e(META['atualizado'])}. A Câmara não tem votos individuais nas bases abertas antes de 2005.</p>

<h2>As votações com voto registrado</h2>
<p>São as votações nominais do texto principal das leis do núcleo do tema. Votar "sim" significa aprovar o texto que virou lei. Isso mede apoio ao texto aprovado, não a posição de cada parlamentar sobre direitos das mulheres em geral.</p>
{''.join(cards)}
<p>Quer ver o voto de cada deputado e senador? <a href="baixar.html">Baixe a lista de votos nominais</a>.</p>
"""
    return pagina("votacoes.html", "Como o Congresso votou — Projeto Democracia Brasil", "Quantas leis sobre direitos das mulheres tiveram voto nominal e como cada partido votou.", corpo)

# ---------------------------------------------------------------- entenda
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
<p>Na votação nominal, fica registrado como cada parlamentar votou. Na simbólica, só o resultado. A maioria das leis sobre direitos das mulheres foi aprovada sem registro nominal. Por isso, para essas leis, não dá para dizer quem votou a favor ou contra. A falta de registro não significa apoio nem oposição.</p>

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
def gerar_compartilhar():
    blocos = []
    for p in POSTS:
        fontes = "\n".join(f"Fonte: {u}" for _, u in p["fontes"][:1])
        texto = p["texto"] + "\n\n" + fontes
        links = "".join(f'<a href="{e(u)}" rel="noopener">{e(n)}</a>' for n, u in p["fontes"])
        blocos.append(f"""<div class="cartao" id="{e(p['id'])}">
<h3>{e(p['titulo'])}</h3>
<p class="post" id="t-{e(p['id'])}">{e(texto)}</p>
<p class="pequeno">{len(texto)} caracteres</p>
<p class="fontes">{links}</p>
<div class="acoes"><button type="button" data-copiar="t-{e(p['id'])}">Copiar texto</button><button type="button" class="cheio" data-copiar="t-{e(p['id'])}" data-share>Compartilhar</button></div>
</div>""")
    corpo = f"""
<h1>Compartilhar</h1>
<p class="lead">Textos curtos, com fatos verificados e a fonte oficial, prontos para redes sociais e grupos de mensagem.</p>
<p class="nota">Versão preliminar. Confira a fonte antes de publicar e, se possível, inclua o link deste site.</p>
{''.join(blocos)}
<p class="status" id="status" role="status"></p>
"""
    return pagina("compartilhar.html", "Compartilhar — Projeto Democracia Brasil", "Textos prontos com fatos verificados sobre direitos das mulheres no Brasil.", corpo, js=True)

# ---------------------------------------------------------------- como usar
def gerar_como_usar():
    secoes = [(h, n) for h, n in MENU]
    desc = {"index.html": "O resumo do piloto, o mosaico das leis e as novidades.",
            "acervo.html": "Todas as leis, decretos, tratados e decisões do STF, com busca, filtros e a ficha de cada item.",
            "votacoes.html": "Como o Congresso votou: votações nominais, placar e votos por partido.",
            "entenda.html": "O caminho de uma lei, um glossário e o método do projeto, em linguagem simples.",
            "compartilhar.html": "Textos curtos com a fonte oficial, prontos para redes sociais e grupos de mensagem.",
            "baixar.html": "O resumo em PDF, a planilha completa, as listas em CSV, o guia metodológico e os vídeos."}
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
    arquivos = [
        ("downloads/resumo_piloto_direitos_mulheres.pdf", "Resumo do piloto (PDF)", "Os principais achados sobre direitos das mulheres, em poucas páginas, com as fontes."),
        ("downloads/planilha_piloto_direitos_mulheres.xlsx", "Planilha completa (Excel)", "Todas as fichas, a tramitação, as votações, os votos e as notas de método."),
        ("downloads/atos_direitos_mulheres.csv", "Lista de atos (CSV)", "Um ato por linha, com resumo, origem, como foi aprovado e link para a fonte. Abre no Excel e no Google Planilhas."),
        ("downloads/votacoes_plenario.csv", "Votações (CSV)", "Todas as votações em Plenário das leis do piloto, com placar."),
        ("downloads/votos_nominais.zip", "Votos de cada parlamentar (CSV compactado)", "O voto de cada deputado e senador nas votações nominais, com partido e UF na data."),
        ("downloads/guia_metodologico.md", "Guia metodológico", "As regras do projeto: fontes, atribuição a governos, votações e linguagem."),
    ]
    for v in VID.values():
        arquivos.append((f"assets/video-{v['id']}.mp4", f"Vídeo: {v['titulo'].lower()} (MP4)", f"{duracao(v['duracao_s'])}, sem som, com legendas. Pode ser enviado por aplicativos de mensagem."))
    itens = "".join(f'<li><a href="{a}" download>{e(t)}</a> <span class="pequeno">({tamanho(a)})</span><br>{e(d)}</li>' for a, t, d in arquivos)
    corpo = f"""
<h1>Baixar</h1>
<p class="lead">Todo o acervo está disponível para pesquisa, aula e reutilização.</p>
<ul>{itens}</ul>
<p>Prefere montar o seu próprio resumo? No <a href="acervo.html">acervo</a>, toque em "Adicionar à seleção" nos itens que interessam e depois em "PDF".</p>
<h2>Como citar</h2>
<p>Projeto Democracia Brasil. Piloto: direitos das mulheres (1985–2026). Versão preliminar, atualizada em {e(META['atualizado'])}. Cite também a fonte oficial de cada dado.</p>
"""
    return pagina("baixar.html", "Baixar — Projeto Democracia Brasil", "Downloads do acervo: resumo em PDF, planilha, listas em CSV e guia metodológico.", corpo)

# ---------------------------------------------------------------- resumo (vira PDF)
def gerar_resumo():
    marcos = [a for a in ATOS if a["ato"] in (
        "Lei 7.353/1985", "Constituição Federal de 1988", "Lei 9.029/1995", "Decreto 1.973/1996", "Lei 9.504/1997", "Decreto 4.377/2002",
        "Lei 11.340/2006", "Lei 13.104/2015", "Lei 13.718/2018", "Lei 14.192/2021", "Emenda Constitucional 117/2022", "Lei 14.611/2023", "Lei 14.994/2024")]
    lin = "".join(f'<tr><td>{br(a["data"])}</td><td><strong>{e(a["ato"])}</strong><br>{e(a["resumo"])}</td><td>{e(a["governo"])}</td></tr>' for a in marcos)
    stf = [a for a in ATOS if a["tipo"] == "STF"]
    lstf = "".join(f'<li><strong>{e(a["ato"])}</strong> ({br(a["data"])}): {e(a["resumo"])}</li>' for a in stf)
    cam, sen = LAC["camara"], LAC["senado"]
    corpo = f"""
<h1>Direitos das mulheres no Brasil, 1985–2026</h1>
<p class="lead">Resumo do piloto do Projeto Democracia Brasil. Versão preliminar, atualizada em {e(META['atualizado'])}.</p>
<h2>O que levantamos</h2>
<ul>
<li>{META['total_atos']} atos federais: leis, decretos, tratados internacionais e decisões do STF.</li>
<li>A tramitação de {LAC['total']} leis, leis complementares e emendas na Câmara e no Senado.</li>
<li>{milhar(META['total_votacoes'])} votações e {milhar(META['total_votos'])} votos individuais de parlamentares.</li>
</ul>
<h2>Principal achado</h2>
<p>Só <strong>{LAC['com_nominal']} das {LAC['total']}</strong> leis tiveram o voto de cada parlamentar registrado no texto principal, em pelo menos uma das Casas.</p>
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
{f'<p>Acervo completo, com a fonte de cada item: <a href="{URL}">{URL}</a></p>' if URL else ''}
"""
    return pagina("resumo.html", "Resumo do piloto — Projeto Democracia Brasil", "Resumo dos principais achados sobre direitos das mulheres, 1985–2026.", corpo)

if __name__ == "__main__":
    for nome, f in (("index.html", gerar_index), ("acervo.html", gerar_acervo), ("votacoes.html", gerar_votacoes), ("entenda.html", gerar_entenda),
                    ("compartilhar.html", gerar_compartilhar), ("baixar.html", gerar_baixar), ("resumo.html", gerar_resumo),
                    ("como-usar.html", gerar_como_usar)):
        open(os.path.join(RAIZ, nome), "w", encoding="utf-8").write(f())
        print(f"{nome}: {os.path.getsize(os.path.join(RAIZ, nome))//1024} KB")
