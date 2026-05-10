import json
import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import gspread
import pandas as pd
import streamlit as st
from google.oauth2.service_account import Credentials

APP_TITLE = "YVORA Sensorial Experience"
BRAND_BG = "#EFE7DD"
BRAND_BG_SOFT = "#FAF6EF"
BRAND_BLUE = "#0E2A47"
BRAND_GOLD = "#C6A96A"
BRAND_TEXT = "#47372E"
BRAND_LINE = "#D7CFC3"
LOGO_PATHS = ["yvora_logo.png", "yvora_logo.jpg", "yvora_logo.JPG", "logo.png", "assets/yvora_logo.png"]
DEFAULT_SHEET_ID = "13dJLL4TzMFvJEjn767sDL5nuQ2JY5zJVyRyFltkD87I"

st.set_page_config(page_title=APP_TITLE, layout="wide", initial_sidebar_state="collapsed")


def find_logo_path() -> Optional[str]:
    for path in LOGO_PATHS:
        if os.path.exists(path):
            return path
    return None


def safe(value: Any, default: str = "") -> str:
    if value is None:
        return default
    try:
        if pd.isna(value):
            return default
    except Exception:
        pass
    return str(value).strip()


def is_active(value: Any) -> bool:
    text = safe(value).lower()
    return text in ["1", "sim", "ativo", "true", "yes", "publicado", "live", ""]


def split_options(value: Any) -> List[str]:
    text = safe(value)
    if not text:
        return []
    return [x.strip() for x in text.split(";") if x.strip()]


