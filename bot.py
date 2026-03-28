import os
import json
import time
import requests
from bs4 import BeautifulSoup

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

buscas = [
    "hot wheels super treasure hunt",
    "mini gt skyline",
    "kaido house",
    "inno64 skyline"
]

ARQUIVO = "precos.json"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7"
}

# 📦 HISTÓRICO
if os.path.exists(ARQUIVO):
    with open(ARQUIVO, "r", encoding="utf-8") as f:
        historico = json.load(f)
else:
    historico = {}


def salvar():
    with open(ARQUIVO, "w", encoding="utf-8") as f:
        json.dump(historico, f, ensure_ascii=False, indent=2)


def enviar_telegram(msg):
    if not TOKEN or not CHAT_ID:
        print("❌ TOKEN ou CHAT_ID não configurados.")
        return

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    try:
        resposta = requests.post(
            url,
            data={"chat_id": CHAT_ID, "text": msg},
            timeout=30
        )
        print(f"📨 Telegram status: {resposta.status_code}")
    except Exception as e:
        print("Erro ao enviar:", e)


# 🧠 CLASSIFICAÇÃO
def classificar(titulo):
    t = titulo.lower()

    if "super treasure hunt" in t or "sth" in t:
        return "sth"
    elif "mini gt" in t or "kaido house" in t or "inno64" in t:
        return "premium"
    else:
        return "comum"


# 🚫 FILTRO DE LIXO
def lixo(titulo):
    t = titulo.lower()
    bloqueados = [
        "mario",
        "star wars",
        "boneco",
        "racer verse"
    ]
    return any(p in t for p in bloqueados)


# 🔎 BUSCA
def buscar():
    for termo in buscas:
        print(f"🔎 Buscando: {termo}")

        url = f"https://lista.mercadolivre.com.br/{termo.replace(' ', '-')}"

        try:
            response = requests.get(url, headers=headers, timeout=30)

            print("Status:", response.status_code)
            print("URL final:", response.url)

            if response.status_code != 200:
                print("Erro:", response.status_code)
                continue

            soup = BeautifulSoup(response.text, "lxml")

            itens = soup.select("li.ui-search-layout__item")
            if not itens:
                itens = soup.select("ol.ui-search-layout li")
            if not itens:
                itens = soup.select("div.ui-search-result__wrapper")

            print(f"Encontrados: {len(itens)} itens")

            if len(itens) == 0:
                print("Título da página:", soup.title.string if soup.title else "Sem título")
                print("Trecho HTML:", response.text[:500])
                continue

            for item in itens:
                titulo_tag = (
                    item.select_one("a.poly-component__title")
                    or item.select_one("a.ui-search-item__group__element")
                    or item.select_one("h2 a")
                )

                preco_tag = (
                    item.select_one("span.andes-money-amount__fraction")
                    or item.select_one(".price-tag-fraction")
                )

                if not titulo_tag or not preco_tag:
                    continue

                titulo = titulo_tag.get_text(strip=True)

                try:
                    preco = int(
                        preco_tag.get_text(strip=True)
                        .replace(".", "")
                        .replace(",", "")
                    )
                except ValueError:
                    continue

                link = titulo_tag.get("href", "").split("#")[0]
                item_id = link.split("?")[0]

                if not link:
                    continue

                if lixo(titulo):
                    continue

                tipo = classificar(titulo)
                preco_antigo = historico.get(item_id)

                # 🚨 PROMOÇÃO
                if preco_antigo:
                    queda = preco_antigo - preco

                    if queda > 0:
                        percentual = (queda / preco_antigo) * 100

                        if percentual >= 20:
                            msg = f"""🚨 PROMOÇÃO

🚗 {titulo}
💰 De: R$ {preco_antigo}
🔥 Por: R$ {preco}
📉 {percentual:.0f}% OFF

🔗 {link}
"""
                            print("🚨 Promoção:", titulo)
                            enviar_telegram(msg)

                # 🎯 SNIPER
                enviar = False
                tag = ""

                if tipo == "comum" and preco <= 100:
                    enviar = True
                    tag = "🔥 OPORTUNIDADE"

                elif tipo == "sth" and preco <= 200:
                    enviar = True
                    tag = "💎 STH (Preço Bom)"

                elif tipo == "premium" and preco <= 220:
                    enviar = True
                    tag = "💎 PREMIUM (Preço Bom)"

                if enviar:
                    msg = f"""{tag}

🚗 {titulo}
💰 R$ {preco}
🔎 {termo}
🔗 {link}
"""
                    print("🔥 Sniper:", titulo)
                    enviar_telegram(msg)

                historico[item_id] = preco

        except Exception as e:
            print("Erro:", e)

    salvar()


if __name__ == "__main__":
    print("🚀 Bot iniciado")
    while True:
        buscar()
        print("⏳ Aguardando 10 minutos...\n")
        time.sleep(600)