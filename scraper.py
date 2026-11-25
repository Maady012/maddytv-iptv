#!/usr/bin/env python3
import urllib.request
import json
import re
import os
import sys

# Master channel definitions mapping directly to Maddy TV high quality streams
# Format:
# (id, name, logo, category, stream_type, identifier, server)
# stream_type:
#   'tu_cdn' -> calls https://tamilultra.nl/master.m3u8?c={identifier}&server={server} to get redirect URL
#   'direct_hls' -> identifier is the direct HLS .m3u8
#   'mpd_drm' -> identifier is tuple (mpd_url, key_id, key)

CHANNELS = [
    # --- ENTERTAINMENT & GENERAL ---
    {
        "id": "sun.tv.hd",
        "name": "Sun TV HD",
        "logo": "https://i0.wp.com/tamilultra.nl/wp-content/uploads/2021/05/Sun_TV_HD.png",
        "group": "Tamil Entertainment",
        "type": "tu_cdn",
        "code": "SUN_TV_HD",
        "server": 1
    },
    {
        "id": "star.vijay.hd",
        "name": "Star Vijay HD",
        "logo": "https://i0.wp.com/tamilultra.nl/wp-content/uploads/2021/05/Star_Vijay_HD.png",
        "group": "Tamil Entertainment",
        "type": "tu_cdn",
        "code": "STAR_VIJAY",
        "server": 1
    },
    {
        "id": "zee.tamil.hd",
        "name": "Zee Tamil HD",
        "logo": "https://i0.wp.com/tamilultra.nl/wp-content/uploads/2021/05/Zee_Tamil_HD.png",
        "group": "Tamil Entertainment",
        "type": "tu_cdn",
        "code": "ZEE_TAMIL_HD",
        "server": 1
    },
    {
        "id": "colors.tamil.hd",
        "name": "Colors Tamil HD",
        "logo": "https://i0.wp.com/tamilultra.nl/wp-content/uploads/2021/05/Colors_Tamil_HD.png",
        "group": "Tamil Entertainment",
        "type": "tu_cdn",
        "code": "COLORS_TAMIL_HD",
        "server": 1
    },
    {
        "id": "vijay.takkar",
        "name": "Vijay Takkar",
        "logo": "https://i0.wp.com/tamilultra.nl/wp-content/uploads/2021/05/Vijay_Takkar.png",
        "group": "Tamil Entertainment",
        "type": "tu_cdn",
        "code": "VIJAY_TAKKAR",
        "server": 3
    },
    {
        "id": "shakthi.tv",
        "name": "Shakthi TV",
        "logo": "https://i0.wp.com/tamilultra.nl/wp-content/uploads/2024/05/Sakthi_TV.png",
        "group": "Tamil Entertainment",
        "type": "tu_cdn",
        "code": "SHAKTHI_TV",
        "server": 2
    },
    {
        "id": "vasantham.tv",
        "name": "Vasantham TV",
        "logo": "https://i0.wp.com/tamilultra.nl/wp-content/uploads/2023/06/Vasantham_TV.png",
        "group": "Tamil Entertainment",
        "type": "tu_cdn",
        "code": "VASANTHAM_TV",
        "server": 2
    },
    {
        "id": "biggboss.tamil",
        "name": "Bigg Boss Tamil 24/7 Live",
        "logo": "https://i0.wp.com/tamilultra.nl/wp-content/uploads/2026/09/bbtamils10live.png",
        "group": "Tamil Entertainment",
        "type": "tu_cdn",
        "code": "BBTAMIL",
        "server": 1
    },

    # --- MOVIES ---
    {
        "id": "ktv.hd",
        "name": "KTV HD",
        "logo": "https://i0.wp.com/tamilultra.nl/wp-content/uploads/2021/05/KTV_HD.png",
        "group": "Tamil Movies",
        "type": "tu_cdn",
        "code": "KTV_HD",
        "server": 1
    },
    {
        "id": "vijay.super",
        "name": "Vijay Super",
        "logo": "https://i0.wp.com/tamilultra.nl/wp-content/uploads/2021/05/Vijay_Super.png",
        "group": "Tamil Movies",
        "type": "tu_cdn",
        "code": "VIJAY_SUPER",
        "server": 1
    },
    {
        "id": "zee.thirai.hd",
        "name": "Zee Thirai HD",
        "logo": "https://i0.wp.com/tamilultra.nl/wp-content/uploads/2021/05/Zee_Thirai.png",
        "group": "Tamil Movies",
        "type": "tu_cdn",
        "code": "ZEE_THIRAI_HD",
        "server": 1
    },
    {
        "id": "maddytv.movies.hd",
        "name": "Maddy TV Movies 4K",
        "logo": "https://i0.wp.com/tamilultra.nl/wp-content/uploads/2023/07/TAMILULTRA_4K.png",
        "group": "Tamil Movies",
        "type": "tu_cdn",
        "code": "TAMILULTRA_MOVIES",
        "server": 1
    },

    # --- MUSIC ---
    {
        "id": "sun.music.hd",
        "name": "Sun Music HD",
        "logo": "https://i0.wp.com/tamilultra.nl/wp-content/uploads/2021/05/Sun_Music_HD.png",
        "group": "Tamil Music",
        "type": "tu_cdn",
        "code": "SUN_MUSIC_HD",
        "server": 1
    },
    {
        "id": "isaiaruvi",
        "name": "Isaiaruvi",
        "logo": "https://i0.wp.com/tamilultra.nl/wp-content/uploads/2021/05/Isaiaruvi.png",
        "group": "Tamil Music",
        "type": "direct_hls",
        "url": "https://yuppmedtaorire.akamaized.net/v1/master/a0d007312bfd99c47f76b77ae26b1ccdaae76cb1/isaiaruvi_nim_https/140622/isaiaruvi/playlist.m3u8?e=1"
    },
    {
        "id": "murasu.tv",
        "name": "Murasu TV",
        "logo": "https://i0.wp.com/tamilultra.nl/wp-content/uploads/2024/10/Murasu_Tv.png",
        "group": "Tamil Music",
        "type": "direct_hls",
        "url": "https://segment.yuppcdn.net/050522/murasu/playlist.m3u8"
    },

    # --- SPORTS ---
    {
        "id": "star.sports.1.tamil",
        "name": "Star Sports 1 Tamil HD",
        "logo": "https://i0.wp.com/tamilultra.nl/wp-content/uploads/2021/07/Star_Sports_Tamil.png",
        "group": "Sports",
        "type": "tu_cdn",
        "code": "SPTAMIL",
        "server": 1
    },
    {
        "id": "sony.ten4.tamil",
        "name": "Sony Ten 4 Tamil HD",
        "logo": "https://i0.wp.com/tamilultra.nl/wp-content/uploads/2023/04/Ten4_Tamil_HD_FINAL.png",
        "group": "Sports",
        "type": "tu_cdn",
        "code": "TEN_4_HD",
        "server": 1
    },
    {
        "id": "willow.hd",
        "name": "Willow Cricket HD",
        "logo": "https://i0.wp.com/tamilultra.nl/wp-content/uploads/2023/07/WILLOW_HD.png",
        "group": "Sports",
        "type": "tu_cdn",
        "code": "WILLOW_HD",
        "server": 1
    },
    {
        "id": "sky.cricket",
        "name": "Sky Sports Cricket HD",
        "logo": "https://i0.wp.com/tamilultra.nl/wp-content/uploads/2023/07/SKY_SPORTS_CRICKET.png",
        "group": "Sports",
        "type": "tu_cdn",
        "code": "SKY_CRICKET",
        "server": 1
    },
    {
        "id": "astro.cricket",
        "name": "Astro Cricket HD",
        "logo": "https://i0.wp.com/tamilultra.nl/wp-content/uploads/2023/07/ASTRO_CRICKET.png",
        "group": "Sports",
        "type": "tu_cdn",
        "code": "ASTRO_CRICKET",
        "server": 1
    },
    {
        "id": "sky.f1.hd",
        "name": "Sky Sports F1 HD",
        "logo": "https://i0.wp.com/tamilultra.nl/wp-content/uploads/2026/04/SKY_SPORTS_F1.png",
        "group": "Sports",
        "type": "mpd_drm",
        "mpd": "https://otte.cache.aiv-cdn.net/bom-nitro/live/clients/dash/enc/duqbirmk0d/out/v1/40f53c7cbc95498db3afd081c377d776/cenc.mpd",
        "key_id": "609d795905904705028ef54653019af7",
        "key": "2c791eb611e57a7d7f203022bc1b9ba3"
    },

    # --- INFOTAINMENT & KIDS ---
    {
        "id": "history18.tamil",
        "name": "History TV18 HD",
        "logo": "https://dtil.tmsimg.com/assets/s143133_ld_h15_aa.png?lock=720x540",
        "group": "Tamil Infotainment",
        "type": "direct_hls",
        "url": "https://amg01448-amg01448c16-samsung-in-3495.playouts.now.amagi.tv/playlist/amg01448-samsungindia-historychannelenglish-samsungin/playlist.m3u8"
    },
    {
        "id": "natgeo.tamil",
        "name": "National Geographic Tamil",
        "logo": "https://i0.wp.com/tamilultra.nl/wp-content/uploads/2023/05/National_Geo_Tamil.png",
        "group": "Tamil Infotainment",
        "type": "tu_cdn",
        "code": "NAT_GEO_TAMIL",
        "server": 1
    },
    {
        "id": "natgeo.wild.tamil",
        "name": "Nat Geo Wild HD Tamil",
        "logo": "https://i0.wp.com/tamilultra.nl/wp-content/uploads/2023/04/Nat_Geo_Tamil.png",
        "group": "Tamil Infotainment",
        "type": "tu_cdn",
        "code": "NAT_GEO_WILD_TAMIL",
        "server": 1
    },
    {
        "id": "sony.bbc.earth.tamil",
        "name": "Sony BBC Earth Tamil",
        "logo": "https://i0.wp.com/tamilultra.nl/wp-content/uploads/2021/05/Sony_BBC_Earth_Tamil.png",
        "group": "Tamil Infotainment",
        "type": "tu_cdn",
        "code": "SONY_BBC_TAMIL",
        "server": 1
    },
    {
        "id": "disney.tamil",
        "name": "Disney Channel Tamil",
        "logo": "https://i0.wp.com/tamilultra.nl/wp-content/uploads/2023/06/Disney_Tamil.png",
        "group": "Kids",
        "type": "tu_cdn",
        "code": "DISNEY_TAMIL",
        "server": 1
    },
    {
        "id": "wow.kidz.tamil",
        "name": "Wow Kidz Tamil",
        "logo": "https://i0.wp.com/tamilultra.nl/wp-content/uploads/2026/04/Wow_kids_tamil.png",
        "group": "Kids",
        "type": "direct_hls",
        "url": "https://yuppparoriglin.akamaized.net//181224//smil:wowkidztam.smil//playlist.m3u8?hdnts=st=1735898689~exp=1835898688~acl=*~hmac=f5fe24724fe05481e3841f9eb5ab8efdee0a3dd83645ae9dcf45703f525bab7b&id=25734&type=mp4"
    }
]

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

