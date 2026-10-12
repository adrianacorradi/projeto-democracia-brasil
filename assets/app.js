/* Projeto Democracia Brasil — busca, seleção e compartilhamento. Sem dependências. */
(function () {
  "use strict";
  var CHAVE = "pdb-selecao";
  function norm(s) { return (s || "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase(); }
  function ler() { try { return JSON.parse(localStorage.getItem(CHAVE) || "[]"); } catch (e) { return memoria; } }
  function gravar(v) { memoria = v; try { localStorage.setItem(CHAVE, JSON.stringify(v)); } catch (e) {} }
  var memoria = [];
  function status(msg) {
    var el = document.getElementById("status");
    if (el) { el.textContent = msg; setTimeout(function () { if (el.textContent === msg) el.textContent = ""; }, 4000); }
  }

  /* compartilhar ou copiar */
  function compartilhar(titulo, texto, url) {
    if (navigator.share) {
      navigator.share({ title: titulo, text: texto, url: url }).catch(function () {});
      return;
    }
    var completo = texto + (url ? "\n" + url : "");
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(completo).then(function () { status("Texto copiado."); }, function () { status("Não foi possível copiar. Selecione o texto e copie."); });
    } else { status("Selecione o texto e copie."); }
  }
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
      compartilhar(document.title, texto, url);
    }
    var c = ev.target.closest("[data-copiar]");
    if (c) {
      var el = document.getElementById(c.getAttribute("data-copiar"));
      var txt = el ? el.innerText : "";
      if (c.hasAttribute("data-share") && navigator.share) { navigator.share({ text: txt }).catch(function () {}); return; }
      if (navigator.clipboard) navigator.clipboard.writeText(txt).then(function () { status("Texto copiado."); });
    }
  });

  /* vídeo da página inicial: toca ao abrir, pausa ao fechar */
  document.addEventListener("toggle", function (ev) {
    var d = ev.target;
    if (!d.classList || !d.classList.contains("video-tutorial")) return;
    var v = d.querySelector("video");
    if (!v) return;
    if (d.open) { if (!v.getAttribute("poster") && v.dataset.poster) v.setAttribute("poster", v.dataset.poster); var p = v.play(); if (p && p.catch) p.catch(function () {}); } else { v.pause(); }
  }, true);

  /* acervo */
  var lista = document.getElementById("lista");
  if (!lista) return;
  var itens = Array.prototype.slice.call(lista.children);
  var campo = document.getElementById("q");
  var filtros = Array.prototype.slice.call(document.querySelectorAll("[data-filtro]"));
  var contagem = document.getElementById("contagem");
  var soSelecao = false;
  itens.forEach(function (li) { li._txt = norm(li.getAttribute("data-txt") + " " + li.textContent); });

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
  }
  var espera;
  campo.addEventListener("input", function () { clearTimeout(espera); espera = setTimeout(aplicar, 150); });
  filtros.forEach(function (f) { f.addEventListener("change", aplicar); });

  /* seleção */
  var rotulo = document.getElementById("n-selecao");
  function pintarSelecao() {
    var sel = ler();
    itens.forEach(function (li) {
      var on = sel.indexOf(li.id) !== -1;
      li.classList.toggle("selecionado", on);
      var b = li.querySelector("[data-selecionar]");
      if (b) { b.setAttribute("aria-pressed", on ? "true" : "false"); b.textContent = on ? "Na seleção" : "Adicionar à seleção"; }
    });
    rotulo.textContent = sel.length;
    var barra = document.getElementById("barra-selecao");
    if (barra) barra.hidden = sel.length === 0 && !soSelecao;
  }
  lista.addEventListener("click", function (ev) {
    var b = ev.target.closest("[data-selecionar]");
    if (!b) return;
    var id = b.closest("li").id, sel = ler(), i = sel.indexOf(id);
    if (i === -1) { sel.push(id); status("Adicionado à seleção."); } else { sel.splice(i, 1); status("Retirado da seleção."); }
    gravar(sel); pintarSelecao();
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
  window.addEventListener("afterprint", function () { document.body.classList.remove("imprimir-selecao"); });

  /* abrir item pelo endereço (#MUL-...) */
  function abrirHash() {
    var id = decodeURIComponent(location.hash.slice(1));
    var li = id && document.getElementById(id);
    if (li && li.parentNode === lista) { li.hidden = false; var d = li.querySelector("details"); if (d) d.open = true; li.scrollIntoView(); }
  }
  window.addEventListener("hashchange", abrirHash);
  memoria = ler();
  pintarSelecao(); aplicar(); abrirHash();
})();
