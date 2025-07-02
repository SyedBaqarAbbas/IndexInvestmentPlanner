import os
import streamlit as st

# Page configuration
st.set_page_config(page_title="Syed Baqar Abbas - Profile", layout="centered")

# --- AVATAR ---
# Two buttons side by side for GitHub and LinkedIn
section1, section2 = st.columns([1, 1], gap="medium")

with section2:
    # col1, col2, col3 = st.columns([1, 1, 1], gap="medium")
    # with col2:
    st.image(os.path.join(os.path.abspath("."),"images", "1.png"), width=200)

with section1:
    # --- NAME & TITLE ---
    st.title("Syed Baqar Abbas")
    st.subheader("Data Scientist")
    st.markdown("*Based in Lahore, Pakistan*")

    # --- DESCRIPTION ---
    description = (
        "Click the links below to learn more about me:"
    )
    st.write(description)

    # --- SOCIAL BUTTONS ---
    # Replace URLs with your actual links
    github_url = "https://github.com/SyedBaqarAbbas"
    linkedin_url = "https://www.linkedin.com/in/syedbaqarabbas/"
    portfolio_url = "https://syed-baqar-abbas.lovable.app/"

    st.markdown(f"🐙 [GitHub]({github_url})")
    st.markdown(f"🔗 [LinkedIn]({linkedin_url})")
    st.markdown(f"🌐 [Portfolio]({portfolio_url})")
