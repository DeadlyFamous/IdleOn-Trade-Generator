import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import pandas as pd
import os
import io
from datetime import datetime

# --- CONFIGURATION ---
PAGE_TITLE = "IdleOn Companion Trade Image Generator"
# Make sure your image filenames in 'assets' match these exactly (lowercase in folder)
PET_LIST = [
    # Season 1: Legacy
    "King Doot", "Rift Slug", "Dedotated Ram", "Crystal Custard", 
    "Sheepie", "Molti", "Bored Bean", "Slime", 
    "Sandy Pot", "Bloque", "Frog",

    # Season 2: Fallen Spirits
    "Ancient Golem", "Samurai Guardian", "Rift Jocund", "Leek Spirit", 
    "Crystal Capybara", "Biggole Mole", "Gigafrog", "Mashed Potatoe", 
    "Flying Worm", "Poisonic Frog", "Quenchie", "Green Mushroom",

    # Season 3: Shallow Waters
    "Whallamus", "Balloonfish", "Pufferblob", "Shellslug", 
    "Crystal Cuttlefish", "Eamsy Earl", "Litterfish", "Spearfish", 
    "Equinox Broadbass", "Mafioso", "Baby Boa", "Purp Mushroom",

    # Event & Pack Exclusives
    "Cool Bird", "Axolotl", "Mallay", "Reindeer", "Whale", "Marvelous Pig Pet"
]

st.set_page_config(page_title=PAGE_TITLE, layout="wide")

# --- SESSION STATE ---
if 'trade_rows' not in st.session_state:
    st.session_state.trade_rows = []
if 'want_select' not in st.session_state:
    st.session_state.want_select = []
if 'offer_select' not in st.session_state:
    st.session_state.offer_select = []
# Clear widget values at start of run (before widgets exist) when requested
if st.session_state.get('_clear_selections'):
    st.session_state.want_select = []
    st.session_state.offer_select = []
    del st.session_state['_clear_selections']

# --- FUNCTIONS ---

def get_pet_image_path(pet_name):
    """Resolve asset path: try .png and .gif, with both space and underscore in name."""
    base = pet_name.lower()
    base_underscore = base.replace(" ", "_")
    for name in (base, base_underscore):
        for ext in (".png", ".gif"):
            path = f"{name}{ext}"
            if os.path.exists(path):
                return path
    return None

def get_pet_frame_count(img_path):
    """Return number of frames (1 for static, n_frames for GIF)."""
    if not img_path or not os.path.exists(img_path):
        return 1
    try:
        img = Image.open(img_path)
        return getattr(img, "n_frames", 1)
    except Exception:
        return 1

def load_pet_image(img_path, size=(60, 60)):
    """Load pet image from path; for GIFs use first frame."""
    img = Image.open(img_path).convert("RGBA")
    if getattr(img, "n_frames", 1) > 1:
        img.seek(0)
    return img.resize(size)

def load_pet_image_at_frame(img_path, size=(60, 60), frame_index=0):
    """Load pet image at a specific animation frame (for GIFs). Seek before convert so the right frame is used."""
    img = Image.open(img_path)
    n = getattr(img, "n_frames", 1)
    if n > 1:
        img.seek(frame_index % n)
    img = img.convert("RGBA").resize(size)
    return img

def _max_frames_in_trades(trades):
    """Maximum frame count among all pet assets used in these trades."""
    max_n = 1
    for trade in trades:
        for pet in trade["want"] + trade["offer"]:
            path = get_pet_image_path(pet)
            if path:
                max_n = max(max_n, get_pet_frame_count(path))
    return max_n

