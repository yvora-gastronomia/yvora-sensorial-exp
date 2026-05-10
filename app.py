import json
import os
import re
import uuid
from datetime import datetime
from html import escape
from typing import Any, Dict, List, Optional, Tuple

import gspread
import pandas as pd
import streamlit as st
from google.oauth2.service_account import Credentials


APP_TITLE = "YVORA Sensorial Experience"
DEFAULT_SHEET_ID = "13dJLL4TzMFvJEjn767sDL5nuQ2JY5zJVyRyFltkD87I"

BRAND_BG = "#EFE7DD"
BRAND_BG_SOFT = "#FAF6EF"
BRAND_BLUE = "#0E2A47"
BRAND_GOLD = "#C6A96A"
BRAND_TEXT = "#47372E"

LOGO_PATHS = [
    "yvora_logo.JPG",
    "yvora_logo.jpg",
    "yvora_logo.jpeg",
    "yvora_logo.png",
    "logo.png",
    "logo.jpg",
    "assets/yvora_logo.png",
    "assets/yvora_logo.jpg",
]

st.set_page_config(page_title=APP_TITLE, layout="wide", initial_sidebar_state="collapsed")


def safe(value: Any, default: str = "") -> str:
    if value is None:
        return default
    try:
        if pd.isna(value):
            return default
    except Exception:
        pass
    text = str(value).strip()
    return text if text else default


def esc(value: Any) -> str:
    return escape(safe(value))


def is_active(value: Any) -> bool:
    return safe(value).lower() in ["1", "sim", "ativo", "true", "yes", "publicado", "live"]


def split_options(value: Any) -> List[str]:
    text = safe(value)
    return [x.strip() for x in text.split(";") if x.strip()] if text else []


def find_logo_path() -> Optional[str]:
    for path in LOGO_PATHS:
        if os.path.exists(path):
            return path
    return None


def split_story_blocks(text: str) -> List[Tuple[str, str]]:
    labels = [
        "ABERTURA",
        "BRASILIDADE",
        "PERCEPÇÃO GUIADA",
        "ENCONTRO",
        "VINHO",
        "CELEBRAÇÃO",
        "EXPERIÊNCIA",
        "CONCLUSÃO",
    ]
    pattern = r"(" + "|".join([re.escape(label) for label in labels]) + r")\s*\|"
    parts = re.split(pattern, safe(text))

    if len(parts) <= 1:
        return [("RITUAL", safe(text))]

    blocks: List[Tuple[str, str]] = []
    prefix = parts[0].strip()
    if prefix:
        blocks.append(("RITUAL", prefix))

    for i in range(1, len(parts), 2):
        title = parts[i].strip()
        body = parts[i + 1].strip() if i + 1 < len(parts) else ""
        if body:
            blocks.append((title, body))

    return blocks


