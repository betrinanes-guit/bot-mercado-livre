import os
import requests
from bs4 import BeautifulSoup
import time
import json

TOKEN = os.getenv("8282034895:AAFBtrnwQYhZzVSA_qAH43eYuLCxLU1aTn8")
CHAT_ID = os.getenv("233452068")

# 🔐 CONFIGURAÇÃO
# TOKEN = "8282034895:AAFBtrnwQYhZzVSA_qAH43eYuLCxLU1aTn8"
# CHAT_ID = "233452068"

buscas = [
    "hot wheels super treasure hunt",
    "mini gt skyline",
    "kaido house",
    "inno64 skyline"
]

ARQUIVO = "precos.json"

headers = {
    "User-Agent": "Mozilla/5.0"
}

# 📦 HISTÓRICO
if os.path.exists(ARQUIVO):
    with open(ARQUIVO, "r") as f:
        historico = json.load(f)
else:
    historico = {}

def salvar():
    with open(ARQUIVO, "w") as f:
        json.dump(historico, f)

def enviar_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
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
            response = requests.get(url, headers=headers)

            if response.status_code != 200:
                print("Erro:", response.status_code)
                continue

            soup = BeautifulSoup(response.text, "lxml")

            itens = soup.find_all("li", class_="ui-search-layout__item")

            print(f"Encontrados: {len(itens)} itens")

            for item in itens:
                titulo_tag = item.find("a", class_="poly-component__title")
                preco_tag = item.find("span", class_="andes-money-amount__fraction")

                if not titulo_tag or not preco_tag:
                    continue

                titulo = titulo_tag.text.strip()
                preco = int(preco_tag.text.replace(".", ""))
                link = titulo_tag["href"].split("#")[0]

                item_id = link.split("?")[0]

                # 🚫 lixo
                if lixo(titulo):
                    continue

                tipo = classificar(titulo)

                preco_antigo = historico.get(item_id)

                # 🚨 PROMOÇÃO (queda de preço)
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

                # 🎯 SNIPER (só MUITO barato)
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

                # 🚫 só envia se for MUITO barato
                if enviar and preco <= 100:
                    msg = f"""{tag}

🚗 {titulo}
💰 R$ {preco}
🔎 {termo}
🔗 {link}
"""
                    print("🔥 Sniper:", titulo)
                    enviar_telegram(msg)

                # 💾 salva histórico
                historico[item_id] = preco

        except Exception as e:
            print("Erro:", e)

    salvar()

# 🔁 LOOP
while True:
    buscar()
    print("⏳ Aguardando 10 minutos...\n")
    time.sleep(600)