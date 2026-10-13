# -*- coding: utf-8 -*-
"""Gera o PDF resumido de cada pesquisa do cadastro (dados/pesquisas.json),
a partir da página de resumo dela (por exemplo, resumo.html -> downloads/resumo_piloto_direitos_mulheres.pdf).
Requer: pip install playwright && python -m playwright install chromium
Uso:   python3 scripts/gerar_pdf.py   (rodar depois de gerar_site.py)"""
import asyncio, json, os
from playwright.async_api import async_playwright

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PESQ = json.load(open(os.path.join(RAIZ, "dados", "pesquisas.json"), encoding="utf-8"))["pesquisas"]

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page()
        for pq in PESQ:
            await pg.goto("file://" + os.path.join(RAIZ, pq["paginas"]["resumo"]))
            await pg.pdf(path=os.path.join(RAIZ, pq["pdf"]), format="A4", print_background=True,
                         margin=dict(top="18mm", bottom="18mm", left="16mm", right="16mm"))
            print("PDF gerado:", pq["pdf"])
        await b.close()

asyncio.run(main())