def inject_css() -> None:
    st.markdown(
        f"""
<style>
[data-testid="stSidebar"],
[data-testid="collapsedControl"],
[data-testid="stHeader"],
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"],
#MainMenu,
header,
footer,
.stDeployButton {{
    display: none !important;
    visibility: hidden !important;
    height: 0 !important;
}}

html, body, [data-testid="stAppViewContainer"] {{
    background:
        radial-gradient(circle at 12% 8%, rgba(198,169,106,0.20), transparent 30%),
        radial-gradient(circle at 92% 18%, rgba(14,42,71,0.10), transparent 34%),
        linear-gradient(135deg, {BRAND_BG_SOFT} 0%, {BRAND_BG} 100%) !important;
    color: {BRAND_TEXT};
    scroll-behavior: smooth;
}}

.block-container {{
    padding-top: 1.05rem;
    padding-bottom: 2rem;
    max-width: 1180px;
}}

.yv-logo-mark {{
    width: 64px;
    height: 64px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    background: {BRAND_BLUE};
    color: {BRAND_BG_SOFT};
    font-family: Georgia, serif;
    font-size: 24px;
    letter-spacing: 1px;
}}

.yv-title {{
    margin: 0;
    color: {BRAND_BLUE};
    font-family: Georgia, 'Times New Roman', serif;
    font-size: clamp(27px, 4vw, 46px);
    line-height: 1.0;
    letter-spacing: .2px;
}}

.yv-subtitle {{
    margin-top: 7px;
    color: rgba(14,42,71,.68);
    font-size: 14px;
}}

.yv-card {{
    background: rgba(255,255,255,.72);
    border: 1px solid rgba(14,42,71,.12);
    border-radius: 30px;
    padding: clamp(20px, 4vw, 38px);
    box-shadow: 0 18px 50px rgba(14,42,71,.08);
    margin-bottom: 18px;
}}

.yv-kicker {{
    color: {BRAND_GOLD};
    font-size: 12px;
    letter-spacing: 2.25px;
    text-transform: uppercase;
    font-weight: 900;
}}

.yv-h1 {{
    font-family: Georgia, serif;
    font-size: clamp(38px, 6vw, 78px);
    line-height: .98;
    margin: 10px 0 16px;
    letter-spacing: -1.4px;
}}

.yv-h2 {{
    font-family: Georgia, serif;
    color: {BRAND_BLUE};
    font-size: clamp(25px, 4vw, 44px);
    line-height: 1.05;
    margin: 0 0 10px;
}}

.yv-muted {{
    color: rgba(71,55,46,.72);
    font-size: 15px;
    line-height: 1.56;
}}

.yv-cinema {{
    position: relative;
    border-radius: 38px;
    overflow: hidden;
    background: linear-gradient(135deg, #061626, {BRAND_BLUE});
    box-shadow: 0 30px 80px rgba(14,42,71,.28);
    margin-bottom: 18px;
    isolation: isolate;
}}

.yv-cinema:before {{
    content: "";
    position: absolute;
    inset: 0;
    background: linear-gradient(90deg, rgba(6,22,38,.97) 0%, rgba(6,22,38,.88) 48%, rgba(6,22,38,.55) 100%);
    z-index: 1;
}}

.yv-cinema-bg {{
    position: absolute;
    inset: 0;
    background-size: cover;
    background-position: center;
    transform: scale(1.06);
    filter: saturate(.92) contrast(1.02);
    opacity: .40;
    animation: slowZoom 18s ease-in-out infinite alternate;
}}

.yv-cinema-content {{
    position: relative;
    z-index: 2;
    padding: clamp(26px, 6vw, 66px);
    max-width: 1040px;
}}

.yv-orb {{
    position: absolute;
    width: 360px;
    height: 360px;
    right: -120px;
    top: -120px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(198,169,106,.32), transparent 66%);
    z-index: 2;
}}

.yv-story {{
    font-size: clamp(17px, 1.65vw, 22px);
    line-height: 1.58;
    color: rgba(250,246,239,.92);
    max-width: 1000px;
}}

.yv-white-muted {{
    color: rgba(250,246,239,.76);
    font-size: 15px;
    line-height: 1.55;
}}

.yv-overview {{
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 14px;
    margin-top: 20px;
}}

.yv-overview-card {{
    background: rgba(14,42,71,.055);
    border: 1px solid rgba(14,42,71,.10);
    border-radius: 22px;
    padding: 18px;
    min-height: 120px;
}}

.yv-overview-card b {{
    color: {BRAND_BLUE};
}}

.yv-blocks {{
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 14px;
    margin: 22px 0 18px;
}}

.yv-story-block {{
    border-radius: 24px;
    padding: 18px 20px;
    border: 1px solid rgba(250,246,239,.16);
    background: rgba(250,246,239,.09);
    color: rgba(250,246,239,.90);
    line-height: 1.55;
}}

.yv-story-block:nth-child(even) {{
    background: rgba(198,169,106,.13);
}}

.yv-story-block-title {{
    color: {BRAND_GOLD};
    letter-spacing: 1.8px;
    font-size: 12px;
    font-weight: 900;
    text-transform: uppercase;
    margin-bottom: 8px;
}}

.yv-steps {{
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 12px;
    margin-top: 18px;
}}

.yv-step {{
    background: rgba(250,246,239,.10);
    border: 1px solid rgba(250,246,239,.18);
    border-radius: 22px;
    padding: 16px;
    color: rgba(250,246,239,.88);
}}

.yv-step b {{
    color: {BRAND_GOLD};
}}

.yv-progress {{
    display: flex;
    gap: 7px;
    margin: 18px 0 22px;
    overflow: hidden;
}}

.yv-dot {{
    height: 7px;
    flex: 1;
    border-radius: 999px;
    background: rgba(14,42,71,.15);
}}

.yv-dot-on {{
    background: linear-gradient(90deg, {BRAND_GOLD}, #E6D1A0);
    box-shadow: 0 0 12px rgba(198,169,106,.45);
}}

.yv-feedback {{
    background: rgba(255,255,255,.74);
    border: 1px solid rgba(14,42,71,.10);
    border-radius: 28px;
    padding: 22px 26px;
    margin: 18px 0;
}}

.yv-feedback-title {{
    color: {BRAND_BLUE};
    font-weight: 800;
    margin-bottom: 12px;
}}

.yv-feedback-selected {{
    color: rgba(71,55,46,.72);
    font-size: 14px;
    margin-top: 8px;
}}

.yv-celebration {{
    text-align: center;
    padding: 50px 24px;
}}

.stButton > button {{
    border-radius: 999px !important;
    background: {BRAND_BLUE} !important;
    color: {BRAND_BG_SOFT} !important;
    border: 1px solid rgba(14,42,71,.2) !important;
    min-height: 2.9rem !important;
    font-weight: 900 !important;
    padding: 0 22px !important;
}}

.stTextInput input,
.stTextArea textarea {{
    border-radius: 18px !important;
    border: 1px solid rgba(14,42,71,.16) !important;
    background: rgba(255,255,255,.82) !important;
}}

button[kind="secondary"] {{
    font-size: 28px !important;
}}

@keyframes slowZoom {{
    from {{ transform: scale(1.04); }}
    to {{ transform: scale(1.14); }}
}}

@media(max-width:760px) {{
    .block-container {{
        padding-left: 1rem;
        padding-right: 1rem;
    }}

    .yv-overview,
    .yv-blocks,
    .yv-steps {{
        grid-template-columns: 1fr;
    }}

    .yv-cinema {{
        border-radius: 28px;
    }}

    .yv-cinema:before {{
        background: linear-gradient(180deg, rgba(6,22,38,.95), rgba(6,22,38,.78));
    }}
}}
</style>
""",
        unsafe_allow_html=True,
    )


