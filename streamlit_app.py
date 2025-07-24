import streamlit as st
from PIL import Image
import io

import streamlit as st

# --- CONFIGURATION ---
st.set_page_config(page_title="Analyse numérique du plan de masse", layout="centered")

# --- FONCTIONS UTILES ---
def rgb_to_hex(rgb): return '#%02x%02x%02x' % rgb
def hex_to_rgb(hex_code): return tuple(int(hex_code[i:i+2], 16) for i in (1, 3, 5))
def couleurs_proches(c1, c2): return all(abs(c1[i] - c2[i]) <= seuil for i in range(3))

# --- EN-TÊTE & LOGO ---
logo_url = "https://epa-paris-saclay.fr/wp-content/uploads/2021/12/00_paris-saclay-logo-012-scaled.jpg"
st.title("🖼️ Analyse d'image - Plan de masse")
st.write("Outil réalisé par [Mathias Pisch](https://www.linkedin.com/in/pseudo/)")
st.image(logo_url, width=200)

# --- UPLOAD IMAGE ---
uploaded_file = st.file_uploader("Glissez-déposez une image ici", type=["png", "jpg", "jpeg"])
if uploaded_file:
    st.image(uploaded_file, width=400)

# --- SÉLECTION DES COULEURS À DÉTECTER ---
st.markdown("### Couleurs à détecter")
col1, col2 = st.columns(2)
with col1:
    couleur_background = st.color_picker("Couleur du background", "#004DA9")
    couleur_nat_artificielle = st.color_picker("Couleur naturelle artificielle", "#90EE90")
with col2:
    couleur_urbanise = st.color_picker("Couleur urbanisée", "#FFFFFF")
    couleur_nat_existante = st.color_picker("Couleur naturelle existante", "#006400")
seuil = st.slider("Seuil de tolérance", 0, 150, 10)

st.write("Une valeur typique est 10. [En savoir plus](https://docs.google.com/presentation/d/e/2PACX-1vRxz5DE5uva9u3Uvqn1mU_ylCjGdndhxH_I_OZOBeHeFB6kRP1bo-b7rqyquY4hJ_0dxUsGc_hejEEd/pub)")

# --- COULEURS D’ANNOTATION ---
st.markdown("### Couleurs d’annotation")
col1, col2 = st.columns(2)
with col1:
    couleur_marqueur_urb = st.color_picker("Zones urbanisées", rgb_to_hex((255, 0, 0)))
    couleur_marqueur_nat_art = st.color_picker("Zones naturelles artificielles", rgb_to_hex((255, 165, 0)))
with col2:
    couleur_marqueur_nat_ex = st.color_picker("Zones naturelles existantes", rgb_to_hex((235, 246, 0)))

# Conversion HEX -> RGB
rgb_detect = {
    "background": hex_to_rgb(couleur_background),
    "urbanisé": hex_to_rgb(couleur_urbanise),
    "naturelle_artificielle": hex_to_rgb(couleur_nat_artificielle),
    "naturelle_existante": hex_to_rgb(couleur_nat_existante)
}
rgb_annot = {
    "urbanisé": hex_to_rgb(couleur_marqueur_urb),
    "naturelle_artificielle": hex_to_rgb(couleur_marqueur_nat_art),
    "naturelle_existante": hex_to_rgb(couleur_marqueur_nat_ex)
}

# --- ANALYSE ---
if uploaded_file and st.button("🔍 Lancer l’analyse"):

    image = Image.open(uploaded_file).convert("RGB")
    w, h = image.size
    total_pixels = w * h

    pixels = image.load()
    image_annot = image.copy()
    pixels_annot = image_annot.load()

    # Initialiser compteurs
    surfaces = {k: 0 for k in rgb_detect}

    with st.spinner("🔍 Analyse en cours..."):
        for y in range(h):
            for x in range(w):
                px = pixels[x, y]
                for key, ref_color in rgb_detect.items():
                    if couleurs_proches(px, ref_color):
                        surfaces[key] += 1
                        if key != "background":
                            pixels_annot[x, y] = rgb_annot[key]
                        break

    st.success("✅ Analyse terminée !")
    st.image(image_annot, caption="Image annotée", use_container_width=True)

    total_analyse = total_pixels - surfaces["background"]
    st.markdown("### Résultats")

    def afficher_surface(label, key):
        px = surfaces[key]
        pct = px / total_analyse * 100 if key != "background" else px / total_pixels * 100
        st.markdown(f"""**{label}** :  
- Pixels : `{px}`  
- Pourcentage : `{pct:.2f} %`""")

    afficher_surface("Background", "background")
    afficher_surface("Urbanisé", "urbanisé")
    afficher_surface("Naturelle artificielle", "naturelle_artificielle")
    afficher_surface("Naturelle existante", "naturelle_existante")

    # --- VISUALISATION ---
    st.markdown("### Répartition des surfaces")
    labels = ["Urbanisé", "Naturelle artificielle", "Naturelle existante"]
    pourcentages = [surfaces[k] / total_analyse * 100 for k in ["urbanisé", "naturelle_artificielle", "naturelle_existante"]]
    couleurs_rgb = [rgb_annot[k] for k in ["urbanisé", "naturelle_artificielle", "naturelle_existante"]]

    fig, ax = plt.subplots(figsize=(8, 2))
    start = 0
    for label, pct, color in zip(labels, pourcentages, couleurs_rgb):
        color_norm = [c / 255 for c in color]
        ax.barh(0, pct, left=start, color=color_norm, edgecolor='black')
        ax.text(start + pct / 2, 0, f"{label}\n{pct:.1f}%", ha='center', va='center', color='white', fontsize=9, fontweight='bold')
        start += pct

    ax.set_xlim(0, 100)
    ax.axis("off")
    st.pyplot(fig)
