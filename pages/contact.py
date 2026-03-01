import os

import streamlit as st

st.set_page_config(page_title="Syed Baqar Abbas - Profile", layout="centered")

st.markdown(
    """
    <style>
      .block-container {
          padding-top: 1.3rem;
      }
      .profile-shell {
          border: 1px solid rgba(127, 127, 127, 0.28);
          border-radius: 16px;
          padding: 1rem 1.1rem;
          background: linear-gradient(
            125deg,
            var(--secondary-background-color) 0%,
            var(--background-color) 100%
          );
          color: var(--text-color);
      }
      .link-pill {
          padding: 0.4rem 0.7rem;
          border-radius: 999px;
          background: var(--secondary-background-color);
          border: 1px solid rgba(127, 127, 127, 0.25);
          display: inline-block;
          margin-right: 0.35rem;
          color: var(--text-color) !important;
          text-decoration: none;
      }
      .link-pill:visited,
      .link-pill:hover,
      .link-pill:active {
          color: var(--text-color) !important;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="profile-shell">', unsafe_allow_html=True)

left, right = st.columns([1.15, 1], gap="large")

with right:
    st.image(os.path.join(os.path.abspath("."), "images", "1.png"), width=220)

with left:
    st.title("Syed Baqar Abbas")
    st.subheader("Data Scientist")
    st.caption("Lahore, Pakistan")
    st.write("Learn more through the links below.")

    github_url = "https://github.com/SyedBaqarAbbas"
    linkedin_url = "https://www.linkedin.com/in/syedbaqarabbas/"
    portfolio_url = "https://syed-baqar-abbas.lovable.app/"

    st.markdown(
        f'<a class="link-pill" href="{github_url}" target="_blank">GitHub</a>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<a class="link-pill" href="{linkedin_url}" target="_blank">LinkedIn</a>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<a class="link-pill" href="{portfolio_url}" target="_blank">Portfolio</a>',
        unsafe_allow_html=True,
    )

st.markdown("</div>", unsafe_allow_html=True)