@st.cache_resource(ttl=600)
def get_client():
    google_block = st.secrets.get("google", {})

    if google_block.get("service_account_json"):
        sa = json.loads(google_block["service_account_json"])
    elif "gcp_service_account" in st.secrets:
        sa = dict(st.secrets["gcp_service_account"])
    else:
        st.error("Configure a conta de serviço do Google Sheets nos secrets do Streamlit.")
        st.stop()

    if "\\n" in sa.get("private_key", "") and "\n" not in sa.get("private_key", ""):
        sa["private_key"] = sa["private_key"].replace("\\n", "\n")

    creds = Credentials.from_service_account_info(
        sa,
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ],
    )
    return gspread.authorize(creds)


@st.cache_resource(ttl=600)
def get_workbook():
    google_block = st.secrets.get("google", {})
    sheet_id = (
        google_block.get("sheet_id")
        or st.secrets.get("SPREADSHEET_ID")
        or DEFAULT_SHEET_ID
    )
    return get_client().open_by_key(sheet_id)


@st.cache_data(ttl=180)
def read_df(tab: str) -> pd.DataFrame:
    try:
        ws = get_workbook().worksheet(tab)
        return pd.DataFrame(ws.get_all_records())
    except Exception as exc:
        st.error(f"Não foi possível ler a aba '{tab}': {exc}")
        return pd.DataFrame()


def append_row(tab: str, row: Dict[str, Any]) -> None:
    ws = get_workbook().worksheet(tab)
    headers = ws.row_values(1)
    output = [row.get(h, "") for h in headers]
    ws.append_row(output, value_input_option="USER_ENTERED")


def validate_token(token: str) -> bool:
    df = read_df("tokens")

    if df.empty or "token" not in df.columns:
        return False

    df["token"] = df["token"].astype(str).str.strip()
    valid = df[df["token"] == token.strip()]

    if valid.empty:
        return False

    if "status" in valid.columns:
        return is_active(valid.iloc[0].get("status"))

    return True


