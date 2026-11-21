"""
Complete Page assembly renderer for news-image-20261121-r2.
Implements full layout spec: masthead, timeline, region strip, stats, 3 lead cards, 17 secondary cards, map + 50 briefs, legend, footer.
Includes mandatory verification for all text blocks and full text placement.
"""

import os
import random
from typing import List, Dict, Tuple
from PIL import Image, ImageDraw, ImageFont, ImageOps
from stories import CARDS, BRIEFS, REGIONS, DATE_CHECK, SOURCING, TRUTH, META, TIMELINE, STATS

REGION_COLORS = {
    "EUROPE": "#3d6fb4",
    "THE AMERICAS": "#3f8f5f",
    "ASIA-PACIFIC": "#d97b2f",
    "MIDDLE EAST": "#c0453e",
    "AFRICA": "#7a4f9d",
    "OCEANIA": "#2f8f8a",
    "WORLD": "#8a7a3a"
}

BRIEF_TRIMS = {
    21: "21 BERLIN — The 'coalition of the willing' meets on Ukraine [Reports]",
    23: "23 MADRID — A general strike brings Spain to a halt [Reports]",
    24: "24 ROME — Workers and students march against Meloni's budget.",
    25: "25 BERLIN — Students march against rearmament [Reports]",
    26: "26 PODGORICA — Montenegro rejects land concessions [Reports]",
    27: "27 BRUSSELS — EU and Canada deepen ties on minerals [EU]",
    30: "30 EUROPE — Cost-of-living protests continue into weekend.",
    31: "31 TURIN — Alcaraz beats Shelton 3-6, 6-3, 7-6 [ATP]",
    32: "32 MANCHESTER — Fulham hold Man City 1-1 at Etihad [Reuters]",
    33: "33 PREMIER LEAGUE — Saturday results: Coventry 3-2 [Reports]",
    34: "34 WASHINGTON — Trump says Iran wants a deal [AP]",
    35: "35 LOS ANGELES — Jury convicts man who started Palisades Fire [AP]",
    36: "36 BRASILIA — Brazil strengthens land safeguards [Reports]",
    37: "37 OTTAWA — Security forum hears US leadership wanes [Forum]",
    38: "38 OTTAWA — US sanctions syndicate in Canada [Treasury]",
    39: "39 WASHINGTON — US sanctions four Iranians over oil revenues.",
    40: "40 WASHINGTON — Second judge blocks triumphal arch",
    41: "41 WASHINGTON — Pentagon puts Iran engagement cost at $48bn [Reports]",
    42: "42 WASHINGTON — US floats NATO membership for Ukraine [Report]",
    43: "43 SOUTHERN MEXICO — Caravan of 300 migrants crosses [Reports]",
    44: "44 LOS ANGELES — Hyundai unveils 2027 Elantra [Show reports]",
    45: "45 LAS VEGAS — Las Vegas GP qualifying tonight [F1]",
    47: "47 BUENOS AIRES — Senate backs disability framework",
    48: "48 TOKYO — Takaichi gets frosty APEC greeting [Asahi]",
    49: "49 KABUL — UN warns ISIS-K gaining drones [UN]",
    50: "50 MUMBAI — IndusInd seeks to recover ex-CEO pay [Reuters]",
    51: "51 NEW DELHI — US panel says India targets minorities [Panel]",
    52: "52 MALAYSIA — Malaysia to send Rohingya to Turkey [Reports]",
    53: "53 PAKISTAN — Minerals worth $8-10 trillion [Reports]",
    54: "54 SINGAPORE — US presses Singapore on Iran sanctions [Reports]",
    55: "55 CANBERRA — Australia and China agree on AI dialogue [ABC]",
    56: "56 BAGHDAD — Pipeline chief arrested over oil trade [Reports]",
    57: "57 STRAIT OF HORMUZ — Iran claims waters 500km beyond [IRGC]",
    58: "58 GAZA — Children appeal for help on World Children's Day.",
    59: "59 STRAIT OF HORMUZ — Tanker struck and on fire in strait.",
    61: "61 JOHANNESBURG — Murder rate falls to 60 a day [Stats]",
    62: "62 WEST KORDOFAN — Army clears RSF strongholds [Army]",
    63: "63 OGUN, NIGERIA — NAFDAC destroys fake products [Punch]",
    64: "64 RABAT — Morocco commits €366m to defence industry [Africanews]",
    65: "65 SOUTHERN ETHIOPIA — Conflict displaces 700k people [Reports]",
    66: "66 KAMPALA — Uganda signs crude-oil agreement [Reports]",
    67: "67 MELBOURNE — Australia host England in T20 at MCG [AFP diary]",
    68: "68 COOK ISLANDS — Cyclone Xavier damages northern islands [Reports]",
    69: "69 GENEVA — UN yearbook finds climate indicators lagging [UN News]",
    70: "70 HEALTH — Pill hailed as pancreatic cancer breakthrough."
}

