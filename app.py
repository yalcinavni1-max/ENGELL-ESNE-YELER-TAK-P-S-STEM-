import re
from flask import Flask, jsonify, request, send_from_directory
import requests
from bs4 import BeautifulSoup
from flask_cors import CORS
import time
import random

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

# --- 1. HESAP GRUPLARI ---
HESAPLAR = {
    "abt": [
        "https://www.leagueofgraphs.com/summoner/tr/Ragnar+Lothbrok-0138",
        "https://www.leagueofgraphs.com/summoner/tr/D%C3%96L+VE+OKS%C4%B0JEN-011"
    ],
    "yiğit": ["https://www.leagueofgraphs.com/summoner/tr/EGO-19050"],
    "dogi": ["https://www.leagueofgraphs.com/summoner/tr/xXZeUs01-TR1"],
    "fedo": ["https://www.leagueofgraphs.com/summoner/tr/betrayal1907-KURT"],
    "kayhan": [
        "https://www.leagueofgraphs.com/summoner/tr/AMIN+O%C4%9ELU+SC-3831",
        "https://www.leagueofgraphs.com/summoner/tr/EYouLoST-TR1"
    ],
    "yerli": ["https://www.leagueofgraphs.com/summoner/tr/Tangal%C4%B1+ILLAO%C4%B0-TR1"],
    "memet": ["https://www.leagueofgraphs.com/summoner/tr/Kaybeden-3131"],
    "oktay": ["https://www.leagueofgraphs.com/summoner/tr/kaybetmeyen-svm"],
    "alper": ["https://www.leagueofgraphs.com/summoner/tr/22010600025-3131"],
    "avni": ["https://www.leagueofgraphs.com/summoner/tr/JAYLES-SAMA"],
    "ibo": [
        "https://www.leagueofgraphs.com/summoner/tr/Retruyol-one",
        "https://www.leagueofgraphs.com/summoner/euw/retruyol-EUW"
    ],
    "furkan": ["https://www.leagueofgraphs.com/summoner/tr/Legorn-RNG"],
    "kofi": ["https://www.leagueofgraphs.com/summoner/tr/KOFI-KOOFI"],
    "musto": ["https://www.leagueofgraphs.com/summoner/tr/QUZEY+TEK%C4%B0NO%C4%9ELU-CAZ"],
    "kaan": ["https://www.leagueofgraphs.com/summoner/tr/Eloha-111"],
    "murat": ["https://www.leagueofgraphs.com/summoner/tr/call%20me%20sch-911"],
    "taha": ["https://www.leagueofgraphs.com/summoner/tr/Killdozer-3807"],
    "hepsi": []
}

# Hepsi grubunu otomatik doldur
all_links = []
for k, v in HESAPLAR.items():
    if k != "hepsi": all_links.extend(v)
HESAPLAR["hepsi"] = list(set(all_links))

@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

def get_latest_version():
    try:
        r = requests.get("https://ddragon.leagueoflegends.com/api/versions.json", timeout=3)
        if r.status_code == 200: return r.json()[0]
    except: pass
    return "14.3.1"

def calculate_grade(score):
    if score >= 4.0: return "S"
    elif score >= 3.0: return "A"
    elif score >= 2.5: return "B"
    elif score >= 2.0: return "C"
    elif score >= 1.0: return "D"
    else: return "F"

