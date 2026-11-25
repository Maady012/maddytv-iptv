import xml.etree.ElementTree as ET
import datetime
import re
import gzip
import shutil

print("1. Parsing enriched EPG XML...")
tree = ET.parse("/sdcard/Download/maddy_epg.xml")
root = tree.getroot()

existing_ch_ids = set()
for ch in root.findall("channel"):
    existing_ch_ids.add(ch.get("id"))

print(f"Existing channel IDs in EPG: {len(existing_ch_ids)}")

# Scan both maddytv.m3u and maddytvboom.m3u for every channel
all_channels = {}

for m3u in ["/data/data/com.termux/files/home/maddytv-iptv/maddytv.m3u", "/data/data/com.termux/files/home/maddytvboom/maddytvboom.m3u"]:
    with open(m3u, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("#EXTINF:"):
                name = line.strip().split(",")[-1].strip()
                m = re.search(r'tvg-id="([^"]*)"', line)
                tid = m.group(1) if m else name
                g = re.search(r'group-title="([^"]*)"', line)
                grp = g.group(1) if g else "General"
                all_channels[tid] = (name, grp)

print(f"Total unique channels across both playlists: {len(all_channels)}")

now = datetime.datetime.now(datetime.timezone.utc)
today = now.date()

# Genre-based schedules for any channel without broadcast satellite EPG
genre_templates = {
    "music": [
        ("000000", "060000", "Midnight Melodies", "Non-stop relaxing melodies and vintage classic hits."),
        ("060000", "090000", "Kaalai Thendral", "Fresh morning songs, spiritual chants, and evergreen melodies."),
        ("090000", "120000", "Super Hits Non-Stop", "Back-to-back Kollywood chartbusters and new releases."),
        ("120000", "150000", "Ragalai 100", "Peppy youth anthems, high-energy dance hits, and trending songs."),
        ("150000", "180000", "Trendsetters Special", "Exclusive tracklists featuring top music directors."),
        ("180000", "210000", "Prime Time Beats", "Most celebrated blockbusters and crowd favourites."),
        ("210000", "240000", "Evergreen Night", "Sweet nostalgic classics and soothing melodies.")
    ],
    "news": [
        ("000000", "060000", "Night Headlines & World Round-Up", "Overnight news updates, national and global headlines."),
        ("060000", "080000", "Morning Express News", "Headlines, paper review, weather, and daily horoscope."),
        ("080000", "100000", "Special Investigation & Debate", "Detailed coverage of trending state and national stories."),
        ("100000", "130000", "Midday News Bulletin", "Live midday breaking updates, business and local affairs."),
        ("130000", "150000", "Special Ground Report", "In-depth investigative reports and political analysis."),
        ("150000", "180000", "Speed News 100", "100 fast-paced headlines from Tamil Nadu, India, and World."),
        ("180000", "200000", "Prime Time Headlines", "Comprehensive evening news bulletin."),
        ("200000", "220000", "Prime Debate Live", "Engaging panel discussion on burning political and social issues."),
        ("220000", "240000", "Night Desk Round-Up", "Wrap-up of all major events that shaped the day.")
    ],
    "kids": [
        ("000000", "060000", "Bedtime Stories & Rhymes", "Sweet fairy tales, moral stories, and lullabies."),
        ("060000", "090000", "Fun Learning Morning", "Engaging alphabet, colours, numbers, and preschool fun."),
        ("090000", "120000", "Action Animated Adventures", "High-energy animation, hero missions, and comedy."),
        ("120000", "150000", "Comedy Cartoon Fiesta", "Hilarious cartoons and slapstick comedy for children."),
        ("150000", "180000", "Adventure Heroes Club", "Exciting magical worlds, robotics, and mysteries."),
        ("180000", "210000", "Prime Time Kidz Power", "Top trending cartoon episodes and games."),
        ("210000", "240000", "Folk Tales & Moral Lessons", "Classic Panchatantra and Akbar Birbal tales.")
    ],
    "movies": [
        ("000000", "060000", "Midnight Movie Marathon", "Selected blockbuster films and thriller stories."),
        ("060000", "090000", "Comedy Kalanjiayam", "Selected hilarious comedy scenes from top movies."),
        ("090000", "120000", "Morning Matinee Blockbuster", "High-rated family drama and action feature film."),
        ("120000", "150000", "Noon Special Feature Film", "Special selection of classic and popular hit movies."),
        ("150000", "180000", "Action Matinee Film", "Thrillers, action entertainers, and commercial hits."),
        ("180000", "210000", "Prime Time Mega Premiere", "Mega star blockbuster with complete family entertainment."),
        ("210000", "240000", "Night Suspense Special Film", "Gripping crime, thriller, and action cinema.")
    ],
    "devotional": [
        ("000000", "060000", "Spiritual Chants & Mantras", "Peaceful sacred mantras and Vedic chants."),
        ("060000", "090000", "Morning Suprabhatam & Darshan", "Live temple darshan, spiritual discourses, and bhajans."),
        ("090000", "120000", "Bhakti Songs & Stotras", "Devotional songs praising regional deities."),
        ("120000", "150000", "Temple History & Traditions", "Documentaries on sacred ancient shrines and architecture."),
        ("150000", "180000", "Spiritual Pravachanam", "Inspiring moral discourses by revered spiritual leaders."),
        ("180000", "210000", "Evening Deeparadhana", "Auspicious evening prayers, hymns, and aarti ceremonies."),
        ("210000", "240000", "Meditation & Peace", "Tranquil ambient chants for peaceful rest.")
    ],
    "general": [
        ("000000", "060000", "Night Variety Hour", "Relaxing variety programs, music, and highlights."),
        ("060000", "090000", "Vanakkam Tamil Nadu", "Morning motivation, yoga, healthy living, and daily news."),
        ("090000", "120000", "Entertainment Express", "Cinema news, celebrity interviews, and lifestyle features."),
        ("120000", "150000", "Afternoon Special Show", "Cookery shows, women's special, and family talk shows."),
        ("150000", "180000", "Comedy & Game Show", "Celebrity games, family trivia, and comedy highlights."),
        ("180000", "210000", "Prime Time Drama & Series", "Engaging drama series and cultural celebrations."),
        ("210000", "240000", "Cinema Talk & Late Night Special", "Behind-the-scenes movie updates and celebrity chats.")
    ]
}

# Determine template by channel name or group
def get_template(name, grp):
    n = name.lower()
    g = grp.lower()
    if any(x in n or x in g for x in ["music", "isai", "paadal", "gana", "rhythm"]):
        return genre_templates["music"]
    if any(x in n or x in g for x in ["news", "seithigal", "murasu", "polimer", "puthiya", "samachar"]):
        return genre_templates["news"]
    if any(x in n or x in g for x in ["kids", "chutti", "cartoon", "pogo", "hungama", "animation", "balam"]):
        return genre_templates["kids"]
    if any(x in n or x in g for x in ["movie", "thirai", "cinema", "talkies", "film", "gold"]):
        return genre_templates["movies"]
    if any(x in n or x in g for x in ["bakthi", "bhakti", "divya", "om", "aaradhana", "devotional", "god", "temple"]):
        return genre_templates["devotional"]
    return genre_templates["general"]

added_channels = 0
added_programmes = 0

for tid, (name, grp) in all_channels.items():
    if tid not in existing_ch_ids:
        # Add channel definition
        ch_el = ET.SubElement(root, "channel", id=tid)
        dn = ET.SubElement(ch_el, "display-name")
        dn.text = name
        existing_ch_ids.add(tid)
        added_channels += 1
        
        # Add 7-day schedule
        template = get_template(name, grp)
        for d in range(-1, 8):
            cdate = today + datetime.timedelta(days=d)
            date_str = cdate.strftime("%Y%m%d")
            next_date_str = (cdate + datetime.timedelta(days=1)).strftime("%Y%m%d")
            
            for start_t, end_t, title, desc in template:
                if end_t == "240000":
                    p_start = f"{date_str}{start_t} +0530"
                    p_stop = f"{next_date_str}000000 +0530"
                else:
                    p_start = f"{date_str}{start_t} +0530"
                    p_stop = f"{date_str}{end_t} +0530"
                
                prog = ET.SubElement(root, "programme", start=p_start, stop=p_stop, channel=tid)
                t_el = ET.SubElement(prog, "title", lang="ta")
                t_el.text = f"{name}: {title}"
                d_el = ET.SubElement(prog, "desc", lang="en")
                d_el.text = desc
                added_programmes += 1

print(f"Added {added_channels} newly defined channels with {added_programmes} programmes.")
print(f"Grand total channels in EPG: {len(root.findall('channel'))}")
print(f"Grand total programmes in EPG: {len(root.findall('programme'))}")

out_path = "/sdcard/Download/maddy_epg.xml"
gz_path = "/sdcard/Download/maddy_epg.xml.gz"

tree = ET.ElementTree(root)
ET.indent(tree, space="  ", level=0)
print(f"Writing to {out_path} and {gz_path}...")
tree.write(out_path, encoding="utf-8", xml_declaration=True)

with open(out_path, "rb") as f_in, gzip.open(gz_path, "wb") as f_out:
    f_out.writelines(f_in)

# Sync to repo
shutil.copyfile(gz_path, "/data/data/com.termux/files/home/maddytv-iptv/epg.xml.gz")
shutil.copyfile(out_path, "/data/data/com.termux/files/home/maddytv-iptv/epg.xml")
print("100% COMPLETE: All channels across all playlists now have full 7-day EPG data!")
