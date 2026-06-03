import svgwrite
import math
import base64

ZODIAC_ELEMENTS = {
    "Aries": "Fire", "Leo": "Fire", "Sagittarius": "Fire",
    "Taurus": "Earth", "Virgo": "Earth", "Capricorn": "Earth",
    "Gemini": "Air", "Libra": "Air", "Aquarius": "Air",
    "Cancer": "Water", "Scorpio": "Water", "Pisces": "Water"
}

ELEMENT_COLORS = {
    "Fire": "#e65a3c",
    "Earth": "#4a7a5a",
    "Air": "#d9b340",
    "Water": "#4f6b9c"
}

ZODIAC_SYMBOLS = {
    "Aries": "♈", "Taurus": "♉", "Gemini": "♊", "Cancer": "♋",
    "Leo": "♌", "Virgo": "♍", "Libra": "♎", "Scorpio": "♏",
    "Sagittarius": "♐", "Capricorn": "♑", "Aquarius": "♒", "Pisces": "♓"
}

PLANET_SYMBOLS = {
    "Sun": "☀️", "Moon": "🌙", "Mercury": "☿", "Venus": "♀",
    "Mars": "♂", "Jupiter": "♃", "Saturn": "♄"
}

ASPECT_COLORS = {
    "Conjunction": "#ffd700",
    "Sextile": "#00ff00",
    "Square": "#ff0000",
    "Trine": "#0088ff",
    "Opposition": "#880000"
}