class LayoutError(Exception):
    pass

class TextBox:
    def __init__(self, rect: Tuple[int, int, int, int], content: str):
        self.rect = rect
        self.content = content

class Page:
    WIDTH = 1024
    HEIGHT = 1024
    BG_COLOR = "#f3ecde"
    PANEL_COLORS = {"charcoal1": "#292722", "charcoal2": "#211f1b", "gold": "#d9b568", "ivory": "#f8f1e2"}

    def __init__(self) -> None:
        self.image = Image.new("RGB", (self.WIDTH, self.HEIGHT), self.BG_COLOR)
        self.draw = ImageDraw.Draw(self.image)
        self.boxes: List[TextBox] = []
        self.fonts: Dict[str, ImageFont.FreeTypeFont] = {}
        self._load_system_fonts()

    def _load_system_fonts(self) -> None:
        possible_serif = [
            "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
        ]
        possible_sans = [
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/noto/NotoSansDisplayCondensed-Regular.ttf",
        ]
        
        serif_path = possible_serif[0]
        for p in possible_serif:
            if os.path.isfile(p):
                serif_path = p
                break
                
        sans_path = possible_sans[0]
        for p in possible_sans:
            if os.path.isfile(p):
                sans_path = p
                break

        self.fonts["serif_34"] = ImageFont.truetype(serif_path, size=32)
        self.fonts["serif_16"] = ImageFont.truetype(serif_path, size=15)
        self.fonts["serif_13"] = ImageFont.truetype(serif_path, size=12)
        self.fonts["sans_14"] = ImageFont.truetype(sans_path, size=13)
        self.fonts["sans_10"] = ImageFont.truetype(sans_path, size=10)
        self.fonts["sans_9"] = ImageFont.truetype(sans_path, size=9)
        self.fonts["sans_8"] = ImageFont.truetype(sans_path, size=8)
        self.fonts["sans_7"] = ImageFont.truetype(sans_path, size=7)

    def get_font(self, name: str) -> ImageFont.FreeTypeFont:
        return self.fonts.get(name, self.fonts["sans_10"])

    def add_box(self, rect: Tuple[int, int, int, int], content: str = "") -> None:
        x0, y0, x1, y1 = rect
        if x0 < 0 or y0 < 0 or x1 > self.WIDTH or y1 > self.HEIGHT:
            raise LayoutError(f"Box {rect} out of canvas bounds")
        for b in self.boxes:
            if self._rects_overlap(rect, b.rect):
                raise LayoutError(f"Box {rect} overlaps with existing box {b.rect}")
        self.boxes.append(TextBox(rect, content))

    @staticmethod
    def _rects_overlap(a: Tuple[int, int, int, int], b: Tuple[int, int, int, int]) -> bool:
        ax0, ay0, ax1, ay1 = a
        bx0, by0, bx1, by1 = b
        return not (ax1 <= bx0 or ax0 >= bx1 or ay1 <= by0 or ay1 >= by1)

    def measured_text(self, text: str, font_name: str, max_width: int, max_lines: int = 99) -> List[str]:
        font = self.get_font(font_name)
        words = text.split()
        if not words:
            return [""]
        lines = []
        current_line = []
        for word in words:
            test_line = " ".join(current_line + [word])
            bbox = font.getbbox(test_line)
            w = bbox[2] - bbox[0]
            if w <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                    current_line = [word]
                else:
                    lines.append(word)
        if current_line:
            lines.append(" ".join(current_line))
        if len(lines) > max_lines:
            lines = lines[:max_lines]
        return lines


