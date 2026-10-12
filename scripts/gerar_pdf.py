# -*- coding: utf-8 -*-
"""Gera downloads/resumo_piloto_direitos_mulheres.pdf a partir de resumo.html.
Requer: pip install playwright && python -m playwright install chromium
Uso:   python3 scripts/gerar_pdf.py   (rodar depois de gerar_site.py)"""
import asyncio, os
from playwright.async_api import async_playwright

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page()
        await pg.goto("file://" + os.path.join(RAIZ, "resumo.html"))
        await pg.pdf(path=os.path.join(RAIZ, "downloads", "resumo_piloto_direitos_mulheres.pdf"), format="A4",
                     print_background=True, margin=dict(top="18mm", bottom="18mm", left="16mm", right="16mm"))
        await b.close()

asyncio.run(main())
print("PDF gerado em downloads/resumo_piloto_direitos_mulheres.pdf")
