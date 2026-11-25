import os, sys, json, urllib.request, re

DATA_URL = "https://api.ygxworld.workers.dev/fetcher.json"
EPG_BASE_URL = "https://raw.githubusercontent.com/Maady012/maddytv-iptv/main/epg.xml.gz"

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
req = urllib.request.Request(DATA_URL, headers=headers)
raw = json.loads(urllib.request.urlopen(req, timeout=15).read().decode('utf-8'))
channels = raw.get("data", {}).get("channels", [])

VALID_LANGUAGES = {
    "Tamil", "Hindi", "Telugu", "Malayalam", "Kannada", "English",
    "Bengali", "Marathi", "Punjabi", "Gujarati", "Odia", "Assamese"
}

VALID_GENRES = {
    "Entertainment", "Movies", "Sports", "News", "Kids", "Music",
    "Knowledge", "Lifestyle", "Spiritual", "Drama"
}

OUTPUT_DIR = "/data/data/com.termux/files/home/maddytv-iptv/playlists"
os.makedirs(f"{OUTPUT_DIR}/languages", exist_ok=True)
os.makedirs(f"{OUTPUT_DIR}/genres", exist_ok=True)

lang_map = {l: [] for l in VALID_LANGUAGES}
genre_map = {g: [] for g in VALID_GENRES}
master_list = []

for c in channels:
    cid = c.get("id")
    name = c.get("name")
    manifest = c.get("manifest_url")
    logo = c.get("logo_url") or ""
    genre = c.get("primaryGenre") or "Entertainment"
    languages = c.get("languages") or []
    license_url = c.get("license_url") or ""

    if not manifest or not name:
        continue

    item = {
        "id": cid,
        "name": name,
        "manifest": manifest,
        "logo": logo,
        "genre": genre,
        "languages": languages,
        "license_url": license_url,
        "is_catchup": c.get("is_catchup_available", False)
    }
    master_list.append(item)

    # Normalize languages
    for l in languages:
        l_cap = l.strip().capitalize()
        if l_cap in lang_map:
            lang_map[l_cap].append(item)

    # Normalize genre
    g_cap = genre.strip().capitalize()
    if g_cap in genre_map:
        genre_map[g_cap].append(item)
    elif "News" in g_cap:
        genre_map["News"].append(item)
    elif "Movie" in g_cap:
        genre_map["Movies"].append(item)

def format_entry(ch, group):
    tvg_id = f"tataplay_{ch['id']}"
    catchup = ' catchup="append" catchup-days="8" catchup-source="&begin={utc}&end={utcend}"' if ch["is_catchup"] else ""
    lines = [
        f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-name="{ch["name"]}" tvg-logo="{ch["logo"]}" group-title="{group}"{catchup},{ch["name"]}',
        '#KODIPROP:inputstream=inputstream.adaptive',
        '#KODIPROP:inputstream.adaptive.manifest_type=dash',
        '#KODIPROP:inputstream.adaptive.license_type=com.widevine.alpha'
    ]
    if ch["license_url"]:
        lines.append(f'#KODIPROP:inputstream.adaptive.license_key={ch["license_url"]}|Origin=https%3A%2F%2Fwatch.tataplay.com&Referer=https%3A%2F%2Fwatch.tataplay.com%2F')
    
    headers_prop = '|Origin="https://watch.tataplay.com"&Referer="https://watch.tataplay.com/"&User-Agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"'
    lines.append(f'{ch["manifest"]}{headers_prop}')
    return "\n".join(lines)

# Write Master Tata Play M3U
with open(f"{OUTPUT_DIR}/tataplay_all.m3u", "w", encoding="utf-8") as f:
    f.write(f'#EXTM3U x-tvg-url="{EPG_BASE_URL}"\n')
    for ch in master_list:
        f.write(format_entry(ch, ch["genre"]) + "\n")

# Write Languages
for l, list_ch in lang_map.items():
    if not list_ch: continue
    filename = f"{OUTPUT_DIR}/languages/tataplay_{l.lower()}.m3u"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f'#EXTM3U x-tvg-url="{EPG_BASE_URL}"\n')
        for ch in list_ch:
            f.write(format_entry(ch, f"Tata Play {l}") + "\n")
    print(f"[✓] {l}: {len(list_ch)} channels -> {filename}")

# Write Genres
for g, list_ch in genre_map.items():
    if not list_ch: continue
    filename = f"{OUTPUT_DIR}/genres/tataplay_{g.lower()}.m3u"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f'#EXTM3U x-tvg-url="{EPG_BASE_URL}"\n')
        for ch in list_ch:
            f.write(format_entry(ch, f"Tata Play {g}") + "\n")
    print(f"[✓] {g}: {len(list_ch)} channels -> {filename}")