# --- SCRAPER ---
def scrape_summoner(url):
    time.sleep(random.uniform(0.3, 0.7))
    version = get_latest_version()
    RIOT_CDN = f"https://ddragon.leagueoflegends.com/cdn/{version}/img"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.content, 'html.parser')

        summoner_name = "Sihirdar"
        try: summoner_name = soup.find("title").text.split("(")[0].strip().replace(" - League of Legends", "")
        except: pass

        rank_text = "Unranked"
        try:
            banner = soup.find("div", class_="bannerSubtitle")
            rank_text = banner.text.strip() if banner else soup.find("div", class_="league-tier").text.strip()
        except: pass

        profile_icon = f"{RIOT_CDN}/profileicon/29.png"
        try:
            img = soup.find("div", class_="img").find("img")
            if img: profile_icon = "https:" + img.get("src")
        except: pass

        matches_info = []
        all_rows = soup.find_all("tr")
        
        for row in all_rows:
            try:
                kda_div = row.find("div", class_="kda")
                if not kda_div: continue

                # --- 1. OYUN SÜRESİ ---
                game_duration = 0
                duration_div = row.find("div", class_="gameDuration")
                if duration_div:
                    dur_text = duration_div.text.strip()
                    min_match = re.search(r"(\d+)", dur_text)
                    if min_match: game_duration = int(min_match.group(1))

                # --- 2. OYUN TÜRÜ (DÜZELTİLMİŞ) ---
                queue_mode = "Normal"
                
                # A) Direkt QueueType Div'i
                q_div = row.find("div", class_="queueType")
                if q_div:
                    raw_q = q_div.text.strip()
                    if "Ranked Solo" in raw_q: queue_mode = "Solo/Duo"
                    elif "Ranked Flex" in raw_q: queue_mode = "Flex"
                    elif "ARAM" in raw_q: queue_mode = "ARAM"
                    elif "Arena" in raw_q: queue_mode = "Arena"
                    else: queue_mode = raw_q.split()[0]
                else:
                    # B) GameMode Div'i
                    g_div = row.find("div", class_="gameMode")
                    if g_div:
                        raw_g = g_div.text.strip()
                        if "Solo" in raw_g: queue_mode = "Solo/Duo"
                        elif "Flex" in raw_g: queue_mode = "Flex"
                        else: queue_mode = raw_g
                    else:
                        # C) Metin Taraması (Son Çare)
                        row_text = row.text.strip()
                        if "Ranked Solo" in row_text: queue_mode = "Solo/Duo"
                        elif "Ranked Flex" in row_text: queue_mode = "Flex"
                        elif "ARAM" in row_text: queue_mode = "ARAM"

                # --- 3. ŞAMPİYON BULMA ---
                champ_key = "Poro"
                links = row.find_all("a")
                for link in links:
                    href = link.get("href", "")
                    if "/champions/builds/" in href:
                        parts = href.split("/")
                        if len(parts) > 3:
                            raw = parts[3].replace("-", "").replace(" ", "").lower()
                            name_map = {
                                "wukong": "MonkeyKing", "renata": "Renata", "missfortune": "MissFortune",
                                "masteryi": "MasterYi", "drmundo": "DrMundo", "jarvaniv": "JarvanIV",
                                "tahmkench": "TahmKench", "xinzhao": "XinZhao", "kogmaw": "KogMaw",
                                "reksai": "RekSai", "kaisa": "Kaisa", "velkoz": "Velkoz",
                                "chogath": "Chogath", "khazix": "Khazix", "belveth": "Belveth",
                                "leblanc": "Leblanc", "nunu&willump": "Nunu"
                            }
                            champ_key = name_map.get(raw, raw.capitalize())
                            break
                
                if champ_key == "Poro":
                    for img in row.find_all("img"):
                        alt = img.get("alt", "")
                        if alt and len(alt) > 2 and alt not in ["Victory", "Defeat", "Role", "Item", "Gold"]:
                            raw_alt = alt.replace(" ", "").replace("'", "").replace(".", "")
                            if "LeBlanc" in raw_alt: champ_key = "Leblanc"
                            elif "Nunu" in raw_alt: champ_key = "Nunu"
                            elif "KaiSa" in raw_alt: champ_key = "Kaisa"
                            elif "RekSai" in raw_alt: champ_key = "RekSai"
                            elif "VelKoz" in raw_alt: champ_key = "Velkoz"
                            elif "ChoGath" in raw_alt: champ_key = "Chogath"
                            elif "KhaZix" in raw_alt: champ_key = "Khazix"
                            elif "Wukong" in raw_alt: champ_key = "MonkeyKing"
                            else: champ_key = raw_alt
                            break
                final_champ_img = f"{RIOT_CDN}/champion/{champ_key}.png"

                # --- 4. İTEMLER (Resimsizleri Eledik) ---
                items = []
                img_tags = row.find_all("img")
                for img in img_tags:
                    img_str = str(img)
                    if any(x in img_str for x in ["champion", "spell", "tier", "perk"]): continue
                    candidates = re.findall(r"(\d{4})", img_str)
                    for num in candidates:
                        val = int(num)
                        if 1000 <= val <= 8000 and not (5000 <= val < 6000) and not (2020 <= val <= 2030):
                            items.append(f"{RIOT_CDN}/item/{val}.png")
                
                # Boş veya hatalı linkleri önlemek için temizle
                clean_items = list(dict.fromkeys(items))[:7]

                # --- 5. VERİLER ---
                kda_text = kda_div.text.strip()
                result = "win" if "Victory" in row.text or "Zafer" in row.text else "lose"

                nums = re.findall(r"(\d+)", kda_text)
                score_val = 0.0
                if len(nums) >= 3:
                    k, d, a = int(nums[0]), int(nums[1]), int(nums[2])
                    score_val = (k + a) / d if d > 0 else 99.0
                    kda_display = "{:.2f}".format(score_val)
                else: 
                    score_val = 99.0
                    kda_display = "Perfect"
                
                grade = calculate_grade(score_val)

                # --- 6. CS / VISION SCORE ---
                raw_val = 0
                cs_div = row.find("div", class_="minions")
                if cs_div:
                    m = re.search(r"(\d+)", cs_div.text)
                    if m: raw_val = int(m.group(1))
                else:
                    m = re.search(r"(\d+)\s*CS", row.text, re.IGNORECASE)
                    if m: raw_val = int(m.group(1))

                display_stat = f"{raw_val} CS"
                if game_duration > 10 and raw_val < 70:
                    display_stat = f"GÖRÜŞ {raw_val} VS"
                
                lp_text = ""
                lp_match = re.search(r"([+-]\d+)\s*LP", row.text)
                if lp_match: lp_text = f"{lp_match.group(1)} LP"

                matches_info.append({
                    "champion": champ_key, "result": result, "kda": kda_text,
                    "img": final_champ_img, "items": clean_items, "grade": grade,
                    "cs": display_stat, "queue_mode": queue_mode,
                    "lp_change": lp_text, "kda_score": kda_display
                })
                if len(matches_info) >= 8: break
            except: continue
        
        # --- WIN RATE HESAPLAMA ---
        wins = sum(1 for m in matches_info if m['result'] == 'win')
        total_games = len(matches_info)
        win_rate = (wins / total_games * 100) if total_games > 0 else 0

        return {
            "summoner": summoner_name, "rank": rank_text, "icon": profile_icon, 
            "matches": matches_info, "win_rate": int(win_rate), "win_count": wins
        }

    except Exception as e:
        return {"error": str(e), "summoner": "Hata", "matches": []}

@app.route('/api/search', methods=['GET'])
def search_users():
    query = request.args.get('q', '').lower().strip()
    if not query: query = "abt"
    if query in HESAPLAR:
        return jsonify([scrape_summoner(url) for url in HESAPLAR[query]])
    return jsonify({"error": f"'{query}' grubu bulunamadı."})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
