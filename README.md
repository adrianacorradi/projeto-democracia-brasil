# Projeto Democracia Brasil — site

Site estático, leve e pensado primeiro para celular, com o acervo do Projeto Democracia Brasil: leis, decretos, tratados e decisões do STF desde 1985, com a fonte oficial de cada informação.

Funciona sem servidor, sem banco de dados e sem bibliotecas externas. Cada página pesa menos de 40 KB comprimida.

## Publicar no GitHub Pages

1. Crie um repositório no GitHub, por exemplo `democracia-brasil`.
2. Envie **todo o conteúdo desta pasta** para a raiz do repositório. Pelo site do GitHub, use "Add file" e depois "Upload files". Arraste os arquivos e as pastas.
3. No repositório, abra **Settings**, depois **Pages**. Em "Build and deployment", escolha **Deploy from a branch**, branch `main`, pasta `/ (root)`, e clique em **Save**.
4. Em alguns minutos o site estará em `https://SEU-USUARIO.github.io/democracia-brasil/`.
5. Coloque esse endereço em `dados/config.json` (campo `url_site`) e gere o site de novo. Assim o endereço aparece no PDF resumido.

O arquivo `.nojekyll` precisa ir junto: ele faz o GitHub publicar os arquivos como estão.

## Estrutura

| Pasta ou arquivo | O que é |
|---|---|
| `index.html` | Início: mosaico das leis, temas e novidades |
| `acervo.html` | Acervo com busca, filtros, seleção e PDF da seleção |
| `votacoes.html` | Como o Congresso votou: lacunas e votações nominais |
| `entenda.html` | Caminho de uma lei, glossário e método, para leigos |
| `compartilhar.html` | Textos prontos para redes sociais, com fontes |
| `baixar.html` | Downloads |
| `resumo.html` | Base do PDF resumido |
| `assets/` | Estilo, script, ícone e o vídeo "Como usar o site" (`tutorial.mp4`, com capa e miniatura) |
| `dados/` | Dados que alimentam as páginas (JSON) |
| `downloads/` | PDF, planilha, CSVs e guia metodológico |
| `scripts/` | Geradores do site e do PDF |

## Atualizar o site

As páginas HTML são **geradas** a partir de `dados/`. Não edite os HTML à mão.

1. Atualize os arquivos de `dados/`. São eles: `atos.json`, `mosaico.json`, `lacunas.json`, `votacoes_indice.json` e `meta.json`, que vêm da planilha-mestre, e `posts.json`, `novidades.json`, `temas.json`, `tutorial.json` e `config.json`, que são editoriais. O `video.json` é gravado pelo gerador do vídeo.
2. Rode `python3 scripts/gerar_site.py`.
3. Rode `python3 scripts/gerar_pdf.py` (opcional; precisa do Playwright).
4. Se as telas mudaram, grave de novo o vídeo "Como usar o site": `python3 scripts/gerar_video.py` (precisa do Playwright, do Pillow e do ffmpeg). As legendas ficam em `dados/tutorial.json`. Depois rode `gerar_site.py` outra vez, para atualizar a duração e o tamanho do vídeo na página.
5. Substitua os arquivos de `downloads/` que mudaram.
6. Registre a mudança em `dados/novidades.json`.
7. Envie as alterações para o GitHub.

## Princípios

- Toda informação tem link para a fonte oficial.
- Linguagem neutra e simples; termos técnicos explicados em `entenda.html`.
- Sem rankings de governos por contagem de leis.
- Acessível: funciona sem JavaScript (exceto a busca), com teclado, em telas pequenas e no modo escuro.
