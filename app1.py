import streamlit as st
from PIL import Image, ImageStat, ImageOps
import io
import zipfile
import math

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
    """Calculates brightness. If crop_box is None, analyzes whole image."""
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
    """Adjusts the opacity of an RGBA image."""
    img = img.copy()
    alpha = img.split()[3]
    alpha = ImageStat.Stat(alpha).mean[0]
    # Reduce alpha by the opacity percentage
    alpha_factor = opacity / 100.0
    
    # Create a new alpha channel
    new_alpha = img.split()[3].point(lambda p: int(p * alpha_factor))
    img.putalpha(new_alpha)
    return img

def create_tiled_overlay(base_w, base_h, logo_img, scale_pct, spacing_scale=1.5):
    """Creates a transparent layer with the logo repeated in a grid."""
    overlay = Image.new('RGBA', (base_w, base_h), (0,0,0,0))
    
    # Calculate tile size
    tile_w = int(base_w * (scale_pct / 100))
    if tile_w < 20: tile_w = 20
    aspect = logo_img.width / logo_img.height
    tile_h = int(tile_w / aspect)
    
    # Resize logo once
    tile_logo = logo_img.resize((tile_w, tile_h), Image.Resampling.LANCZOS)
    
    # Grid Logic
    cols = int(base_w / tile_w) + 2
    rows = int(base_h / tile_h) + 2
    
    step_x = int(tile_w * spacing_scale)
    step_y = int(tile_h * spacing_scale)
    
    for y in range(0, base_h, step_y):
        for x in range(0, base_w, step_x):
            # Shift every other row for a "brick" pattern
            shift = int(step_x / 2) if (y // step_y) % 2 == 1 else 0
            
            # Paste (using the logo as its own mask)
            final_x = x + shift
            # Check bounds to avoid unnecessary pasting
            if final_x < base_w and y < base_h:
                overlay.paste(tile_logo, (final_x, y), tile_logo)
                
    return overlay

# --- 4. CORE PROCESSING ---

def process_single_image(image_file, logo_black, logo_white, settings, manual_override=None):
    """
    Main logic handling multiple styles.
    """
    img = Image.open(image_file).convert("RGBA")
    img_w, img_h = img.size
    
    # Unpack Settings
    style = settings['style']
    corner = settings['corner']
    scale = settings['scale']
    padding = settings['padding']
    threshold = settings['threshold']
    opacity = settings['opacity']
    
    # --- 1. DETERMINE COLOR ---
    # Smart detection logic differs by style
    ref_logo = logo_black
    
    if manual_override:
        used_color = manual_override
    else:
        # Auto-detect logic
        if style == "Tiled (Pattern)":
            # For tiled, check AVERAGE brightness of the whole image
            brightness = get_brightness(img)
        elif style == "Center (Big)":
            # Check center area brightness
            cw, ch = int(img_w*0.3), int(img_h*0.3)
            cx, cy = int((img_w-cw)/2), int((img_h-ch)/2)
            brightness = get_brightness(img, (cx, cy, cx+cw, cy+ch))
        else:
            # Corner logic (Standard)
            # Roughly estimate corner based on standard size
            test_w = int(img_w * (scale/100))
            test_h = int(test_w * (ref_logo.height / ref_logo.width))
            px = int(img_w*(padding/100))
            if "Right" in corner: x = img_w - test_w - px
            else: x = px
            if "Bottom" in corner: y = img_h - test_h - px
            else: y = px
            brightness = get_brightness(img, (x, y, x+test_w, y+test_h))
            
        if brightness < threshold:
            used_color = "White"
        else:
            used_color = "Black"

    # Select and Prep Logo Color
    raw_logo = logo_black.copy() if used_color == "Black" else logo_white.copy()
    
    # Apply Opacity
    logo_final = change_opacity(raw_logo, opacity)

    # --- 2. APPLY STYLE ---
    watermark_layer = Image.new('RGBA', img.size, (0,0,0,0))
    
    if style == "Tiled (Pattern)":
        # Generate Tiled Overlay
        # For tiled, we usually rotate the logo slightly (optional, handled in logic if needed)
        # Here we just pass the opaque logo to the tiler
        tiled_layer = create_tiled_overlay(img_w, img_h, logo_final, scale, spacing_scale=1.5)
        # Rotate the whole tiled layer slightly for that professional look? 
        # Optional: keeping it simple grid for now.
        watermark_layer = tiled_layer

    elif style == "Center (Big)":
        # Calculate Center Size
        t_w = int(img_w * (scale / 100))
        aspect = logo_final.width / logo_final.height
        t_h = int(t_w / aspect)
        
        logo_resized = logo_final.resize((t_w, t_h), Image.Resampling.LANCZOS)
        
        x = (img_w - t_w) // 2
        y = (img_h - t_h) // 2
        
        watermark_layer.paste(logo_resized, (x, y), logo_resized)
        
    else: # "Corner (Standard)"
        # Calculate Corner Size
        t_w = int(img_w * (scale / 100))
        aspect = logo_final.width / logo_final.height
        t_h = int(t_w / aspect)
        
        logo_resized = logo_final.resize((t_w, t_h), Image.Resampling.LANCZOS)
        
        pad_x = int(img_w * (padding / 100))
        pad_y = int(img_h * (padding / 100))
        
        if corner == "Bottom Right":
            x, y = img_w - t_w - pad_x, img_h - t_h - pad_y
        elif corner == "Bottom Left":
            x, y = pad_x, img_h - t_h - pad_y
        elif corner == "Top Right":
            x, y = img_w - t_w - pad_x, pad_y
        elif corner == "Top Left":
            x, y = pad_x, pad_y
            
        watermark_layer.paste(logo_resized, (x, y), logo_resized)

    # Composite
    final_img = Image.alpha_composite(img, watermark_layer)
    return final_img, used_color

# --- 5. UI SETUP ---
with st.sidebar:
    st.header("🎨 Watermark Style")
    
    # NEW: Style Selector
    wm_style = st.selectbox("Choose Style", ["Corner (Standard)", "Center (Big)", "Tiled (Pattern)"])
    
    st.divider()
    st.header("⚙️ Settings")
    
    # Dynamic settings based on style
    if wm_style == "Corner (Standard)":
        wm_scale = st.slider("Logo Size (%)", 5, 50, 15)
        wm_corner = st.selectbox("Position", ["Bottom Right", "Bottom Left", "Top Right", "Top Left"])
        wm_opacity = st.slider("Opacity (%)", 10, 100, 100)
    elif wm_style == "Center (Big)":
        wm_scale = st.slider("Center Logo Size (%)", 20, 90, 50)
        wm_corner = "Center" # Placeholder
        wm_opacity = st.slider("Opacity (%)", 10, 100, 30, help="Lower is better for center watermarks")
    else: # Tiled
        wm_scale = st.slider("Tile Size (%)", 5, 30, 10)
        wm_corner = "Tiled" # Placeholder
        wm_opacity = st.slider("Opacity (%)", 5, 100, 15, help="Lower is better for patterns")
        
    st.divider()
    with st.expander("🛠️ Advanced"):
        wm_padding = st.slider("Edge Padding (%)", 0, 10, 2)
        wm_threshold = st.slider("Contrast Threshold", 0, 255, 128)
        out_fmt = st.radio("Format", ["JPG", "PNG"], horizontal=True)

    # Dictionary to pass around easily
    current_settings = {
        'style': wm_style, 'corner': wm_corner, 'scale': wm_scale,
        'padding': wm_padding, 'threshold': wm_threshold, 'opacity': wm_opacity
    }

# --- 6. MAIN TABS ---
st.title(f"🛡️ AutoBrand: {wm_style} Mode")

tab1, tab2 = st.tabs(["📤 Upload & Process", "👁️ Review & Download"])

with tab1:
    col1, col2 = st.columns(2)
    with col1:
        u_files = st.file_uploader("Upload Bulk Images", type=['jpg','png','jpeg','webp'], accept_multiple_files=True)
    with col2:
        b_logo_file = st.file_uploader("Upload BLACK Logo", type=['png'])
        w_logo_file = st.file_uploader("Upload WHITE Logo", type=['png'])

    if u_files and b_logo_file and w_logo_file:
        st.divider()
        if st.button("🚀 Apply Watermarks", type="primary"):
            b_logo = Image.open(b_logo_file)
            w_logo = Image.open(w_logo_file)
            
            st.session_state.processed_images = {}
            
            progress = st.progress(0)
            for i, f in enumerate(u_files):
                f.seek(0)
                img, color = process_single_image(f, b_logo, w_logo, current_settings)
                
                st.session_state.processed_images[f.name] = {
                    "original": f, "processed": img, "color": color, 
                    "logos": (b_logo, w_logo), "include": True
                }
                progress.progress((i+1)/len(u_files))
            
            st.session_state.review_mode = True
            st.success("Done! Switch to the Review tab.")

with tab2:
    if st.session_state.review_mode:
        # Metrics
        total = len(st.session_state.processed_images)
        st.caption(f"Reviewing {total} images. Style applied: {wm_style}")
        
        # Grid
        items = list(st.session_state.processed_images.items())
        for i in range(0, len(items), 3):
            cols = st.columns(3)
            for j in range(3):
                if i+j < len(items):
                    name, data = items[i+j]
                    with cols[j]:
                        with st.container(border=True):
                            # Display
                            show_img = data["processed"] if data["include"] else ImageOps.grayscale(data["processed"])
                            st.image(show_img, use_container_width=True)
                            
                            # Controls
                            c1, c2 = st.columns([2, 1])
                            new_c = c1.radio("Color", ["Black", "White"], 
                                             index=0 if data["color"]=="Black" else 1, 
                                             key=f"r_{name}", horizontal=True, label_visibility="collapsed")
                            keep = c2.checkbox("Keep", value=data["include"], key=f"c_{name}")
                            
                            # Update Logic
                            if keep != data["include"]:
                                st.session_state.processed_images[name]["include"] = keep
                                st.rerun()
                                
                            if new_c != data["color"] and keep:
                                f_obj = data["original"]
                                f_obj.seek(0)
                                b, w = data["logos"]
                                # Reprocess with override
                                new_img, _ = process_single_image(f_obj, b, w, current_settings, manual_override=new_c)
                                st.session_state.processed_images[name]["processed"] = new_img
                                st.session_state.processed_images[name]["color"] = new_c
                                st.rerun()

        # Download
        st.divider()
        cnt = sum(1 for x in st.session_state.processed_images.values() if x['include'])
        if cnt > 0:
            z_buf = io.BytesIO()
            with zipfile.ZipFile(z_buf, "w") as zf:
                for n, d in st.session_state.processed_images.items():
                    if d['include']:
                        buf = io.BytesIO()
                        d['processed'] = d['processed'].convert("RGB") if out_fmt == "JPG" else d['processed']
                        d['processed'].save(buf, format="JPEG" if out_fmt=="JPG" else "PNG", quality=95)
                        zf.writestr(f"branded_{n.rsplit('.',1)[0]}.{out_fmt.lower()}", buf.getvalue())
            
            st.download_button(f"📥 Download {cnt} Images", z_buf.getvalue(), "branded_batch.zip", "application/zip", type="primary")
                                
