/* Projeto Democracia Brasil — busca, seleção, painel da seleção e compartilhamento. Sem dependências. */
(function () {
  "use strict";
  var CHAVE = "pdb-selecao";
  function norm(s) { return (s || "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase(); }
  function ler() { try { return JSON.parse(localStorage.getItem(CHAVE) || "[]"); } catch (e) { return memoria; } }
  function gravar(v) { memoria = v; try { localStorage.setItem(CHAVE, JSON.stringify(v)); } catch (e) {} }
  var memoria = [];
  function esc(s) { return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]; }); }
  function status(msg, perto) {
    var caixa = perto && perto.closest ? perto.closest(".ccard, .cartao, section, .barra-selecao, form") : null;
    var el = (caixa && caixa.querySelector(".status")) || document.getElementById("status");
    if (el) { el.textContent = msg; setTimeout(function () { if (el.textContent === msg) el.textContent = ""; }, 5000); }
  }
  function copiar(txt, perto, ok) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(txt).then(function () { status(ok || "Texto copiado. Agora é só colar onde quiser.", perto); },
        function () { status("Não foi possível copiar. Selecione o texto e copie.", perto); });
    } else { status("Selecione o texto e copie.", perto); }
  }

  /* seleção no endereço: ids MUL-2018-010 viram p=MUL&s=2018010.2006001 */
  function codificar(ids) {
    if (!ids.length) return "";
    var p = ids[0].split("-")[0];
    var curto = ids.every(function (i) { return /^[A-Z]+-\d{4}-\d{3}$/.test(i) && i.split("-")[0] === p; });
    if (!curto) return "s=" + ids.map(encodeURIComponent).join(".");
    return "p=" + p + "&s=" + ids.map(function (i) { return i.slice(p.length + 1).replace("-", ""); }).join(".");
  }
  function decodificar(prm) {
    var s = prm.get("s"); if (!s) return null;
    var p = prm.get("p") || "";
    if (s === "todos") return { p: p, todos: true, ids: [] };
    return { p: p, ids: s.split(".").filter(Boolean).map(function (x) {
      return (p && /^\d{7}$/.test(x)) ? p + "-" + x.slice(0, 4) + "-" + x.slice(4) : decodeURIComponent(x);
    }) };
  }
  function urlAbsoluta(rel) { try { return new URL(rel, location.href).href; } catch (e) { return rel; } }

  /* compartilhar ou copiar */
  document.addEventListener("click", function (ev) {
    var b = ev.target.closest("[data-compartilhar]");
    if (b) {
      var alvo = document.getElementById(b.getAttribute("data-compartilhar"));
      var url = location.href.split("#")[0] + "#" + b.getAttribute("data-compartilhar");
      var texto = "";
      if (alvo) {
        var h = alvo.querySelector("h3"), r = alvo.querySelector("article > p:not(.quando)"), f = alvo.querySelector(".fontes a");
        texto = (h ? h.textContent + ": " : "") + (r ? r.textContent : "") + (f ? " Fonte: " + f.href : "");
      }
      if (navigator.share) { navigator.share({ title: document.title, text: texto, url: url }).catch(function () {}); }
      else copiar(texto + "\n" + url, b);
    }
    var c = ev.target.closest("[data-copiar]");
    if (c) {
      var el = document.getElementById(c.getAttribute("data-copiar"));
      var fechado = el && el.closest("details:not([open])");
      var txt = el ? ((fechado || el.hidden) ? el.textContent : el.innerText) : "";
      if (c.hasAttribute("data-share") && navigator.share) { navigator.share({ text: txt }).catch(function () {}); return; }
      if (fechado && !el.hidden) fechado.open = true;
      copiar(txt, c);
    }
    var l = ev.target.closest("[data-copiar-link]");
    if (l) copiar(l.getAttribute("data-copiar-link"), l, "Link copiado. Quem abrir vê o mesmo painel e pode mudar a seleção.");
    /* PDF visual: imprime só o painel pedido, com as cores da tela */
    var im = ev.target.closest("[data-imprimir]");
    if (im) {
      var sec = document.getElementById(im.getAttribute("data-imprimir"));
      var col = document.querySelector("main .coluna");
      if (!sec || !col) return;
      var filho = sec; while (filho.parentElement && filho.parentElement !== col) filho = filho.parentElement;
      filho.classList.add("alvo-impressao");
      document.body.classList.add("imprimir-painel");
      var dt = sec.querySelector(".data-impressao"); if (dt) dt.textContent = new Date().toLocaleDateString("pt-BR");
      window.print();
    }
  });
  window.addEventListener("afterprint", function () {
    document.body.classList.remove("imprimir-painel", "imprimir-selecao");
    Array.prototype.forEach.call(document.querySelectorAll(".alvo-impressao"), function (x) { x.classList.remove("alvo-impressao"); });
  });

  /* vídeos: tocam ao abrir, pausam ao fechar */
  document.addEventListener("toggle", function (ev) {
    var d = ev.target;
    if (!d.classList || !d.classList.contains("video-tutorial")) return;
    var v = d.querySelector("video");
    if (!v) return;
    if (d.open) {
      Array.prototype.forEach.call(document.querySelectorAll("details.video-tutorial[open]"), function (o) { if (o !== d) o.open = false; });
      if (!v.getAttribute("poster") && v.dataset.poster) v.setAttribute("poster", v.dataset.poster); var p = v.play(); if (p && p.catch) p.catch(function () {}); } else { v.pause(); }
  }, true);

  /* ------------------------------------------------------------ painel da seleção (página inicial) */
  var SIT = { nominal: ["Voto nominal registrado", "s-nominal"], simbolica: ["Votação simbólica", "s-simbolica"],
              comissoes: ["Decidida nas comissões", "s-comissoes"], "sem-registro": ["Sem registro nas bases abertas", "s-sem-registro"] };
  function br(d) { var x = d.slice(0, 10).split("-"); return x[2] + "/" + x[1] + "/" + x[0]; }
  function milhar(n) { return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, "."); }
  function selo(a) {
    if (a.situacao) return '<span class="selo ' + a.situacao + '">' + esc(SIT[a.situacao][0]) + "</span>";
    var r = a.tipo === "STF" ? ["Decisão do STF", "stf"] : a.escopo === "Tratado internacional" ? ["Tratado internacional", "outro"] :
            a.tipo === "Constituição" ? ["Constituinte", "outro"] : [a.tipo, "outro"];
    return '<span class="selo ' + r[1] + '">' + esc(r[0]) + "</span>";
  }
  function legenda() {
    return '<ul class="legenda">' + Object.keys(SIT).map(function (k) { return '<li><i class="' + SIT[k][1] + '" aria-hidden="true"></i>' + SIT[k][0] + "</li>"; }).join("") + "</ul>";
  }
  function barra(v) {
    var tot = v.sim + v.nao + v.abst + v.obst || 1;
    return '<div class="barra" aria-hidden="true">' + [["sim", "b-sim"], ["nao", "b-nao"], ["abst", "b-abst"], ["obst", "b-obst"]].map(function (k) {
      return v[k[0]] ? '<span class="' + k[1] + '" style="width:' + (v[k[0]] * 100 / tot).toFixed(2) + '%"></span>' : ""; }).join("") + "</div>";
  }
  function textoDidatico(pq, sel, leis, nom, subs, link, cont) {
    /* linguagem simples; até 500 caracteres sem contar o link */
    var n = sel.length, outros = n - leis.length;
    var partes = [[cont.simbolica, "votação simbólica"], [cont.comissoes, "decisão nas comissões"], [cont["sem-registro"], "sem registro nas bases abertas"]]
      .filter(function (x) { return x[0] > 0; }).map(function (x) { return x[1] + " (" + x[0] + ")"; });
    var como = partes.length > 1 ? partes.slice(0, -1).join(", ") + " ou " + partes[partes.length - 1] : partes.join("");
    var t = "Escolhi " + n + (n === 1 ? " norma" : " normas") + " sobre " + pq.assunto + " no Projeto Democracia Brasil (" + pq.situacao.toLowerCase() + "):\n\n";
    if (leis.length) {
      t += "• " + leis.length + (leis.length === 1 ? " é lei aprovada" : " são leis aprovadas") + " no Congresso. ";
      if (nom === 0) t += (leis.length === 1 ? "Nela não" : "Em nenhuma delas") + " ficou registrado o voto de cada parlamentar: " + como + ".\n";
      else if (nom === leis.length) t += (leis.length === 1 ? "Nela" : "Em todas") + " ficou registrado o voto de cada parlamentar (votação nominal).\n";
      else t += "Em " + nom + " ficou registrado o voto de cada parlamentar (votação nominal); nas outras, não: " + como + ".\n";
    }
    if (outros > 0) t += "• " + outros + (outros === 1 ? " é outro ato" : " são outros atos") + " (decreto, tratado, decisão do STF ou Constituição).\n";
    t += "• Assuntos: " + subs.slice(0, 3).map(function (s) { return s[0] + " (" + s[1].length + ")"; }).join(", ") + (subs.length > 3 ? " e outros" : "") + ".\n\n";
    t += "Fonte: " + (pq.fonte_congresso || "https://dadosabertos.camara.leg.br") + "\nVeja o painel e monte a sua versão:\n" + link;
    return t;
  }
  function montarPainel(caixa, pq, atos, vot, pedido) {
    var porId = {}; atos.forEach(function (a) { porId[a.id] = a; });
    var ids = pedido.todos ? atos.map(function (a) { return a.id; }) : pedido.ids.filter(function (i) { return porId[i]; });
    var faltam = pedido.todos ? 0 : pedido.ids.length - ids.length;
    var sel = ids.map(function (i) { return porId[i]; }).sort(function (a, b) { return a.data < b.data ? -1 : 1; });
    if (!sel.length) { caixa.innerHTML = '<p class="nota">Nenhum dos itens do link foi encontrado nos dados atuais. <a href="acervo.html">Monte uma nova seleção no Acervo</a>.</p>'; return; }
    var leis = sel.filter(function (a) { return a.situacao; });
    var nom = leis.filter(function (a) { return a.situacao === "nominal"; }).length;
    var cont = { simbolica: 0, comissoes: 0, "sem-registro": 0 }; leis.forEach(function (a) { if (a.situacao in cont) cont[a.situacao]++; });
    var grupos = {}; sel.forEach(function (a) { (grupos[a.subtema] = grupos[a.subtema] || []).push(a); });
    var subs = Object.keys(grupos).map(function (k) { return [k, grupos[k]]; }).sort(function (x, y) { return y[1].length - x[1].length; });
    var nomes = {}; sel.forEach(function (a) { nomes[a.ato] = true; });
    var vs = vot.filter(function (v) { return nomes[v.ato]; }).sort(function (a, b) { return a.data < b.data ? 1 : -1; });
    var stf = sel.filter(function (a) { return a.tipo === "STF"; });
    var q = codificar(ids);
    var link = urlAbsoluta("index.html?" + q + "#painel");
    var editar = "acervo.html?" + q;
    var texto = textoDidatico(pq, sel, leis, nom, subs, link, cont);
    var hoje = new Date().toLocaleDateString("pt-BR");
    var anos = sel.map(function (a) { return a.ano; });
    var acoes = '<div class="acoes-pesquisa">' +
      '<button type="button" class="cheio" data-imprimir="painel">Baixar PDF visual</button>' +
      '<a class="botao zap" href="https://wa.me/?text=' + encodeURIComponent(texto) + '" target="_blank" rel="noopener">Enviar no WhatsApp</a>' +
      '<button type="button" data-copiar="texto-painel">Copiar texto</button>' +
      '<button type="button" data-copiar-link="' + esc(link) + '">Copiar link</button>' +
      '<a class="botao" href="' + esc(editar) + '">Editar esta seleção</a></div><p class="status" role="status"></p>';
    var h = [];
    h.push('<section class="resultado" id="painel" aria-labelledby="titulo-painel">');
    var temaRot = pq.numero_tema ? "Tema " + pq.numero_tema + " de " + pq.total_temas + " · " : (pq.n_temas ? pq.n_temas + " temas · " : "");
    h.push('<div class="r-abertura"><div><p class="rotulo">Resumo visual da seleção · ' + temaRot + esc(pq.situacao) + " · gerado em " + hoje + "</p>" +
      '<h2 id="titulo-painel">' + sel.length + (sel.length === 1 ? " norma escolhida" : " normas escolhidas") + "</h2></div>" +
      '<div class="contador"><strong>' + sel.length + '</strong><span>' + (sel.length === 1 ? "item" : "itens") + "</span></div>" +
      '<p class="lead">' + esc(pq.titulo) + ". Painel montado no seu navegador só com as normas escolhidas no Acervo, de " + Math.min.apply(null, anos) + " a " + Math.max.apply(null, anos) + ".</p></div>");
    if (faltam > 0) h.push('<p class="nota">' + faltam + (faltam === 1 ? " item do link não existe" : " itens do link não existem") + " mais nos dados e " + (faltam === 1 ? "ficou" : "ficaram") + " de fora.</p>");
    h.push(acoes);
    /* achado */
    h.push('<div class="achado" id="painel-achado"><p class="rotulo">Principal achado da seleção</p>');
    if (leis.length) {
      h.push('<p class="grande">' + nom + " <small>de " + leis.length + "</small></p><p>" + (leis.length === 1 ? "lei escolhida, aprovada no Congresso, teve" : "leis escolhidas, aprovadas no Congresso, tiveram") +
        " o voto de cada parlamentar registrado na votação do texto principal. As outras foram aprovadas por votação simbólica (" + cont.simbolica + "), decididas nas comissões (" + cont.comissoes +
        ") ou não têm registro nas bases abertas (" + cont["sem-registro"] + "). Sem registro nominal, não dá para saber como cada parlamentar votou, e isso não indica apoio nem oposição.</p>");
      h.push('<div class="painel"><p class="pequeno">Cada quadrado é uma das leis escolhidas, em ordem de data. Toque para ver a lei.</p><div class="mosaico" role="list" aria-label="Leis escolhidas em ordem de data">' +
        leis.map(function (a) { return '<a class="' + SIT[a.situacao][1] + '" href="acervo.html#' + esc(a.id) + '" title="' + esc(a.ato) + '" aria-label="' + esc(a.ato + ", " + SIT[a.situacao][0].toLowerCase()) + '"></a>'; }).join("") +
        "</div>" + legenda() + "</div>");
    } else {
      h.push('<p class="grande">0 <small>leis</small></p><p>Nenhuma das normas escolhidas é lei votada no Congresso: são decretos, tratados, decisões do STF ou a Constituição.</p>');
    }
    h.push("</div>");
    /* números */
    var nums = [[sel.length, "itens escolhidos", "Acervo do projeto"], [leis.length, "leis aprovadas no Congresso", "Planalto"],
      [nom, "com o voto de cada parlamentar registrado", "Dados abertos da Câmara e do Senado"], [vs.length, "votações nominais do texto principal", "Dados abertos da Câmara e do Senado"],
      [stf.length, "decisões do STF", "Supremo Tribunal Federal"], [sel.length - leis.length - stf.length, "outros atos (decretos, tratados, Constituição)", "Planalto"]];
    h.push('<h2 id="painel-numeros">Em números</h2><ul class="grade-numeros">' + nums.map(function (x) { return "<li><strong>" + milhar(x[0]) + "</strong><span>" + esc(x[1]) + "</span><em>Fonte: " + esc(x[2]) + "</em></li>"; }).join("") + "</ul>");
    /* assuntos */
    h.push('<h2 id="painel-assuntos">Assuntos</h2><p class="pequeno">Um cartão por assunto da seleção. Deslize para o lado.</p><div class="carrossel">');
    subs.forEach(function (sg) {
      var lista = sg[1].slice().sort(function (a, b) { return a.data < b.data ? 1 : -1; }), ult = lista[0];
      var ls = lista.filter(function (a) { return a.situacao; }), nn = ls.filter(function (a) { return a.situacao === "nominal"; }).length;
      h.push('<article class="ccard"><p class="rotulo">' + lista.length + (lista.length === 1 ? " item" : " itens") + "</p><h3>" + esc(sg[0]) + '</h3><p class="chamada">Mais recente: ' + esc(ult.ato) + ", de " + br(ult.data) + ".</p>" +
        (ls.length ? '<div class="dado"><span class="n">' + nn + " de " + ls.length + "</span>leis do assunto tiveram o voto de cada parlamentar registrado.<span class=\"fonte\">Fonte: dados abertos da Câmara e do Senado</span></div>"
                   : '<div class="dado"><span class="n">' + lista.length + '</span>' + (lista.length === 1 ? "ato" : "atos") + ", nenhum deles lei votada no Congresso.<span class=\"fonte\">Fonte: Planalto e STF</span></div>") +
        '<div class="recente"><b>O que diz a mais recente</b>' + esc(ult.resumo) + "</div>" +
        '<details class="mais"><summary>Fatos e fontes</summary><ul class="fatos">' + lista.slice(0, 8).map(function (a) {
          return '<li><a href="acervo.html#' + esc(a.id) + '">' + esc(a.ato) + "</a> (" + a.ano + "): " + esc(a.resumo) + ' <a href="' + esc(a.link) + '" rel="noopener">texto oficial</a></li>'; }).join("") +
        (lista.length > 8 ? "<li>e mais " + (lista.length - 8) + " no Acervo</li>" : "") + "</ul></details></article>");
    });
    h.push("</div>");
    /* linha do tempo */
    var tl = sel.slice(0, 60);
    h.push('<h2 id="painel-tempo">Linha do tempo</h2><p class="pequeno">As normas escolhidas, em ordem de data, com a forma como cada uma foi aprovada.' + (sel.length > 60 ? " Aparecem as 60 primeiras." : "") + '</p><ol class="tempo">' +
      tl.map(function (a) { return '<li><time datetime="' + a.data + '">' + br(a.data) + '</time><div><div class="t-ato"><a href="acervo.html#' + esc(a.id) + '">' + esc(a.ato) + "</a></div><p>" + esc(a.resumo) + "</p>" + selo(a) + ' <span class="pequeno">Governo ' + esc(a.governo) + "</span></div></li>"; }).join("") + "</ol>");
    /* STF */
    if (stf.length) {
      h.push('<h2 id="painel-stf">No Supremo</h2><div class="carrossel">' + stf.map(function (a) {
        var s = a.stf || {};
        return '<article class="ccard stf"><p class="rotulo">STF · ' + esc(s.caso || a.ato) + " · " + a.ano + "</p><h3>" + esc(a.resumo) + '</h3><div class="fato"><b>Situação: ' + esc(s.status || "—") + "</b>" + esc(s.resultado || "") +
          '</div><p class="pequeno"><a href="acervo.html#' + esc(a.id) + '">Detalhes e cronologia</a> · <a href="' + esc(a.link) + '" rel="noopener">Fonte</a></p></article>'; }).join("") + "</div>");
    }
    /* votações nominais */
    if (vs.length) {
      h.push('<h2 id="painel-votos">Votações com voto registrado</h2><p class="pequeno">Votações nominais do texto principal das leis escolhidas (leis do núcleo do tema). Votar sim significa aprovar o texto que virou lei.</p><ol class="ranking">' +
        vs.map(function (v) { return '<li><div><div class="r-titulo">' + esc(v.ato) + '</div><div class="r-meta">' + esc(v.casa) + " · " + br(v.data) + " · " + v.sim + " sim · " + v.nao + " não" + (v.abst ? " · " + v.abst + " abst." : "") + (v.obst ? " · " + v.obst + " obstr." : "") + "</div>" + barra(v) +
          '<div class="pequeno"><a href="' + esc(v.fonte) + '" rel="noopener">Tramitação oficial</a> · <a href="' + esc(v.dados_abertos) + '" rel="noopener">Dados abertos</a></div></div></li>'; }).join("") + "</ol>");
    }
    /* baixar e compartilhar */
    h.push('<h2 id="painel-baixar" class="so-tela">Baixar e compartilhar</h2>' + acoes +
      '<details class="mais" open><summary>Texto para o WhatsApp (' + (texto.length - link.length) + ' caracteres, mais o link)</summary><p class="post" id="texto-painel">' + esc(texto) + "</p></details>");
    h.push('<div class="limites"><strong>Limites.</strong><ul><li>Os números deste painel valem só para as normas escolhidas. Não representam o tema inteiro.</li>' +
      '<li>Versão preliminar: os dados ainda passam por checagem final.</li><li>A Câmara não tem votos individuais nas bases abertas antes de 2005.</li></ul>' +
      '<p class="pequeno">Fontes: Planalto (legislação), dados abertos da Câmara e do Senado, Supremo Tribunal Federal. Cada item tem o link da sua fonte no <a href="acervo.html">Acervo</a>.</p>' +
      '<p class="so-impressao">Gerado em <span class="data-impressao"></span>. Abra e edite esta seleção em: ' + esc(link) + "</p></div>");
    h.push(pq.id ? '<p><a href="pesquisa-' + esc(pq.id) + '.html">Ver o resultado completo da pesquisa deste tema</a></p></section>'
                 : '<p><a href="index.html#temas">Ver os temas do projeto</a></p></section>');
    caixa.innerHTML = h.join("\n");
  }
  var caixaPainel = document.getElementById("painel-selecao");
  if (caixaPainel) {
    var pedido = null;
    try { pedido = decodificar(new URLSearchParams(location.search)); } catch (e) {}
    if (pedido) {
      caixaPainel.hidden = false;
      caixaPainel.innerHTML = '<p class="pequeno">Montando o painel da seleção…</p>';
      var destaque = document.getElementById("resultado-destaque"); if (destaque) destaque.hidden = true;
      fetch("dados/pesquisas.json").then(function (r) { return r.json(); }).then(function (cad) {
        /* a seleção pode ter itens de mais de um tema: carrega cada pesquisa envolvida (pelo prefixo dos ids) */
        var prefs = {};
        if (pedido.p) prefs[pedido.p] = true;
        pedido.ids.forEach(function (i) { var m = /^([A-Z]+)-/.exec(i); if (m) prefs[m[1]] = true; });
        var pqs = (pedido.todos && !pedido.p) ? cad.pesquisas : cad.pesquisas.filter(function (x) { return prefs[x.prefixo]; });
        if (!pqs.length) pqs = cad.pesquisas.slice(0, 1);
        return Promise.all(pqs.map(function (pq) {
          return Promise.all([fetch("dados/" + pq.dados.atos).then(function (r) { return r.json(); }),
            pq.dados.votacoes ? fetch("dados/" + pq.dados.votacoes).then(function (r) { return r.json(); }) : []]).then(function (d) { return { pq: pq, atos: d[0], vot: d[1] }; });
        })).then(function (res) {
          var atos = [], vot = [], visto = {};
          res.forEach(function (r) {
            atos = atos.concat(r.atos);
            r.vot.forEach(function (v) { var k = v.ato + "|" + v.casa + "|" + v.data; if (!visto[k]) { visto[k] = true; vot.push(v); } });
          });
          var pq = pqs.length === 1 ? pqs[0] : { id: "", n_temas: pqs.length, titulo: "Seleção com itens de " + pqs.length + " temas: " + pqs.map(function (x) { return x.tema; }).join(", "),
            assunto: pqs.map(function (x) { return x.assunto; }).join(" e "), situacao: pqs[0].situacao, fonte_congresso: pqs[0].fonte_congresso };
          pq.total_temas = cad.total_temas;
          montarPainel(caixaPainel, pq, atos, vot, pedido);
          var ori = document.querySelector(".orientacao .coluna");
          if (ori) ori.innerHTML = '<span class="voce">Você está em <strong>Resumo visual</strong>.</span> Painel da sua seleção: baixe em PDF, envie no WhatsApp ou edite a seleção. <a href="index.html">Voltar ao início</a>';
          if (location.hash === "#painel") { var alvo = document.getElementById("painel"); if (alvo) alvo.scrollIntoView(); }
        });
      }).catch(function () {
        caixaPainel.innerHTML = '<p class="nota">Não foi possível montar o painel agora. Verifique a conexão e tente de novo.</p>';
        if (destaque) destaque.hidden = false;
      });
    }
  }

  /* ------------------------------------------------------------ acervo */
  var lista = document.getElementById("lista");
  if (!lista) return;
  var itens = Array.prototype.slice.call(lista.children);
  var campo = document.getElementById("q");
  var filtros = Array.prototype.slice.call(document.querySelectorAll("[data-filtro]"));
  var contagem = document.getElementById("contagem");
  var botaoTodos = document.getElementById("selecionar-todos");
  var soSelecao = false;
  itens.forEach(function (li) { li._txt = norm(li.getAttribute("data-txt") + " " + li.textContent); });
  function visiveis() { return itens.filter(function (li) { return !li.hidden; }); }

  function aplicar() {
    var termos = norm(campo.value).split(/\s+/).filter(Boolean);
    var sel = ler();
    var n = 0;
    itens.forEach(function (li) {
      var ok = termos.every(function (t) { return li._txt.indexOf(t) !== -1; });
      filtros.forEach(function (f) {
        if (!ok) return;
        if (f.type === "checkbox") { if (!f.checked && li.getAttribute(f.getAttribute("data-filtro")) === "sim") ok = false; }
        else if (f.value && li.getAttribute(f.getAttribute("data-filtro")) !== f.value) ok = false;
      });
      if (soSelecao && sel.indexOf(li.id) === -1) ok = false;
      li.hidden = !ok;
      if (ok) n++;
    });
    contagem.textContent = n + (n === 1 ? " item" : " itens") + (soSelecao ? " na sua seleção" : "");
    pintarTodos();
  }
  function pintarTodos() {
    if (!botaoTodos) return;
    var vis = visiveis(), sel = ler();
    var todos = vis.length > 0 && vis.every(function (li) { return sel.indexOf(li.id) !== -1; });
    botaoTodos.hidden = vis.length === 0;
    botaoTodos.textContent = todos ? "Tirar os " + vis.length + " da seleção" : "Selecionar todos (" + vis.length + ")";
    botaoTodos.setAttribute("aria-pressed", todos ? "true" : "false");
  }
  var espera;
  campo.addEventListener("input", function () { clearTimeout(espera); espera = setTimeout(aplicar, 150); });
  filtros.forEach(function (f) { f.addEventListener("change", aplicar); });
  /* nova busca: limpa o texto e os filtros e volta a mostrar tudo */
  var nova = document.getElementById("nova-busca");
  if (nova) nova.addEventListener("click", function () {
    campo.value = "";
    filtros.forEach(function (f) { if (f.type === "checkbox") f.checked = f.defaultChecked; else f.value = ""; });
    var painel = document.querySelector("details.filtros"); if (painel) painel.open = false;
    if (soSelecao) { soSelecao = false; document.getElementById("ver-selecao").textContent = "Ver"; }
    aplicar();
    campo.focus();
  });

  /* seleção */
  var rotulo = document.getElementById("n-selecao");
  var linkResumo = document.getElementById("resumo-selecao");
  function pintarSelecao() {
    var sel = ler();
    itens.forEach(function (li) {
      var on = sel.indexOf(li.id) !== -1;
      li.classList.toggle("selecionado", on);
      var b = li.querySelector("[data-selecionar]");
      if (b) { b.setAttribute("aria-pressed", on ? "true" : "false"); b.textContent = on ? "Na seleção" : "Adicionar à seleção"; }
    });
    rotulo.textContent = sel.length;
    if (linkResumo) linkResumo.href = "index.html?" + codificar(sel) + "#painel";
    var barra = document.getElementById("barra-selecao");
    if (barra) barra.hidden = sel.length === 0 && !soSelecao;
    pintarTodos();
  }
  lista.addEventListener("click", function (ev) {
    var b = ev.target.closest("[data-selecionar]");
    if (!b) return;
    var id = b.closest("li").id, sel = ler(), i = sel.indexOf(id);
    if (i === -1) { sel.push(id); status("Adicionado à seleção."); } else { sel.splice(i, 1); status("Retirado da seleção."); }
    gravar(sel); pintarSelecao();
  });
  if (botaoTodos) botaoTodos.addEventListener("click", function () {
    var vis = visiveis().map(function (li) { return li.id; }), sel = ler();
    var todos = vis.every(function (id) { return sel.indexOf(id) !== -1; });
    if (todos) { sel = sel.filter(function (id) { return vis.indexOf(id) === -1; }); status(vis.length + " itens retirados da seleção.", botaoTodos); }
    else { vis.forEach(function (id) { if (sel.indexOf(id) === -1) sel.push(id); }); status(vis.length + " itens na seleção. Toque em “Resumo visual” para ver o painel.", botaoTodos); }
    gravar(sel); pintarSelecao();
    if (soSelecao) aplicar();
  });
  document.getElementById("ver-selecao").addEventListener("click", function () {
    soSelecao = !soSelecao;
    this.textContent = soSelecao ? "Tudo" : "Ver";
    aplicar();
  });
  document.getElementById("limpar-selecao").addEventListener("click", function () { gravar([]); soSelecao = false; document.getElementById("ver-selecao").textContent = "Ver"; pintarSelecao(); aplicar(); status("Seleção apagada."); });
  document.getElementById("pdf-selecao").addEventListener("click", function () {
    var sel = ler();
    if (!sel.length) { status("Adicione itens à seleção antes de gerar o PDF."); return; }
    document.body.classList.add("imprimir-selecao");
    itens.forEach(function (li) { if (sel.indexOf(li.id) !== -1) { var d = li.querySelector("details"); if (d) d.open = true; } });
    var data = document.getElementById("data-impressao"); if (data) data.textContent = new Date().toLocaleDateString("pt-BR");
    window.print();
  });

  /* abrir item pelo endereço (#MUL-...) */
  function abrirHash() {
    var id = decodeURIComponent(location.hash.slice(1));
    var li = id && document.getElementById(id);
    if (li && li.parentNode === lista) { li.hidden = false; var d = li.querySelector("details"); if (d) d.open = true; li.scrollIntoView(); }
  }
  window.addEventListener("hashchange", abrirHash);
  /* filtros e seleção vindos do endereço: ?tema=Educação, ?assunto=Saúde, ?tipo=Decreto, ?q=palavra, ?p=MUL&s=... (seleção de um link) */
  var avisoLink = "";
  try {
    var prm = new URLSearchParams(location.search), mapa = { tema: "data-tema", assunto: "data-sub", tipo: "data-tipo", governo: "data-gov" }, algum = false;
    Object.keys(mapa).forEach(function (k) {
      var v = prm.get(k), sel = document.querySelector('[data-filtro="' + mapa[k] + '"]');
      if (v && sel) { sel.value = v; algum = true; }
    });
    if (prm.get("q")) campo.value = prm.get("q");
    if (algum) { var pf = document.querySelector("details.filtros"); if (pf) pf.open = true; }
    var ped = decodificar(prm);
    if (ped) {
      var existentes = {}; itens.forEach(function (li) { existentes[li.id] = true; });
      var ids = ped.todos ? itens.map(function (li) { return li.id; }) : ped.ids.filter(function (i) { return existentes[i]; });
      gravar(ids); soSelecao = true; document.getElementById("ver-selecao").textContent = "Tudo";
      avisoLink = "Seleção do link carregada: " + ids.length + " itens. Tire ou acrescente itens e toque em “Resumo visual” para gerar a sua versão.";
    }
  } catch (e) {}
  memoria = ler();
  pintarSelecao(); aplicar(); abrirHash();
  if (avisoLink) { var sb = document.getElementById("status-busca"); if (sb) sb.textContent = avisoLink; else status(avisoLink); }
})();