def inject_css() -> None:
    st.markdown(
        f"""
        <style>
        [data-testid="stSidebar"], [data-testid="collapsedControl"], [data-testid="stHeader"],
        [data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"],
        #MainMenu, header, footer, .stDeployButton {{
            display:none !important; visibility:hidden !important; height:0 !important;
        }}
        html, body, [data-testid="stAppViewContainer"] {{
            background:
                radial-gradient(circle at 12% 8%, rgba(198,169,106,0.20), transparent 30%),
                radial-gradient(circle at 92% 18%, rgba(14,42,71,0.10), transparent 34%),
                linear-gradient(135deg, {BRAND_BG_SOFT} 0%, {BRAND_BG} 100%) !important;
            color:{BRAND_TEXT};
        }}
        .block-container {{ padding-top:1.1rem; padding-bottom:2rem; max-width:1180px; }}
        .yv-top {{ display:flex; align-items:center; gap:16px; margin-bottom:18px; }}
        .yv-logo-mark {{ width:58px; height:58px; border-radius:50%; display:flex; align-items:center; justify-content:center; background:{BRAND_BLUE}; color:{BRAND_BG_SOFT}; font-family:Georgia, serif; font-size:23px; letter-spacing:1px; }}
        .yv-title {{ margin:0; color:{BRAND_BLUE}; font-family:Georgia, 'Times New Roman', serif; font-size:clamp(26px, 4vw, 44px); line-height:1.0; letter-spacing:.3px; }}
        .yv-subtitle {{ margin-top:6px; color:rgba(14,42,71,.68); font-size:14px; }}
        .yv-card {{ background:rgba(255,255,255,.70); border:1px solid rgba(14,42,71,.12); border-radius:30px; padding:clamp(20px, 4vw, 38px); box-shadow:0 18px 50px rgba(14,42,71,.08); margin-bottom:18px; overflow:hidden; }}
        .yv-session-list {{ display:grid; grid-template-columns:repeat(auto-fit, minmax(280px,1fr)); gap:20px; margin-top:24px; }}
        .yv-session-card {{ position:relative; min-height:260px; overflow:hidden; border-radius:32px; padding:28px; background:rgba(255,255,255,.72); border:1px solid rgba(14,42,71,.12); box-shadow:0 18px 50px rgba(14,42,71,.08); }}
        .yv-session-card:hover {{ transform:translateY(-3px); box-shadow:0 24px 70px rgba(14,42,71,.15); transition:.35s ease; }}
        .yv-session-cover {{ position:absolute; inset:0; background-size:cover; background-position:center; opacity:.23; transform:scale(1.05); }}
        .yv-session-content {{ position:relative; z-index:2; }}
        .yv-kicker {{ color:{BRAND_GOLD}; font-size:12px; letter-spacing:2.2px; text-transform:uppercase; font-weight:800; }}
        .yv-h1 {{ font-family:Georgia, serif; font-size:clamp(40px, 7vw, 88px); line-height:.94; margin:10px 0 16px; letter-spacing:-1.6px; }}
        .yv-h2 {{ font-family:Georgia, serif; color:{BRAND_BLUE}; font-size:clamp(24px, 4vw, 42px); line-height:1.05; margin:0 0 10px; }}
        .yv-muted {{ color:rgba(71,55,46,.70); font-size:15px; line-height:1.55; }}
        .yv-pill {{ display:inline-flex; align-items:center; justify-content:center; padding:7px 13px; border-radius:999px; background:rgba(14,42,71,.08); color:{BRAND_BLUE}; font-size:12px; font-weight:800; border:1px solid rgba(14,42,71,.08); margin:3px 5px 3px 0; }}
        .yv-cinema {{ position:relative; min-height:68vh; border-radius:38px; overflow:hidden; background:linear-gradient(135deg, #061626, {BRAND_BLUE}); box-shadow:0 30px 80px rgba(14,42,71,.28); margin-bottom:18px; isolation:isolate; }}
        .yv-cinema:before {{ content:""; position:absolute; inset:0; background:linear-gradient(90deg, rgba(6,22,38,.96) 0%, rgba(6,22,38,.78) 42%, rgba(6,22,38,.18) 100%); z-index:1; }}
        .yv-cinema-bg {{ position:absolute; inset:0; background-size:cover; background-position:center; transform:scale(1.06); filter:saturate(.92) contrast(1.02); opacity:.60; animation: slowZoom 18s ease-in-out infinite alternate; }}
        .yv-cinema-content {{ position:relative; z-index:2; padding:clamp(28px, 7vw, 76px); max-width:840px; }}
        .yv-orb {{ position:absolute; width:360px; height:360px; right:-120px; top:-120px; border-radius:50%; background:radial-gradient(circle, rgba(198,169,106,.32), transparent 66%); z-index:2; animation: floatOrb 8s ease-in-out infinite alternate; }}
        .yv-story {{ font-size:clamp(18px, 2.2vw, 25px); line-height:1.62; color:rgba(250,246,239,.92); max-width:780px; }}
        .yv-white-muted {{ color:rgba(250,246,239,.74); font-size:15px; line-height:1.55; }}
        .yv-light-story {{ font-size:clamp(17px, 2vw, 22px); line-height:1.62; color:{BRAND_TEXT}; }}
        .yv-grid {{ display:grid; grid-template-columns:repeat(3, minmax(0,1fr)); gap:14px; margin:18px 0; }}
        .yv-mini {{ background:rgba(255,255,255,.58); border:1px solid rgba(14,42,71,.1); border-radius:22px; padding:18px; box-shadow:0 12px 28px rgba(14,42,71,.05); }}
        .yv-mini b {{ color:{BRAND_BLUE}; }}
        .yv-progress {{ display:flex; gap:7px; margin:18px 0 22px; overflow:hidden; }}
        .yv-dot {{ height:7px; flex:1; border-radius:999px; background:rgba(14,42,71,.15); }}
        .yv-dot-on {{ background:linear-gradient(90deg, {BRAND_GOLD}, #E6D1A0); box-shadow:0 0 12px rgba(198,169,106,.45); }}
        .yv-reveal {{ animation: revealUp .9s cubic-bezier(.2,.8,.2,1) both; }}
        .yv-delay-1 {{ animation-delay:.12s; }} .yv-delay-2 {{ animation-delay:.24s; }} .yv-delay-3 {{ animation-delay:.36s; }}
        .stButton > button {{ border-radius:999px !important; background:{BRAND_BLUE} !important; color:{BRAND_BG_SOFT} !important; border:1px solid rgba(14,42,71,.2) !important; min-height:2.85rem !important; font-weight:800 !important; padding:0 22px !important; }}
        .stTextInput input, .stTextArea textarea {{ border-radius:18px !important; border:1px solid rgba(14,42,71,.16) !important; background:rgba(255,255,255,.78) !important; }}
        div[data-testid="stRadio"] label {{ color:{BRAND_TEXT} !important; }}
        @keyframes revealUp {{ from {{ opacity:0; transform:translateY(22px); filter:blur(8px); }} to {{ opacity:1; transform:translateY(0); filter:blur(0); }} }}
        @keyframes slowZoom {{ from {{ transform:scale(1.04); }} to {{ transform:scale(1.14); }} }}
        @keyframes floatOrb {{ from {{ transform:translateY(0); opacity:.7; }} to {{ transform:translateY(28px); opacity:1; }} }}
        @media(max-width:760px) {{
            .block-container {{ padding-left:1rem; padding-right:1rem; }}
            .yv-grid {{ grid-template-columns:1fr; }}
            .yv-cinema {{ min-height:72vh; border-radius:28px; }}
            .yv-cinema:before {{ background:linear-gradient(180deg, rgba(6,22,38,.95), rgba(6,22,38,.72)); }}
            .yv-top {{ gap:12px; }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_resource(ttl=300)
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

    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(sa, scopes=scopes)
    return gspread.authorize(creds)


@st.cache_resource(ttl=300)
def get_workbook():
    google_block = st.secrets.get("google", {})
    sheet_id = google_block.get("sheet_id") or st.secrets.get("SPREADSHEET_ID") or DEFAULT_SHEET_ID
    return get_client().open_by_key(sheet_id)


@st.cache_data(ttl=10)
def read_df(tab: str) -> pd.DataFrame:
    try:
        ws = get_workbook().worksheet(tab)
        values = ws.get_all_records()
        return pd.DataFrame(values)
    except Exception as exc:
        st.error(f"Não foi possível ler a aba '{tab}': {exc}")
        return pd.DataFrame()


def append_feedback(row: Dict[str, Any]) -> None:
    try:
        ws = get_workbook().worksheet("feedbacks")
        headers = ws.row_values(1)
        output = [row.get(h, "") for h in headers]
        ws.append_row(output, value_input_option="USER_ENTERED")
    except Exception as exc:
        st.warning(f"Não foi possível registrar o feedback: {exc}")


def ensure_session() -> None:
    if "session_token" not in st.session_state:
        st.session_state.session_token = str(uuid.uuid4())
    if "step_index" not in st.session_state:
        st.session_state.step_index = 0
    if "selected_experience" not in st.session_state:
        st.session_state.selected_experience = None
    if "saved_answers" not in st.session_state:
        st.session_state.saved_answers = set()


def render_header(subtitle: str = "") -> None:
    logo_path = find_logo_path()
    col_logo, col_text = st.columns([1, 8])
    with col_logo:
        if logo_path:
            st.image(logo_path, width=82)
        else:
            st.markdown('<div class="yv-logo-mark">Y</div>', unsafe_allow_html=True)
    with col_text:
        st.markdown(f'<h1 class="yv-title">{APP_TITLE}</h1><div class="yv-subtitle">{subtitle}</div>', unsafe_allow_html=True)


def progress_strip(total: int, current: int) -> str:
    dots = []
    for i in range(total):
        cls = "yv-dot yv-dot-on" if i <= current else "yv-dot"
        dots.append(f'<div class="{cls}"></div>')
    return '<div class="yv-progress">' + ''.join(dots) + '</div>'


def render_landing() -> None:
    exps = read_df("experiencias")
    if exps.empty:
        st.info("Nenhuma experiência disponível.")
        return

    if "status" in exps.columns:
        exps = exps[exps["status"].apply(is_active)].copy()
    if "ordem" in exps.columns:
        exps["_ordem"] = pd.to_numeric(exps["ordem"], errors="coerce").fillna(9999)
        exps = exps.sort_values("_ordem")

    render_header("Escolha a experiência que você recebeu e inicie sua jornada.")

    st.markdown('<div class="yv-session-list">', unsafe_allow_html=True)
    for _, r in exps.iterrows():
        row = r.to_dict()
        exp_id = safe(row.get("experience_id"))
        nome = safe(row.get("nome_sessao"), APP_TITLE)
        subtitulo = safe(row.get("subtitulo"))
        desc = safe(row.get("descricao_card"))
        img = safe(row.get("imagem_capa_url"))
        cover = f'<div class="yv-session-cover" style="background-image:url({img});"></div>' if img else ""
        st.markdown(
            f"""
            <div class="yv-session-card yv-reveal">
                {cover}
                <div class="yv-session-content">
                    <div class="yv-kicker">Experiência disponível</div>
                    <div class="yv-h2">{nome}</div>
                    <div class="yv-muted"><b>{subtitulo}</b><br>{desc}</div>
                    <br><span class="yv-pill">Sensorial</span><span class="yv-pill">Carnes & Queijos</span><span class="yv-pill">Vinhos</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button(safe(row.get("botao_inicio"), "Iniciar experiência"), key=f"start_{exp_id}"):
            st.session_state.selected_experience = exp_id
            st.session_state.step_index = 0
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)


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