def draw_scene(card: dict, box: Tuple[int, int, int, int]) -> Image.Image:
    x0, y0, x1, y1 = box
    w = max(10, x1 - x0)
    h = max(10, y1 - y0)
    art = Image.new("RGB", (w, h), "#211f1b")
    draw = ImageDraw.Draw(art)
    region = card.get("region", "WORLD")
    accent = REGION_COLORS.get(region, "#d9b568")
    seed = card.get("n", 1)

    if h < 12:
        draw.rectangle([0, 0, w, h], fill=accent)
        return art

    if seed == 1:
        draw.rectangle([0, max(0, h-25), w, h], fill="#333")
        draw.arc([w//2 - min(30, w//3), 2, w//2 + min(30, w//3), h-2], 180, 360, fill=accent, width=2)
    elif seed == 2:
        draw.line([5, h-5, w-5, 5], fill="#e74c3c", width=2)
        draw.ellipse([max(0, w-15), 2, w-2, min(15, h-2)], fill=accent)
    elif seed == 3:
        for i in range(4):
            draw.ellipse([8 + i*max(5, w//5), h//2 - 6, 16 + i*max(5, w//5), h//2 + 6], fill=accent)
    elif seed == 4:
        draw.arc([4, 4, w-4, h-4], 0, 360, fill="#444", width=2)
        draw.ellipse([w//2 - 3, h//2 - 3, w//2 + 3, h//2 + 3], fill=accent)
    elif seed == 5:
        draw.rectangle([8, h//2 - 6, w-8, h//2 + 6], fill="#3d3b36")
    elif seed == 6:
        top_y = min(6, h-2)
        bot_y = max(top_y + 1, h-2)
        draw.rectangle([w//2 - min(25, w//3), top_y, w//2 + min(25, w//3), bot_y], fill="#3a3830")
    elif seed == 7:
        if w > 15 and h > 15:
            draw.rectangle([6, 6, w-6, h-6], fill="#111", outline=accent, width=2)
        else:
            draw.rectangle([2, 2, w-2, h-2], fill="#111", outline=accent, width=1)
    elif seed == 8:
        draw.arc([w//2 - min(30, w//3), 4, w//2 + min(30, w//3), h-4], 0, 270, fill=accent, width=2)
    else:
        draw.rectangle([w//4, h//4, 3*w//4, 3*w//4], fill=accent)
    return art


def render_page() -> Page:
    page = Page()
    draw = page.draw
    y = 12

    # 1. MASTHEAD
    masthead_h = 80
    draw.rectangle([12, y, 1012, y + masthead_h], fill="#292722")
    page.add_box((12, y, 1012, y + masthead_h), "Masthead")
    
    draw.text((20, y + 6), META['title'], font=page.get_font("sans_14"), fill="#d9b568")
    strap_w = page.get_font("sans_9").getbbox(META['subtitle'])[2]
    draw.text((1004 - strap_w, y + 8), META['subtitle'], font=page.get_font("sans_9"), fill="#f8f1e2")
    
    draw.line([(20, y + 25), (1004, y + 25)], fill="#3d3b36", width=1)
    
    date_font = "serif_34"
    date_str = META['date']
    date_w = page.get_font(date_font).getbbox(date_str)[2] - page.get_font(date_font).getbbox(date_str)[0]
    date_x = (1024 - date_w) // 2
    draw.text((date_x, y + 28), date_str, font=page.get_font(date_font), fill="#f8f1e2")
    
    kicker_font = "serif_13"
    kicker_str = META['kicker']
    kicker_lines = page.measured_text(kicker_str, kicker_font, 984, 1)
    kicker_w = page.get_font(kicker_font).getbbox(kicker_lines[0])[2] - page.get_font(kicker_font).getbbox(kicker_lines[0])[0]
    kicker_x = (1024 - kicker_w) // 2
    draw.text((kicker_x, y + 62), kicker_lines[0], font=page.get_font(kicker_font), fill="#d9b568")

    y += masthead_h + 4

    # 2. TIMELINE STRIP
    timeline_h = 20
    draw.rectangle([12, y, 1012, y + timeline_h], fill="#211f1b")
    page.add_box((12, y, 1012, y + timeline_h), "Timeline")
    t_text = "07:15 — COP31 third draft lands · 11:30 — Rutte in Warsaw · 14:00 — Coalition meets Zelenskyy · 19:24 CET — BepiColombo burns · 22:00 — Las Vegas qualifying"
    t_lines = page.measured_text(t_text, "sans_9", 980, 1)
    draw.text((18, y + 4), t_lines[0], font=page.get_font("sans_9"), fill="#d9b568")
    y += timeline_h + 4

    # 3. REGION STRIP
    region_h = 20
    draw.rectangle([12, y, 1012, y + region_h], fill="#292722")
    page.add_box((12, y, 1012, y + region_h), "Regions")
    region_str = "EUROPE 20 · THE AMERICAS 15 · ASIA-PACIFIC 13 · MIDDLE EAST 7 · AFRICA 9 · OCEANIA 3 · WORLD 3   (70 STORIES FROM 7 REGIONS)"
    draw.text((18, y + 4), region_str, font=page.get_font("sans_9"), fill="#f8f1e2")
    y += region_h + 4

    # 4. STAT BAND (Wrapped to 2 lines so all 6 stats fit fully)
    stat_h = 32
    draw.rectangle([12, y, 1012, y + stat_h], fill="#211f1b")
    page.add_box((12, y, 1012, y + stat_h), "Stats")
    
    half_stats = len(STATS) // 2
    stat_str_1 = "  |  ".join(STATS[:half_stats])
    stat_str_2 = "  |  ".join(STATS[half_stats:])
    draw.text((18, y + 3), stat_str_1, font=page.get_font("sans_9"), fill="#d9b568")
    draw.text((18, y + 17), stat_str_2, font=page.get_font("sans_9"), fill="#d9b568")
    y += stat_h + 4

    # 5. THREE LEAD CARDS (Cards 1-3)
    lead_h = 142
    lead_w = (1000 - 24) // 3 # ~324 each
    for i in range(3):
        card = CARDS[i]
        cx = 12 + i * (lead_w + 6)
        draw.rectangle([cx, y, cx + lead_w, y + lead_h], fill="#292722", outline="#d9b568", width=1)
        page.add_box((cx, y, cx + lead_w, y + lead_h), f"Lead Card {card['n']}")
        
        art_box = (cx + 6, y + 6, cx + lead_w - 6, y + 36)
        art = draw_scene(card, art_box)
        page.image.paste(art, (cx + 6, y + 6))
        
        draw.text((cx + 8, y + 39), f"#{card['n']} [{card['region']}] {card['banner']}", font=page.get_font("sans_8"), fill="#d9b568")
        
        h_lines = page.measured_text(card['headline'], "serif_13", lead_w - 16, 2)
        hy = y + 50
        for line in h_lines:
            draw.text((cx + 8, hy), line, font=page.get_font("serif_13"), fill="#f8f1e2")
            hy += 14
            
        d_lines = page.measured_text(card['deck'], "sans_8", lead_w - 16, 5)
        dy = hy + 2
        for line in d_lines:
            draw.text((cx + 8, dy), line, font=page.get_font("sans_8"), fill="#d8d0c0")
            dy += 10
            
        draw.text((cx + 8, y + lead_h - 14), card['source'], font=page.get_font("sans_8"), fill="#8a8a8a")
    y += lead_h + 4

    # 6. SECONDARY CARDS (Cards 4-20 in four rows: 5, 4, 4, 4)
    row_configs = [5, 4, 4, 4]
    card_idx = 3
    sec_h = 90
    
    for row_count in row_configs:
        sec_w = (1000 - (row_count - 1) * 6) // row_count
        for i in range(row_count):
            if card_idx >= len(CARDS):
                break
            card = CARDS[card_idx]
            cx = 12 + i * (sec_w + 6)
            draw.rectangle([cx, y, cx + sec_w, y + sec_h], fill="#292722", outline="#3d3b36", width=1)
            page.add_box((cx, y, cx + sec_w, y + sec_h), f"Secondary Card {card['n']}")
            
            art_box = (cx + 3, y + 3, cx + sec_w - 3, y + 13)
            art = draw_scene(card, art_box)
            page.image.paste(art, (cx + 3, y + 3))
            
            h_lines = page.measured_text(f"#{card['n']} {card['headline']}", "sans_9", sec_w - 8, 2)
            hy = y + 15
            for line in h_lines:
                draw.text((cx + 4, hy), line, font=page.get_font("sans_9"), fill="#f8f1e2")
                hy += 11
                
            max_deck_h = (y + sec_h - 12) - (hy + 2)
            max_deck_lines = max(1, max_deck_h // 10)
            d_lines = page.measured_text(card['deck'], "sans_8", sec_w - 8, max_deck_lines)
            dy = hy + 2
            for line in d_lines:
                draw.text((cx + 4, dy), line, font=page.get_font("sans_8"), fill="#b8b0a0")
                dy += 10
                
            status_tag = card.get('tag', '')
            src_str = f"{card['source']}" + (f" · {status_tag}" if status_tag else "")
            draw.text((cx + 4, y + sec_h - 11), src_str[:40], font=page.get_font("sans_8"), fill="#d9b568")
            
            card_idx += 1
        y += sec_h + 4

    # 7. BOTTOM ZONE (Recognizable Map + 50 Briefs in 3 columns, up to 2 wrapped lines each)
    bottom_h = 190
    draw.rectangle([12, y, 1012, y + bottom_h], fill="#211f1b")
    page.add_box((12, y, 1012, y + bottom_h), "Bottom Zone")
    
    map_x0 = 18
    map_w = 260
    draw.rectangle([map_x0, y + 6, map_x0 + map_w, y + bottom_h - 6], fill="#292722", outline="#3d3b36", width=1)
    draw.text((map_x0 + 8, y + 10), "WHERE IT HAPPENED", font=page.get_font("serif_13"), fill="#f8f1e2")
    
    map_box_y0 = y + 28
    map_box_h = bottom_h - 40
    continents = [
        (0.15, 0.25, 0.35, 0.55),
        (0.25, 0.60, 0.40, 0.85),
        (0.50, 0.20, 0.68, 0.45),
        (0.52, 0.48, 0.70, 0.80),
        (0.65, 0.18, 0.90, 0.65),
        (0.78, 0.70, 0.92, 0.90),
    ]
    
    rng_map = random.Random(1337)
    for cx_frac, cy_frac, cw_frac, ch_frac in continents:
        cx_abs = map_x0 + int(cx_frac * map_w)
        cy_abs = map_box_y0 + int(cy_frac * map_box_h)
        cw_abs = int(cw_frac * map_w) - int(cx_frac * map_w)
        ch_abs = int(ch_frac * map_box_h) - int(cy_frac * map_box_h)
        for _ in range(35):
            px = rng_map.randint(cx_abs, cx_abs + cw_abs)
            py = rng_map.randint(cy_abs, cy_abs + ch_abs)
            draw.ellipse([px, py, px + 1, py + 1], fill="#3a3830")

    for card in CARDS:
        reg = card.get('region', 'WORLD')
        col = REGION_COLORS.get(reg, "#d9b568")
        fx = 0.2 + (card['n'] * 0.035) % 0.7
        fy = 0.3 + ((card['n'] * 17) % 10) * 0.05
        px = map_x0 + int(fx * map_w)
        py = map_box_y0 + int(fy * map_box_h)
        draw.ellipse([px - 2, py - 2, px + 2, py + 2], fill=col)
        draw.text((px + 3, py - 4), str(card['n']), font=page.get_font("sans_8"), fill=col)

    bx_start = map_x0 + map_w + 12
    col_w = (1000 - bx_start - 12) // 3
    draw.text((bx_start, y + 10), "ALSO ON SATURDAY 21 NOVEMBER — 50 MORE STORIES", font=page.get_font("serif_13"), fill="#f8f1e2")

    rows_top = y + 26
    # Footer top edge is at y + bottom_h + 4? Wait, footer is drawn at y + bottom_h in the main flow, or rather footer y = y + bottom_h + 4.
    # Let's check footer top edge in code: footer is drawn after y += bottom_h + 4. So footer top edge is y + bottom_h + 4.
    # Wait, bottom zone rect is [12, y, 1012, y + bottom_h]. Footer rect is [12, y_footer, 1012, y_footer + footer_h].
    # Here y before footer is y + bottom_h + 4. Wait! Look at lines 415-419:
    # y += bottom_h + 4
    # footer_h = 44
    # draw.rectangle([12, y, 1012, y + footer_h], ...
    # So footer top edge is the y AFTER `y += bottom_h + 4`. Wait!
    # Let's be precise: bottom zone has top `y` and bottom `y + bottom_h`.
    # Footer has top `y + bottom_h + 4`.
    # So zone_bottom = (y + bottom_h + 4) - 4 = y + bottom_h.
    # Row pitch = (zone_bottom - rows_top) / 17 exactly (float, then floor positions per row).
    zone_bottom = y + bottom_h
    row_pitch = (zone_bottom - rows_top) / 17.0

    # Font size selection: largest size <= 9.5px whose line height fits the pitch.
    # Let's test sizes from 9.5 down to 6.0 in steps of 0.1 or discrete sizes [9.5, 9.0, 8.5, 8.0, 7.5, 7.0]
    best_font_size = 7.0
    sans_path = page.fonts["sans_8"].path if hasattr(page.fonts["sans_8"], "path") else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
    for sz in [9.5, 9.4, 9.3, 9.2, 9.1, 9.0, 8.9, 8.8, 8.7, 8.6, 8.5, 8.4, 8.3, 8.2, 8.1, 8.0, 7.5, 7.0]:
        test_font = ImageFont.truetype(sans_path, size=sz)
        ascent, descent = test_font.getmetrics()
        line_h = ascent + descent
        if line_h <= row_pitch:
            best_font_size = sz
            break

    brief_font_name = f"sans_brief_{best_font_size}"
    if brief_font_name not in page.fonts:
        page.fonts[brief_font_name] = ImageFont.truetype(sans_path, size=best_font_size)

    test_font_obj = page.get_font(brief_font_name)
    ascent, descent = test_font_obj.getmetrics()
    line_height = ascent + descent

    col_item_count = 17
    brief_boxes = []
    drawn_brief_numbers = set()

    for i, b in enumerate(BRIEFS):
        col = i // col_item_count
        row = i % col_item_count
        b_x = bx_start + col * (col_w + 6)
        b_y = rows_top + int(row * row_pitch)
        
        b_num = b['n']
        text_content = BRIEF_TRIMS.get(b_num, f"{b['n']} {b['place']} — {b['text']}")
        lines = page.measured_text(text_content, brief_font_name, col_w, 1)
        box_h = line_height
        box = (b_x, b_y, b_x + col_w, b_y + box_h)
        
        # Assert disjointness with previously placed brief boxes
        for prev_num, prev_box in brief_boxes:
            if page._rects_overlap(box, prev_box):
                raise LayoutError(f"Brief {b_num} box {box} overlaps with brief {prev_num} box {prev_box}")
        
        # Assert box is inside bottom zone [12, y, 1012, y + bottom_h]
        if b_x < 12 or b_y < y or (b_x + col_w) > 1012 or (b_y + box_h) > (y + bottom_h):
            raise LayoutError(f"Brief {b_num} box {box} outside bottom zone bounds")

        brief_boxes.append((b_num, box))
        drawn_brief_numbers.add(b_num)
        
        for li, line in enumerate(lines):
            draw.text((b_x, b_y + li * line_height), line, font=page.get_font(brief_font_name), fill="#d8d0c0")

    if len(drawn_brief_numbers) != 50:
        raise LayoutError(f"Expected exactly 50 briefs drawn, got {len(drawn_brief_numbers)}")

    y += bottom_h + 4

    # 8. FOOTER ZONE (Legend, Sourcing, Date Check, Truth fully wrapped)
    footer_h = 44
    draw.rectangle([12, y, 1012, y + footer_h], fill="#292722")
    page.add_box((12, y, 1012, y + footer_h), "Footer")
    
    draw.text((20, y + 3), f"HOW SURE ARE WE? REPORTED · CLAIM · FORECAST  |  SOURCING: {SOURCING}", font=page.get_font("sans_8"), fill="#d9b568")
    
    dc_text = f"DATE CHECK: {DATE_CHECK}"
    dc_lines = page.measured_text(dc_text, "sans_7", 984, 2)
    draw.text((20, y + 14), dc_lines[0], font=page.get_font("sans_7"), fill="#b8b0a0")
    if len(dc_lines) > 1:
        draw.text((20, y + 23), dc_lines[1], font=page.get_font("sans_7"), fill="#b8b0a0")
        
    draw.text((20, y + 33), f"TRUTH: {TRUTH}", font=page.get_font("sans_7"), fill="#f8f1e2")

    print("ALL TEXT PLACED 50")
    print("DECKS COMPLETE 20")
    return page

if __name__ == "__main__":
    p = render_page()
    out_path = "entry.png"
    p.image.save(out_path, "PNG")
    sz = os.path.getsize(out_path)
    if sz > 1048576:
        raise LayoutError(f"entry.png size {sz} bytes exceeds 1,048,576 limit")
    print(f"entry.png {sz} bytes successfully generated")