def ensure_session() -> None:
    defaults = {
        "session_token": str(uuid.uuid4()),
        "authenticated": False,
        "guest_name": "",
        "guest_phone": "",
        "guest_token": "",
        "selected_experience": None,
        "step_index": 0,
        "saved_answers": set(),
        "celebrated": False,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def log_login(nome: str, telefone: str, token: str, status: str) -> None:
    try:
        append_row(
            "login_logs",
            {
                "created_at": datetime.now().isoformat(timespec="seconds"),
                "nome": nome,
                "telefone": telefone,
                "token": token,
                "status": status,
                "session_token": st.session_state.session_token,
                "user_agent": "",
            },
        )
    except Exception:
        pass


def render_header(subtitle: str = "") -> None:
    col_logo, col_text = st.columns([1, 8])

    with col_logo:
        logo_path = find_logo_path()
        if logo_path:
            st.image(logo_path, width=78)
        else:
            st.markdown('<div class="yv-logo-mark">Y</div>', unsafe_allow_html=True)

    with col_text:
        st.markdown(
            f"""
<h1 class="yv-title">{esc(APP_TITLE)}</h1>
<div class="yv-subtitle">{esc(subtitle)}</div>
""",
            unsafe_allow_html=True,
        )


def progress_strip(total: int, current: int) -> str:
    dots = []
    for i in range(total):
        cls = "yv-dot yv-dot-on" if i <= current else "yv-dot"
        dots.append(f'<div class="{cls}"></div>')
    return '<div class="yv-progress">' + "".join(dots) + "</div>"


def render_login() -> None:
    exps = read_df("experiencias")
    row = exps.iloc[0].to_dict() if not exps.empty else {}

    texto = safe(
        row.get("texto_abertura"),
        "Você foi convidado para uma experiência criada para revelar sabores que normalmente passam despercebidos.",
    )

    img = safe(row.get("imagem_capa_url"))
    bg_style = (
        f"background-image:url('{esc(img)}');"
        if img
        else "background-image:radial-gradient(circle at 70% 30%, rgba(198,169,106,.28), transparent 38%);"
    )

    st.markdown(
        f"""
<section class="yv-cinema">
  <div class="yv-cinema-bg" style="{bg_style}"></div>
  <div class="yv-orb"></div>
  <div class="yv-cinema-content">
    <div class="yv-kicker">WELCOME TO YVORA</div>
    <div class="yv-h1">Sensorial Experience</div>
    <div class="yv-story">{esc(texto)}</div>
    <br>
    <div class="yv-white-muted">Antes de iniciar, identifique-se para liberar sua jornada.</div>
  </div>
</section>
""",
        unsafe_allow_html=True,
    )

    st.markdown('<div class="yv-card">', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1.2, 1, 0.7])

    with col1:
        nome = st.text_input("Nome", placeholder="Seu nome")

    with col2:
        telefone = st.text_input("Telefone", placeholder="DDD + telefone")

    with col3:
        token = st.text_input("Token", placeholder="")

    if st.button("Vamos iniciar"):
        if not nome.strip() or not telefone.strip() or not token.strip():
            st.warning("Preencha nome, telefone e token para iniciar.")
        elif validate_token(token):
            st.session_state.authenticated = True
            st.session_state.guest_name = nome.strip()
            st.session_state.guest_phone = telefone.strip()
            st.session_state.guest_token = token.strip()

            log_login(nome.strip(), telefone.strip(), token.strip(), "autorizado")
            st.rerun()
        else:
            log_login(nome.strip(), telefone.strip(), token.strip(), "negado")
            st.error("Token inválido ou inativo.")

    st.markdown("</div>", unsafe_allow_html=True)


def active_experiences() -> pd.DataFrame:
    df = read_df("experiencias")

    if df.empty:
        return df

    if "status" in df.columns:
        df = df[df["status"].apply(is_active)].copy()

    df["_ordem"] = pd.to_numeric(df.get("ordem", 0), errors="coerce").fillna(9999)
    return df.sort_values("_ordem")


