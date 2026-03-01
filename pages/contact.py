import os

import streamlit as st

st.set_page_config(
    page_title="Syed Baqar Abbas - Profile",
    page_icon=":bust_in_silhouette:",
    layout="wide",
)

st.markdown(
    """
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=Source+Sans+3:wght@400;600&display=swap');

      .block-container {
          max-width: 1000px;
          padding-top: 1.4rem;
          padding-bottom: 1.8rem;
      }
      .profile-shell {
          border: 1px solid rgba(127, 127, 127, 0.26);
          border-radius: 22px;
          padding: 1.1rem;
          background:
            radial-gradient(circle at 100% 0%, color-mix(in srgb, var(--primary-color) 24%, transparent) 0%, transparent 35%),
            radial-gradient(circle at 0% 100%, color-mix(in srgb, var(--primary-color) 18%, transparent) 0%, transparent 30%),
            linear-gradient(130deg, var(--secondary-background-color) 0%, var(--background-color) 100%);
      }
      .intro-card {
          border: 1px solid rgba(127, 127, 127, 0.2);
          border-radius: 16px;
          padding: 1.2rem;
          background: color-mix(in srgb, var(--background-color) 86%, var(--primary-color) 14%);
      }
      .intro-title {
          margin: 0;
          font-family: "Space Grotesk", sans-serif;
          font-size: clamp(1.7rem, 3.8vw, 2.35rem);
          letter-spacing: -0.02em;
          line-height: 1.05;
      }
      .intro-role {
          margin: 0.35rem 0 0 0;
          font-family: "Source Sans 3", sans-serif;
          color: color-mix(in srgb, var(--text-color) 74%, transparent);
          font-size: 1.06rem;
      }
      .meta-row {
          margin-top: 0.95rem;
          display: flex;
          gap: 0.5rem;
          flex-wrap: wrap;
      }
      .meta-chip {
          border: 1px solid rgba(127, 127, 127, 0.26);
          border-radius: 999px;
          padding: 0.3rem 0.7rem;
          font-size: 0.85rem;
          background: color-mix(in srgb, var(--secondary-background-color) 80%, transparent);
      }
      .bio {
          margin: 1rem 0 0 0;
          font-family: "Source Sans 3", sans-serif;
          color: color-mix(in srgb, var(--text-color) 84%, transparent);
          font-size: 1rem;
          line-height: 1.5;
      }
      .social-grid {
          margin-top: 1rem;
          display: grid;
          grid-template-columns: repeat(3, minmax(0, 1fr));
          gap: 0.55rem;
      }
      .social-btn {
          text-decoration: none !important;
          border-radius: 12px;
          border: 1px solid color-mix(in srgb, var(--primary-color) 35%, rgba(127,127,127,0.22));
          background: color-mix(in srgb, var(--primary-color) 20%, var(--secondary-background-color));
          color: var(--text-color) !important;
          font-family: "Source Sans 3", sans-serif;
          font-weight: 600;
          font-size: 0.92rem;
          text-align: center;
          padding: 0.52rem 0.3rem;
          transition: transform 120ms ease, filter 120ms ease;
          display: block;
      }
      .social-btn:hover {
          transform: translateY(-1px);
          filter: brightness(1.04);
      }
      .avatar-card {
          border: 1px solid rgba(127, 127, 127, 0.2);
          border-radius: 16px;
          padding: 0.9rem;
          background: color-mix(in srgb, var(--secondary-background-color) 88%, transparent);
      }
      .avatar-caption {
          margin-top: 0.7rem;
          text-align: center;
          font-family: "Source Sans 3", sans-serif;
          color: color-mix(in srgb, var(--text-color) 72%, transparent);
          font-size: 0.9rem;
      }
      @media (max-width: 840px) {
          .social-grid {
              grid-template-columns: 1fr;
          }
      }
    </style>
    """,
    unsafe_allow_html=True,
)

github_url = "https://github.com/SyedBaqarAbbas"
linkedin_url = "https://www.linkedin.com/in/syedbaqarabbas/"
portfolio_url = "https://syed-baqar-abbas.lovable.app/"

st.markdown('<div class="profile-shell">', unsafe_allow_html=True)
left, right = st.columns([1.4, 1], gap="large")

with left:
    st.markdown(
        """
        <div class="intro-card">
          <h1 class="intro-title">Syed Baqar Abbas</h1>
          <p class="intro-role">Data Scientist</p>
          <div class="meta-row">
            <span class="meta-chip">Lahore, Pakistan</span>
            <span class="meta-chip">Open to Collaboration</span>
          </div>
          <p class="bio">
            Building practical data products with a focus on market analysis, portfolio tooling,
            and analytics that are simple to use and easy to trust.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="social-grid">
          <a class="social-btn" href="{github_url}" target="_blank">GitHub</a>
          <a class="social-btn" href="{linkedin_url}" target="_blank">LinkedIn</a>
          <a class="social-btn" href="{portfolio_url}" target="_blank">Portfolio</a>
        </div>
        """,
        unsafe_allow_html=True,
    )

with right:
    st.markdown('<div class="avatar-card">', unsafe_allow_html=True)
    st.image(
        os.path.join(os.path.abspath("."), "images", "1.png"),
        use_container_width=True,
    )
    st.markdown(
        '<p class="avatar-caption">Data, markets, and product-focused problem solving.</p>',
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)