def resolve_tu_token(channel_code, server=1):
    url = f"https://tamilultra.nl/master.m3u8?c={channel_code}&server={server}"
    opener = urllib.request.build_opener(NoRedirect)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': f'https://tamilultra.nl/player.php?master.m3u8?c={channel_code}&server={server}',
        'Accept': '*/*'
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        resp = opener.open(req, timeout=10)
        return resp.geturl()
    except urllib.error.HTTPError as e:
        if e.code in [301, 302, 303, 307, 308]:
            loc = e.headers.get('Location')
            return loc
        print(f"[-] HTTP error resolving {channel_code}: {e.code}")
    except Exception as ex:
        print(f"[-] Exception resolving {channel_code}: {ex}")
    return None

def verify_stream(url, user_agent=None, referer=None):
    headers = {'User-Agent': user_agent or 'Mozilla/5.0'}
    if referer:
        headers['Referer'] = referer
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=8) as r:
            return r.getcode() == 200
    except:
        return False

def build_playlist():
    print(f"[*] Starting Maddy TV playlist generation ({len(CHANNELS)} channels)...")
    lines = ["#EXTM3U x-tvg-url=\"\""]
    
    success_count = 0
    for ch in CHANNELS:
        ch_id = ch["id"]
        name = ch["name"]
        logo = ch["logo"]
        group = ch["group"]
        stype = ch["type"]

        stream_url = None

        if stype == "tu_cdn":
            code = ch["code"]
            server = ch.get("server", 1)
            print(f" -> Resolving token for {name} ({code})...", end=" ")
            target_url = resolve_tu_token(code, server)
            if target_url:
                stream_url = target_url
                print(f"OK: {stream_url[:60]}...")
            else:
                print("FAILED")

        elif stype == "direct_hls":
            stream_url = ch["url"]
            print(f" -> Direct HLS stream for {name} OK")

        elif stype == "mpd_drm":
            lines.append(f'#EXTINF:-1 tvg-id="{ch_id}" tvg-name="{name}" tvg-logo="{logo}" group-title="{group}",{name}')
            lines.append(f'#KODIPROP:inputstream=inputstream.adaptive')
            lines.append(f'#KODIPROP:inputstream.adaptive.manifest_type=mpd')
            lines.append(f'#KODIPROP:inputstream.adaptive.license_type=clearkey')
            lines.append(f'#KODIPROP:inputstream.adaptive.license_key={ch["key_id"]}:{ch["key"]}')
            lines.append(ch["mpd"])
            success_count += 1
            print(f" -> DRM ClearKey stream for {name} OK")
            continue

        if stream_url:
            lines.append(f'#EXTINF:-1 tvg-id="{ch_id}" tvg-name="{name}" tvg-logo="{logo}" group-title="{group}",{name}')
            lines.append(stream_url)
            success_count += 1

    playlist_content = "\n".join(lines) + "\n"
    
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "maddytv.m3u")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(playlist_content)
    
    print(f"\n[+] Successfully generated playlist at {out_path} ({success_count}/{len(CHANNELS)} channels active).")

if __name__ == "__main__":
    build_playlist()