def render_landing() -> None:
    exps = active_experiences()
    render_header(f"Bem-vindo, {st.session_state.guest_name}. Escolha a sessão para iniciar.")

    if exps.empty:
        st.info("Nenhuma experiência disponível.")
        return

    overview = """
<div class="yv-overview">
  <div class="yv-overview-card"><b>Jornada 1</b><br>Prosciutto Crudo, Parmesão 24 meses e Taça 2. Gordura aromática, cristais e umami.</div>
  <div class="yv-overview-card"><b>Jornada 2</b><br>Pastrami, Canastra curado e Taça 1. Fumaça, especiarias, acidez e limpeza de paladar.</div>
  <div class="yv-overview-card"><b>Jornada 3</b><br>Copa de Lombo, Queijo Tulha e Taça 1. Cura, gordura longa, cristais e persistência.</div>
  <div class="yv-overview-card"><b>Jornada 4</b><br>Carpaccio de Lagarto, Queijo Azul e Taça 2. Delicadeza, fungos nobres e fruta do vinho.</div>
</div>
"""

    for _, r in exps.iterrows():
        row = r.to_dict()
        exp_id = safe(row.get("experience_id"))

        st.markdown(
            f"""
<div class="yv-card">
  <div class="yv-kicker">Experiência disponível</div>
  <div class="yv-h2">{esc(row.get("nome_sessao", APP_TITLE))}</div>
  <div class="yv-muted"><b>{esc(row.get("subtitulo"))}</b><br>{esc(row.get("descricao_card"))}</div>
  {overview}
</div>
""",
            unsafe_allow_html=True,
        )

        if st.button("Entrar na degustação", key=f"start_{exp_id}"):
            st.session_state.selected_experience = exp_id
            st.session_state.step_index = 0
            st.session_state.celebrated = False
            st.rerun()


def current_steps(experience_id: str) -> pd.DataFrame:
    df = read_df("jornada")

    if df.empty:
        return df

    df["experience_id"] = df["experience_id"].astype(str).str.strip()
    df = df[df["experience_id"] == experience_id].copy()

    if "ativo" in df.columns:
        df = df[df["ativo"].apply(is_active)]

    df["ordem"] = pd.to_numeric(df.get("ordem", 0), errors="coerce").fillna(0).astype(int)
    return df.sort_values("ordem").reset_index(drop=True)


def render_journey(row: Dict[str, Any], idx: int, total: int) -> None:
    st.markdown('<script>window.scrollTo(0,0);</script>', unsafe_allow_html=True)
    st.markdown(progress_strip(total, idx), unsafe_allow_html=True)

    img = safe(row.get("imagem_url"))
    bg_style = (
        f"background-image:url('{esc(img)}');"
        if img
        else "background-image:radial-gradient(circle at 70% 30%, rgba(198,169,106,.28), transparent 38%);"
    )

    block_html = ""
    for title, body in split_story_blocks(safe(row.get("texto_principal"))):
        block_html += (
            '<div class="yv-story-block">'
            f'<div class="yv-story-block-title">{esc(title)}</div>'
            f'<div>{esc(body)}</div>'
            "</div>"
        )

    step_html = (
        '<div class="yv-steps">'
        f'<div class="yv-step"><b>1. Carne</b><br>{esc(row.get("carne"))}</div>'
        f'<div class="yv-step"><b>2. Queijo</b><br>{esc(row.get("queijo"))}</div>'
        '<div class="yv-step"><b>3. Juntos</b><br>Prove a dupla na ordem indicada.</div>'
        f'<div class="yv-step"><b>4. Vinho</b><br>{esc(row.get("vinho"))}</div>'
        "</div>"
    )

    html = f"""
<section class="yv-cinema">
  <div class="yv-cinema-bg" style="{bg_style}"></div>
  <div class="yv-orb"></div>
  <div class="yv-cinema-content">
    <div class="yv-kicker">{esc(row.get("conceito_sensorial", APP_TITLE))}</div>
    <div class="yv-h1">{esc(row.get("titulo_tela"))}</div>
    <div class="yv-story"><b>{esc(row.get("subtitulo_tela"))}</b></div>
    <div class="yv-blocks">{block_html}</div>
    {step_html}
    <br>
    <div class="yv-white-muted">{esc(row.get("instrucao_cliente"))}</div>
  </div>
</section>
"""
    st.markdown(html, unsafe_allow_html=True)


def render_final(row: Dict[str, Any], idx: int, total: int) -> Tuple[str, str]:
    render_journey(row, idx, total)

    options = split_options(row.get("opcoes_feedback"))
    escolha = st.selectbox("Qual jornada mais marcou sua experiência?", options) if options else ""
    comentario = st.text_area("Comentário opcional", placeholder="Conte o que mais chamou sua atenção")
    return escolha, comentario