def generate_birth_chart_image(
    planets: dict,
    houses: dict,
    ascendant: float,
    midheaven: float,
    name: str,
    birth_info: str
) -> dict:
    
    # 800x800 SVG
    width, height = 800, 800
    cx, cy = width / 2, height / 2
    
    dwg = svgwrite.Drawing(size=(f"{width}px", f"{height}px"), profile='full')
    
    # Background
    dwg.add(dwg.rect(insert=(0, 0), size=('100%', '100%'), fill='#1a1a2e'))
    
    # Info Box (Top Left)
    info_group = dwg.g(font_family="serif", font_size="14px", fill="#e6d5b8")
    info_group.add(dwg.text(f"Natal Chart for {name}", insert=(20, 30), font_size="18px", font_weight="bold"))
    info_group.add(dwg.text(birth_info, insert=(20, 50)))
    
    asc_str = f"ASC: {ZODIAC_SYMBOLS.get(get_zodiac_sign(ascendant), '')} {int(ascendant)%30}° {get_zodiac_sign(ascendant)}"
    mc_str = f"MC: {ZODIAC_SYMBOLS.get(get_zodiac_sign(midheaven), '')} {int(midheaven)%30}° {get_zodiac_sign(midheaven)}"
    
    info_group.add(dwg.text(asc_str, insert=(20, 75)))
    info_group.add(dwg.text(mc_str, insert=(20, 95)))
    info_group.add(dwg.text("System: Placidus / Tropical", insert=(20, 115)))
    dwg.add(info_group)
    
    # Helper to calculate x,y on a circle based on degree
    # In astrology, Ascendant (usually drawn on left at 180 degrees visually)
    # Let's align Ascendant to the left (180 deg in SVG polar).
    # So SVG angle = 180 - (degree - ascendant)
    def deg_to_xy(deg, radius):
        # 0 degree astrology = Ascendant (Left = 180)
        # going counter-clockwise
        svg_angle = math.radians(180 + (ascendant - deg))
        x = cx + radius * math.cos(svg_angle)
        y = cy + radius * math.sin(svg_angle)
        return x, y
        
    r_outer = 350
    r_zodiac_inner = 310
    r_house_inner = 200
    
    # Draw Outer Zodiac Wheel
    dwg.add(dwg.circle(center=(cx, cy), r=r_outer, stroke='#e6d5b8', stroke_width=2, fill='none'))
    dwg.add(dwg.circle(center=(cx, cy), r=r_zodiac_inner, stroke='#e6d5b8', stroke_width=2, fill='none'))
    
    for i, sign in enumerate(ZODIAC_ELEMENTS.keys()):
        start_deg = i * 30
        end_deg = start_deg + 30
        mid_deg = start_deg + 15
        
        # Draw sign separator line
        x1, y1 = deg_to_xy(start_deg, r_outer)
        x2, y2 = deg_to_xy(start_deg, r_zodiac_inner)
        dwg.add(dwg.line(start=(x1, y1), end=(x2, y2), stroke='#e6d5b8', stroke_width=1))
        
        # Color arc (Optional, SVG arcs are complex, skipping fill for simplicity, just text color)
        color = ELEMENT_COLORS[ZODIAC_ELEMENTS[sign]]
        
        xt, yt = deg_to_xy(mid_deg, r_outer - 20)
        dwg.add(dwg.text(ZODIAC_SYMBOLS[sign], insert=(xt, yt), text_anchor="middle", alignment_baseline="middle", font_size="24px", fill=color))
        
        xt_name, yt_name = deg_to_xy(mid_deg, r_zodiac_inner + 12)
        dwg.add(dwg.text(sign[:3].upper(), insert=(xt_name, yt_name), text_anchor="middle", alignment_baseline="middle", font_size="10px", fill=color))

    # Draw House Wheel
    dwg.add(dwg.circle(center=(cx, cy), r=r_house_inner, stroke='#e6d5b8', stroke_width=1.5, fill='none'))
    
    for house_num, house_data in houses.items():
        cusp_deg = house_data["degrees"]
        x1, y1 = deg_to_xy(cusp_deg, r_zodiac_inner)
        x2, y2 = deg_to_xy(cusp_deg, r_house_inner)
        
        is_asc = str(house_num) == "1"
        is_mc = str(house_num) == "10"
        
        sw = 3 if is_asc or is_mc else 1
        st = "#ffaa00" if is_asc or is_mc else "rgba(230, 213, 184, 0.5)"
        
        dwg.add(dwg.line(start=(x1, y1), end=(x2, y2), stroke=st, stroke_width=sw))
        
        # House number
        next_house = str(int(house_num) + 1) if int(house_num) < 12 else "1"
        next_deg = houses[next_house]["degrees"]
        
        # calculate mid degree handling 360 wrap
        if next_deg < cusp_deg:
            next_deg += 360
        mid_deg = (cusp_deg + next_deg) / 2
        
        xt, yt = deg_to_xy(mid_deg, r_house_inner + 20)
        dwg.add(dwg.text(house_num, insert=(xt, yt), text_anchor="middle", alignment_baseline="middle", font_size="14px", fill="rgba(230, 213, 184, 0.7)"))

    # Draw Planets
    r_planet = r_house_inner - 25
    # simple collision avoidance based on angle
    placed_angles = []
    
    for p_name, p_data in planets.items():
        if p_name not in PLANET_SYMBOLS:
            continue
            
        deg = p_data["degrees"]
        
        # Adjust radius if planets are very close
        draw_r = r_planet
        for a, r in placed_angles:
            diff = abs(deg - a)
            if diff > 180: diff = 360 - diff
            if diff < 5 and abs(draw_r - r) < 15:
                draw_r -= 20
        placed_angles.append((deg, draw_r))
        
        x, y = deg_to_xy(deg, draw_r)
        
        # Symbol
        dwg.add(dwg.text(PLANET_SYMBOLS[p_name], insert=(x, y), text_anchor="middle", alignment_baseline="middle", font_size="20px", fill="#ffffff"))
        
        # Degree text
        deg_in_sign = int(deg) % 30
        dwg.add(dwg.text(f"{deg_in_sign}°", insert=(x + 12, y + 8), font_size="10px", fill="#e6d5b8"))

    # Determine aspects
    # we don't have aspect calculation here easily, let's just plot lines if we are passed aspect data
    # but the tool logic doesn't pass aspect data directly unless we do it.
    # Actually, we should just calculate it here to draw lines
    aspect_defs = {
        "Conjunction": (0, 8),
        "Sextile": (60, 6),
        "Square": (90, 8),
        "Trine": (120, 8),
        "Opposition": (180, 8)
    }
    
    pnames = list(p for p in planets.keys() if p in PLANET_SYMBOLS)
    for i in range(len(pnames)):
        for j in range(i+1, len(pnames)):
            p1 = pnames[i]
            p2 = pnames[j]
            d1 = planets[p1]["degrees"]
            d2 = planets[p2]["degrees"]
            diff = abs(d1 - d2)
            if diff > 180: diff = 360 - diff
            
            for asp, (ang, orb) in aspect_defs.items():
                if abs(diff - ang) <= orb:
                    if asp != "Conjunction":  # Don't draw lines for conjunctions
                        x1, y1 = deg_to_xy(d1, r_house_inner - 45)
                        x2, y2 = deg_to_xy(d2, r_house_inner - 45)
                        dwg.add(dwg.line(start=(x1, y1), end=(x2, y2), stroke=ASPECT_COLORS[asp], stroke_width=1, opacity=0.6))

    svg_str = dwg.tostring()
    b64 = base64.b64encode(svg_str.encode('utf-8')).decode('utf-8')
    
    return {
        "success": True,
        "image_base64": f"data:image/svg+xml;base64,{b64}"
    }

def get_zodiac_sign(degrees: float) -> str:
    ZODIAC_SIGNS = [
        "Aries", "Taurus", "Gemini", "Cancer",
        "Leo", "Virgo", "Libra", "Scorpio",
        "Sagittarius", "Capricorn", "Aquarius", "Pisces"
    ]
    index = int(degrees / 30) % 12
    return ZODIAC_SIGNS[index]