def generate_image(trades):
    """
    Creates a single image: Left = WANT, Right = OFFER
    """
    # Settings
    row_height = 120
    img_width = 800
    bg_color = (40, 44, 52) 
    text_color = (255, 255, 255)
    
    # Calculate canvas size
    total_height = max(row_height * len(trades), row_height)
    canvas = Image.new('RGB', (img_width, total_height), color=bg_color)
    draw = ImageDraw.Draw(canvas)
    
    try:
        font = ImageFont.truetype("arial.ttf", 24)
    except Exception:
        font = ImageFont.load_default()

    y = 10 

    for trade in trades:
        # --- LEFT SIDE: WANT ---
        draw.text((20, y+40), "WANT:", font=font, fill=(100, 255, 100)) # Green text
        current_x = 120
        
        for pet in trade['want']:
            img_path = get_pet_image_path(pet)
            if img_path:
                pet_img = load_pet_image(img_path)
                canvas.paste(pet_img, (current_x, y+20), pet_img)
                current_x += 70
            else:
                draw.text((current_x, y+40), pet, font=font, fill=text_color)
                current_x += 80 
        
        # --- CENTER: ARROW ---
        draw.text((img_width//2 - 20, y+40), "-->", font=font, fill=text_color)

        # --- RIGHT SIDE: OFFER ---
        draw.text((img_width//2 + 50, y+40), "OFFER:", font=font, fill=(255, 100, 100)) # Red text
        current_x = img_width//2 + 150
        
        for pet in trade['offer']:
            img_path = get_pet_image_path(pet)
            if img_path:
                pet_img = load_pet_image(img_path)
                canvas.paste(pet_img, (current_x, y+20), pet_img)
                current_x += 70
            else:
                draw.text((current_x, y+40), pet, font=font, fill=text_color)
                current_x += 80

        # Divider line
        draw.line([(0, y+110), (img_width, y+110)], fill=(80, 80, 80), width=2)
        y += row_height

    return canvas

def generate_single_frame(trades, frame_index, row_height=120, img_width=800, bg_color=(40, 44, 52), text_color=(255, 255, 255)):
    """Draw one frame of the trade image with pets at the given animation frame."""
    total_height = max(row_height * len(trades), row_height)
    canvas = Image.new("RGB", (img_width, total_height), color=bg_color)
    draw = ImageDraw.Draw(canvas)
    try:
        font = ImageFont.truetype("arial.ttf", 24)
    except Exception:
        font = ImageFont.load_default()
    y = 10
    for trade in trades:
        draw.text((20, y + 40), "WANT:", font=font, fill=(100, 255, 100))
        current_x = 100
        for pet in trade["want"]:
            img_path = get_pet_image_path(pet)
            if img_path:
                pet_img = load_pet_image_at_frame(img_path, (60, 60), frame_index)
                canvas.paste(pet_img, (current_x, y + 20), pet_img)
                current_x += 70
            else:
                draw.text((current_x, y + 40), pet, font=font, fill=text_color)
                current_x += 80
        ##draw.text((img_width // 2 - 80, y + 40), "->", font=font, fill=text_color)
        draw.text((img_width // 2 - 80, y + 40), "OFFER:", font=font, fill=(255, 100, 100))
        current_x = img_width // 2 + 20
        for pet in trade["offer"]:
            img_path = get_pet_image_path(pet)
            if img_path:
                pet_img = load_pet_image_at_frame(img_path, (60, 60), frame_index)
                canvas.paste(pet_img, (current_x, y + 20), pet_img)
                current_x += 70
            else:
                draw.text((current_x, y + 40), pet, font=font, fill=text_color)
                current_x += 80
        draw.line([(0, y + 110), (img_width, y + 110)], fill=(80, 80, 80), width=2)
        y += row_height
    return canvas

def generate_animated_gif(trades, duration_ms=120, loop=0):
    """Build an animated GIF from trade rows; uses each pet GIF's frames. Returns GIF bytes."""
    n_frames = _max_frames_in_trades(trades)
    frames = [generate_single_frame(trades, i) for i in range(n_frames)]
    if not frames:
        return None
    # Quantize every frame to the first frame's palette so background/text stay same color (no flicker)
    first_p = frames[0].convert("P", palette=Image.ADAPTIVE)
    rest_p = [f.quantize(palette=first_p) for f in frames[1:]]
    buf = io.BytesIO()
    first_p.save(buf, format="GIF", save_all=True, append_images=rest_p, loop=loop, duration=duration_ms)
    buf.seek(0)
    return buf.getvalue()

def save_data_locally(trades):
    data_records = []
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    for trade in trades:
        data_records.append({
            "timestamp": timestamp,
            "want": ", ".join(trade['want']),
            "offer": ", ".join(trade['offer']),
            "row_count": len(trades)
        })
    
    df = pd.DataFrame(data_records)
    if not os.path.isfile("trade_analytics.csv"):
        df.to_csv("trade_analytics.csv", index=False)
    else:
        df.to_csv("trade_analytics.csv", mode='a', header=False, index=False)

# --- UI LAYOUT ---

st.title("🐾 IdleOn Trade Image Generator")
st.markdown("Select what you **WANT** (Left) and what you **OFFER** (Right).")

# 1. The Input Form
with st.container(border=True):
    col1, col2, col3 = st.columns([2, 0.5, 2])
    
    # --- FIXED SECTION ---
    with col1:
        # Left Side = Want
        want_pets = st.multiselect("I Want This Companion:", PET_LIST, key="want_select")
    
    with col2:
        st.markdown("<h2 style='text-align: center;'>➡</h2>", unsafe_allow_html=True)
        
    with col3:
        # Right Side = Offer
        offer_pets = st.multiselect("I Offer:", PET_LIST, key="offer_select")
    
    add_btn = st.button("➕ Add Row to Trade")

# Logic: Add to session state
if add_btn:
    if not offer_pets and not want_pets:
        st.error("Please select at least one companion!")
    else:
        # Store exactly as named
        st.session_state.trade_rows.append({
            "want": want_pets,
            "offer": offer_pets
        })
        # Request clear on next run (can't modify widget state after widgets are created)
        st.session_state['_clear_selections'] = True
        st.rerun()

# 2. Display Current List (Preview)
if len(st.session_state.trade_rows) > 0:
    st.write("### Current Trade List")
    
    for i, row in enumerate(st.session_state.trade_rows):
        c1, c2, c3 = st.columns([4, 4, 1])
        # Display correctly in text preview too
        c1.text(f"Want: {', '.join(row['want'])}")
        c2.text(f"Offer: {', '.join(row['offer'])}")
        
        if c3.button("❌", key=f"del_{i}"):
            st.session_state.trade_rows.pop(i)
            st.rerun()

    st.divider()

    # 3. Generate Image & Save Data
    if st.button("🎨 Generate Trade Image", type="primary"):
        gif_bytes = generate_animated_gif(st.session_state.trade_rows)
        png_image = generate_image(st.session_state.trade_rows)  # static first frame for PNG
        st.session_state["_last_gif_bytes"] = gif_bytes
        st.session_state["_last_png_image"] = png_image
        save_data_locally(st.session_state.trade_rows)
        st.rerun()

    if "_last_gif_bytes" in st.session_state:
        gif_bytes = st.session_state["_last_gif_bytes"]
        st.image(gif_bytes, caption="Animated trade image (loops). Right click to save or use buttons below.")
        st.caption("✅ Trade data saved to analytics database.")

        # Export as PNG (static) or GIF (animated loop)
        col_png, col_gif, _ = st.columns([1, 1, 2])
        with col_png:
            buf_png = io.BytesIO()
            st.session_state["_last_png_image"].save(buf_png, format="PNG")
            st.download_button(
                "📥 Download PNG",
                data=buf_png.getvalue(),
                file_name="trade_image.png",
                mime="image/png",
                key="dl_png",
            )
        with col_gif:
            st.download_button(
                "📥 Download GIF (animated)",
                data=gif_bytes,
                file_name="trade_image.gif",
                mime="image/gif",
                key="dl_gif",
            )

else:
    st.info("Start by adding a row above!")
