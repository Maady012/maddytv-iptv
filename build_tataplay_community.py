import os, sys, json, urllib.request, re

DATA_URL = "https://api.ygxworld.workers.dev/fetcher.json"
EPG_BASE_URL = "https://raw.githubusercontent.com/Maady012/maddytv-iptv/main/epg.xml.gz"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

print("[*] Fetching 700+ Tata Play channel dataset...")
req = urllib.request.Request(DATA_URL, headers=headers)
try:
    with urllib.request.urlopen(req, timeout=15) as r:
        raw = json.loads(r.read().decode('utf-8'))
        channels = raw.get("data", {}).get("channels", [])
        print(f"[+] Loaded {len(channels)} Tata Play channels.")
except Exception as e:
    print(f"[-] Fetch error: {e}")
    sys.exit(1)

# Categorize channels by Language and by Genre
by_language = {}
by_genre = {}
all_valid = []

for c in channels:
    cid = c.get("id")
    name = c.get("name")
    manifest = c.get("manifest_url")
    logo = c.get("logo_url") or ""
    genre = c.get("primaryGenre") or (c.get("genres") and c.get("genres")[0]) or "General"
    languages = c.get("languages") or ["Other"]
    license_url = c.get("license_url") or ""

    if not manifest or not name:
        continue

    channel_obj = {
        "id": cid,
        "name": name,
        "manifest": manifest,
        "logo": logo,
        "genre": genre,
        "languages": languages,
        "license_url": license_url,
        "is_catchup": c.get("is_catchup_available", False),
        "is_drm": c.get("is_drm_protected", True)
    }

    all_valid.append(channel_obj)

    # Add to language buckets
    for lang in languages:
        by_language.setdefault(lang.capitalize(), []).append(channel_obj)

    # Add to genre buckets
    by_genre.setdefault(genre.capitalize(), []).append(channel_obj)

def format_m3u_entry(ch, group_name):
    # Formats for Kodi, TiviMate, OTT Navigator
    tvg_id = f"tataplay_{ch['id']}"
    catchup_str = ' catchup="append" catchup-days="8" catchup-source="&begin={utc}&end={utcend}"' if ch["is_catchup"] else ""
    
    lines = [
        f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-name="{ch["name"]}" tvg-logo="{ch["logo"]}" group-title="{group_name}"{catchup_str},{ch["name"]}'
    ]
    if ch["is_drm"]:
        lines.append('#KODIPROP:inputstream=inputstream.adaptive')
        lines.append('#KODIPROP:inputstream.adaptive.manifest_type=dash')
        lines.append('#KODIPROP:inputstream.adaptive.license_type=com.widevine.alpha')
        if ch["license_url"]:
            lines.append(f'#KODIPROP:inputstream.adaptive.license_key={ch["license_url"]}|Origin=https%3A%2F%2Fwatch.tataplay.com&Referer=https%3A%2F%2Fwatch.tataplay.com%2F')
    
    # Custom headers for DASH Akamai playback
    headers_prop = '|Origin="https://watch.tataplay.com"&Referer="https://watch.tataplay.com/"&User-Agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"'
    lines.append(f'{ch["manifest"]}{headers_prop}')
    return "\n".join(lines)

OUTPUT_DIR = "/data/data/com.termux/files/home/maddytv-iptv/playlists"
os.makedirs(f"{OUTPUT_DIR}/languages", exist_ok=True)
os.makedirs(f"{OUTPUT_DIR}/genres", exist_ok=True)

# 1. Master Tata Play M3U
master_m3u = [f'#EXTM3U x-tvg-url="{EPG_BASE_URL}"']
for ch in all_valid:
    master_m3u.append(format_m3u_entry(ch, ch["genre"]))

with open(f"{OUTPUT_DIR}/tataplay_all.m3u", "w", encoding="utf-8") as f:
    f.write("\n".join(master_m3u) + "\n")
print(f"[+] Master playlist created with {len(all_valid)} channels -> {OUTPUT_DIR}/tataplay_all.m3u")

# 2. Language-wise playlists
for lang, ch_list in by_language.items():
    clean_lang = re.sub(r'[^a-zA-Z0-9_]', '_', lang).lower()
    p_lines = [f'#EXTM3U x-tvg-url="{EPG_BASE_URL}"']
    for ch in ch_list:
        p_lines.append(format_m3u_entry(ch, f"Tata Play - {lang}"))
    out_file = f"{OUTPUT_DIR}/languages/tataplay_{clean_lang}.m3u"
    with open(out_file, "w", encoding="utf-8") as f:
        f.write("\n".join(p_lines) + "\n")
    print(f"  -> Language playlist: {lang} ({len(ch_list)} channels) -> {out_file}")

# 3. Genre-wise playlists
for gen, ch_list in by_genre.items():
    clean_gen = re.sub(r'[^a-zA-Z0-9_]', '_', gen).lower()
    p_lines = [f'#EXTM3U x-tvg-url="{EPG_BASE_URL}"']
    for ch in ch_list:
        p_lines.append(format_m3u_entry(ch, f"Tata Play - {gen}"))
    out_file = f"{OUTPUT_DIR}/genres/tataplay_{clean_gen}.m3u"
    with open(out_file, "w", encoding="utf-8") as f:
        f.write("\n".join(p_lines) + "\n")
    print(f"  -> Genre playlist: {gen} ({len(ch_list)} channels) -> {out_file}")

# Summary JSON index for easy dynamic routing
with open(f"{OUTPUT_DIR}/tataplay_index.json", "w", encoding="utf-8") as f:
    json.dump({
        "total_channels": len(all_valid),
        "languages": {l: len(c) for l, c in by_language.items()},
        "genres": {g: len(c) for g, c in by_genre.items()},
        "epg_url": EPG_BASE_URL
    }, f, indent=2)

print("\n[✓] All language-wise and genre-wise playlists successfully generated!")