def save_feedback(row: Dict[str, Any], resposta: str, comentario: str = "") -> None:
    if not resposta and not comentario:
        return

    etapa_id = safe(row.get("etapa_id"))
    key = f"{etapa_id}:{resposta}:{comentario}"

    if key in st.session_state.saved_answers:
        return

    append_row(
        "feedbacks",
        {
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "experience_id": safe(row.get("experience_id")),
            "etapa_id": etapa_id,
            "jornada_numero": safe(row.get("jornada_numero")),
            "nome_jornada": safe(row.get("nome_jornada")),
            "tipo_tela": safe(row.get("tipo_tela")),
            "session_token": st.session_state.session_token,
            "nome": st.session_state.guest_name,
            "telefone": st.session_state.guest_phone,
            "token": st.session_state.guest_token,
            "resposta": resposta,
            "comentario_final": comentario,
            "user_agent": "",
        },
    )

    st.session_state.saved_answers.add(key)


def render_optional_feedback(row: Dict[str, Any]) -> str:
    etapa_id = safe(row.get("etapa_id"))
    key = f"choice_{etapa_id}"

    if key not in st.session_state:
        st.session_state[key] = ""

    st.markdown(
        """
<div class="yv-feedback">
  <div class="yv-feedback-title">A jornada funcionou para você?</div>
</div>
""",
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([0.15, 0.15, 1])

    with col1:
        if st.button("👍", key=f"up_{etapa_id}"):
            st.session_state[key] = "👍"

    with col2:
        if st.button("👎", key=f"down_{etapa_id}"):
            st.session_state[key] = "👎"

    if st.session_state[key]:
        st.markdown(
            f'<div class="yv-feedback-selected">Feedback selecionado: {esc(st.session_state[key])}</div>',
            unsafe_allow_html=True,
        )

    return st.session_state[key]


def render_celebration() -> None:
    render_header("Degustação concluída")

    st.markdown(
        """
<section class="yv-cinema">
  <div class="yv-cinema-bg" style="background-image:radial-gradient(circle at 70% 30%, rgba(198,169,106,.34), transparent 38%);"></div>
  <div class="yv-orb"></div>
  <div class="yv-cinema-content yv-celebration">
    <div class="yv-kicker">YVORA</div>
    <div class="yv-h1">Degustação concluída</div>
    <div class="yv-story">
      Obrigado por viver esta experiência. Você não apenas provou carnes, queijos e vinhos:
      participou de uma leitura guiada de sabor criada para revelar como a culinária brasileira
      contemporânea pode ganhar novas camadas quando encontra técnica, vinho e percepção.
    </div>
    <br>
    <div class="yv-white-muted">
      Sua jornada ajuda a construir a inteligência sensorial da YVORA.
    </div>
  </div>
</section>
""",
        unsafe_allow_html=True,
    )

    if st.button("Voltar ao início"):
        st.session_state.celebrated = False
        st.session_state.selected_experience = None
        st.session_state.step_index = 0
        st.rerun()


def render_experience(experience_id: str) -> None:
    if st.session_state.celebrated:
        render_celebration()
        return

    steps = current_steps(experience_id)

    if steps.empty:
        st.warning("Experiência não encontrada ou sem etapas ativas.")
        return

    idx = max(0, min(st.session_state.step_index, len(steps) - 1))
    row = steps.iloc[idx].to_dict()

    render_header("Siga o ritual. Prove, combine, depois deixe o vinho transformar.")

    tipo = safe(row.get("tipo_tela"))

    if tipo == "encerramento":
        escolha, comentario = render_final(row, idx, len(steps))
    else:
        render_journey(row, idx, len(steps))
        escolha = render_optional_feedback(row)
        comentario = ""

    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        if idx > 0 and st.button("Retornar"):
            st.session_state.step_index = idx - 1
            st.rerun()

    with col2:
        label = safe(row.get("botao_texto"), "Avançar")

        if st.button(label):
            if tipo == "encerramento":
                save_feedback(row, escolha, comentario)
                st.session_state.celebrated = True
                st.rerun()
            else:
                save_feedback(row, escolha)

                if idx < len(steps) - 1:
                    st.session_state.step_index = idx + 1
                    st.rerun()

    with col3:
        if st.button("Voltar ao início"):
            st.session_state.selected_experience = None
            st.session_state.step_index = 0
            st.rerun()


ensure_session()
inject_css()

query_params = st.query_params

if query_params.get("experience") and not st.session_state.selected_experience:
    st.session_state.selected_experience = query_params.get("experience")

if not st.session_state.authenticated:
    render_login()
elif st.session_state.selected_experience:
    render_experience(st.session_state.selected_experience)
else:
    render_landing()
