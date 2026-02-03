import streamlit as st
from PIL import Image, ImageStat, ImageOps
import io
import zipfile
import math
from datetime import datetime

# --- 1. CONFIG & STYLING ---
st.set_page_config(
    page_title="AutoBrand Pro Ultra", 
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; }
    div[data-testid="stMetricValue"] { font-size: 24px; }
</style>
""", unsafe_allow_html=True)

# --- 2. SESSION STATE ---
if 'processed_images' not in st.session_state:
    st.session_state.processed_images = {}
if 'review_mode' not in st.session_state:
    st.session_state.review_mode = False

# --- 3. HELPER FUNCTIONS ---
def get_brightness(image, crop_box=None):
    if image.mode == 'RGBA':
        background = Image.new("RGB", image.size, (255, 255, 255))
        background.paste(image, mask=image.split()[3])
        target = background
    else:
        target = image
    if crop_box:
        region = target.crop(crop_box).convert('L')
    else:
        region = target.convert('L')
    stat = ImageStat.Stat(region)
    return stat.mean[0]

def change_opacity(img, opacity):
    img = img.copy().convert("RGBA")
    new_alpha = img.split()[3].point(lambda p: int(p * (opacity / 100.0)))
    img.putalpha(new_alpha)
    return img

def create_tiled_overlay(base_w, base_h, logo_img, scale_pct, spacing_scale=1.5):
    overlay = Image.new('RGBA', (base_w, base_h), (0,0,0,0))
    tile_w = max(20, int(base_w * (scale_pct / 100)))
    aspect = logo_img.width / logo_img.height
    tile_h = int(tile_w / aspect)
    tile_logo = logo_img.resize((tile_w, tile_h), Image.Resampling.LANCZOS)
    step_x, step_y = int(tile_w * spacing_scale), int(tile_h * spacing_scale)
    for y in range(0, base_h, step_y):
        for x in range(0, base_w, step_x):
            shift = int(step_x / 2) if (y // step_y) % 2 == 1 else 0
            if (x + shift) < base_w and y < base_h:
                overlay.paste(tile_logo, (x + shift, y), tile_logo)
    return overlay

def process_single_image(image_file, logo_black, logo_white, settings, manual_override=None):
    img = Image.open(image_file).convert("RGBA")
    img_w, img_h = img.size
    style, corner, scale = settings['style'], settings['corner'], settings['scale']
    padding, threshold, opacity = settings['padding'], settings['threshold'], settings['opacity']
    
    if manual_override:
        used_color = manual_override
    else:
        # Smart Logic to find Brightness
        brightness = get_brightness(img)
        used_color = "White" if brightness < threshold else "Black"

    raw_logo = logo_black.copy() if used_color == "Black" else logo_white.copy()
    logo_final = change_opacity(raw_logo, opacity)
    watermark_layer = Image.new('RGBA', img.size, (0,0,0,0))
    
    if style == "Tiled (Pattern)":
        watermark_layer = create_tiled_overlay(img_w, img_h, logo_final, scale)
    elif style == "Center (Big)":
        t_w = int(img_w * (scale / 100))
        t_h = int(t_w / (logo_final.width / logo_final.height))
        logo_resized = logo_final.resize((t_w, t_h), Image.Resampling.LANCZOS)
        watermark_layer.paste(logo_resized, ((img_w - t_w)//2, (img_h - t_h)//2), logo_resized)
    else:
        t_w = int(img_w * (scale / 100))
        t_h = int(t_w / (logo_final.width / logo_final.height))
        logo_resized = logo_final.resize((t_w, t_h), Image.Resampling.LANCZOS)
        pad_x, pad_y = int(img_w * (padding/100)), int(img_h * (padding/100))
        if corner == "Bottom Right": x, y = img_w - t_w - pad_x, img_h - t_h - pad_y
        elif corner == "Bottom Left": x, y = pad_x, img_h - t_h - pad_y
        elif corner == "Top Right": x, y = img_w - t_w - pad_x, pad_y
        else: x, y = pad_x, pad_y
        watermark_layer.paste(logo_resized, (x, y), logo_resized)

    return Image.alpha_composite(img, watermark_layer), used_color

# --- 4. UI ---
with st.sidebar:
    st.header("🎨 Watermark Style")
    wm_style = st.selectbox("Choose Style", ["Corner (Standard)", "Center (Big)", "Tiled (Pattern)"])
    st.divider()
    if wm_style == "Corner (Standard)":
        wm_scale = st.slider("Logo Size (%)", 5, 50, 15)
        wm_corner = st.selectbox("Position", ["Bottom Right", "Bottom Left", "Top Right", "Top Left"])
        wm_opacity = st.slider("Opacity (%)", 10, 100, 100)
    elif wm_style == "Center (Big)":
        wm_scale = st.slider("Center Size (%)", 20, 90, 50)
        wm_corner, wm_opacity = "Center", st.slider("Opacity (%)", 10, 100, 30)
    else:
        wm_scale = st.slider("Tile Size (%)", 5, 30, 10)
        wm_corner, wm_opacity = "Tiled", st.slider("Opacity (%)", 5, 100, 15)
    
    wm_padding = st.slider("Edge Padding (%)", 0, 10, 2)
    wm_threshold = st.slider("Color Threshold", 0, 255, 128)
    out_fmt = st.radio("Format", ["JPG", "PNG"], horizontal=True)
    current_settings = {'style': wm_style, 'corner': wm_corner, 'scale': wm_scale, 'padding': wm_padding, 'threshold': wm_threshold, 'opacity': wm_opacity}

st.title(f"🛡️ AutoBrand: {wm_style}")
tab1, tab2 = st.tabs(["📤 Upload", "👁️ Review"])

with tab1:
    c1, c2 = st.columns(2)
    u_files = c1.file_uploader("Images", type=['jpg','png','jpeg','webp'], accept_multiple_files=True)
    b_logo_file = c2.file_uploader("BLACK Logo", type=['png'])
    w_logo_file = c2.file_uploader("WHITE Logo", type=['png'])

    if u_files and b_logo_file and w_logo_file:
        if st.button("🚀 Apply Watermarks", type="primary"):
            b_logo, w_logo = Image.open(b_logo_file), Image.open(w_logo_file)
            st.session_state.processed_images = {}
            for f in u_files:
                img, color = process_single_image(f, b_logo, w_logo, current_settings)
                st.session_state.processed_images[f.name] = {"original": f, "processed": img, "color": color, "logos": (b_logo, w_logo), "include": True}
            st.session_state.review_mode = True
            st.success("Switch to Review Tab!")

with tab2:
    if st.session_state.review_mode:
        items = list(st.session_state.processed_images.items())
        for i in range(0, len(items), 3):
            cols = st.columns(3)
            for j in range(3):
                if i+j < len(items):
                    name, data = items[i+j]
                    with cols[j].container(border=True):
                        st.image(data["processed"] if data["include"] else ImageOps.grayscale(data["processed"]), use_container_width=True)
                        keep = st.checkbox("Keep", value=data["include"], key=f"k_{name}")
                        if keep != data["include"]:
                            st.session_state.processed_images[name]["include"] = keep
                            st.rerun()

        # Download ZIP
        z_buf = io.BytesIO()
        with zipfile.ZipFile(z_buf, "w") as zf:
            for n, d in st.session_state.processed_images.items():
                if d['include']:
                    buf = io.BytesIO()
                    final = d['processed'].convert("RGB") if out_fmt == "JPG" else d['processed']
                    final.save(buf, format="JPEG" if out_fmt=="JPG" else "PNG")
                    zf.writestr(f"branded_{n}", buf.getvalue())
        st.download_button("📥 Download All", z_buf.getvalue(), "batch.zip", "application/zip", type="primary")