def render_step(row: Dict[str, Any], step_index: int, total_steps: int) -> None:
    tipo = safe(row.get("tipo_tela"))
    transicao = safe(row.get("transicao"), "cinema")
    titulo = safe(row.get("titulo_tela"), "YVORA Sensorial Experience")
    subtitulo = safe(row.get("subtitulo_tela"))
    texto = safe(row.get("texto_principal"))
    instrucao = safe(row.get("instrucao_cliente"))
    img = safe(row.get("imagem_url"))
    conceito = safe(row.get("conceito_sensorial"))
    carne = safe(row.get("carne"))
    queijo = safe(row.get("queijo"))
    vinho = safe(row.get("vinho"))
    perfil_vinho = safe(row.get("perfil_vinho"))

    st.markdown(progress_strip(total_steps, step_index), unsafe_allow_html=True)

    dark_mode = transicao in ["cinema", "dark", "gold"] or tipo in ["abertura", "intro", "troca_vinho", "encerramento"]

    if dark_mode:
        bg_style = f"background-image:url('{img}');" if img else "background-image:radial-gradient(circle at 70% 30%, rgba(198,169,106,.28), transparent 38%);"
        st.markdown(
            f"""
            <section class="yv-cinema">
                <div class="yv-cinema-bg" style="{bg_style}"></div>
                <div class="yv-orb"></div>
                <div class="yv-cinema-content">
                    <div class="yv-kicker yv-reveal">{conceito or APP_TITLE}</div>
                    <div class="yv-h1 yv-reveal yv-delay-1">{titulo}</div>
                    <div class="yv-story yv-reveal yv-delay-2"><b>{subtitulo}</b></div>
                    <br>
                    <div class="yv-story yv-reveal yv-delay-3">{texto}</div>
                    <br>
                    <div class="yv-white-muted yv-reveal yv-delay-3">{instrucao}</div>
                </div>
            </section>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""
            <div class="yv-card yv-reveal">
                <div class="yv-kicker">{conceito or APP_TITLE}</div>
                <div class="yv-h2">{titulo}</div>
                <div class="yv-muted"><b>{subtitulo}</b></div>
                <br>
                <div class="yv-light-story">{texto}</div>
                <br>
                <div class="yv-pill">{instrucao}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    details = []
    if carne:
        details.append(("Carne", carne))
    if queijo:
        details.append(("Queijo", queijo))
    if vinho:
        details.append(("Vinho", vinho))
    if perfil_vinho:
        details.append(("Perfil", perfil_vinho))
    if details:
        cards = ''.join([f'<div class="yv-mini"><b>{k}</b><br><span class="yv-muted">{v}</span></div>' for k, v in details])
        st.markdown(f'<div class="yv-grid">{cards}</div>', unsafe_allow_html=True)


def render_feedback(row: Dict[str, Any]) -> Optional[str]:
    pergunta = safe(row.get("pergunta_feedback"))
    options = split_options(row.get("opcoes_feedback"))
    if not pergunta or not options:
        return None

    etapa_id = safe(row.get("etapa_id"))
    st.markdown(f'<div class="yv-card"><div class="yv-h2">{pergunta}</div></div>', unsafe_allow_html=True)
    resposta = st.radio("Selecione uma opção", options, key=f"radio_{etapa_id}", label_visibility="collapsed")
    return resposta


def save_step_feedback(row: Dict[str, Any], resposta: str, telefone: str = "", comentario: str = "") -> None:
    etapa_id = safe(row.get("etapa_id"))
    dedupe_key = f"{etapa_id}:{resposta}:{telefone}:{comentario}"
    if dedupe_key in st.session_state.saved_answers:
        return

    output = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "experience_id": safe(row.get("experience_id")),
        "etapa_id": etapa_id,
        "jornada_numero": safe(row.get("jornada_numero")),
        "nome_jornada": safe(row.get("nome_jornada")),
        "tipo_tela": safe(row.get("tipo_tela")),
        "session_token": st.session_state.session_token,
        "resposta": resposta,
        "telefone": telefone,
        "comentario_final": comentario,
        "user_agent": "",
    }
    append_feedback(output)
    st.session_state.saved_answers.add(dedupe_key)


def render_experience(experience_id: str) -> None:
    steps = current_steps(experience_id)
    if steps.empty:
        st.warning("Experiência não encontrada ou sem etapas ativas.")
        if st.button("Voltar"):
            st.session_state.selected_experience = None
            st.rerun()
        return

    idx = max(0, min(st.session_state.step_index, len(steps) - 1))
    row = steps.iloc[idx].to_dict()

    render_header("Siga no seu ritmo. Cada celular avança de forma independente.")
    render_step(row, idx, len(steps))

    resposta = render_feedback(row)
    tipo = safe(row.get("tipo_tela"))

    if tipo == "encerramento":
        st.markdown('<div class="yv-card">', unsafe_allow_html=True)
        telefone = st.text_input("Telefone opcional", placeholder="Digite seu telefone se quiser receber novidades")
        comentario = st.text_area("Comentário opcional", placeholder="Conte o que mais chamou sua atenção")
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        telefone = ""
        comentario = ""

    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if idx > 0 and st.button("Voltar"):
            st.session_state.step_index = idx - 1
            st.rerun()
    with col2:
        btn_label = safe(row.get("botao_texto"), "Próximo")
        if st.button(btn_label):
            if resposta:
                save_step_feedback(row, resposta, telefone, comentario)
            elif tipo == "encerramento" and (telefone or comentario):
                save_step_feedback(row, "feedback_final", telefone, comentario)
            if idx < len(steps) - 1:
                st.session_state.step_index = idx + 1
                st.rerun()
            else:
                st.success("Obrigado por viver a experiência YVORA.")
    with col3:
        if st.button("Reiniciar"):
            st.session_state.step_index = 0
            st.rerun()


ensure_session()
inject_css()

query_params = st.query_params
if query_params.get("experience") and not st.session_state.selected_experience:
    st.session_state.selected_experience = query_params.get("experience")

if st.session_state.selected_experience:
    render_experience(st.session_state.selected_experience)
else:
    render_landing()
