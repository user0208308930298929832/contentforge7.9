import streamlit as st
import pandas as pd
from datetime import datetime, date, time, timedelta
from dateutil.relativedelta import relativedelta
import uuid
import json

st.set_page_config(page_title="ContentForge 7.9.3 • Weekly Planner", layout="wide")

# ----------------------------- THEME BASE (cores legíveis) -----------------------------
BASE_CSS = """
<style>
:root { --bg:#0f1115; --card:#171923; --text:#e6e8ee; --muted:#a0a7b4; --accent:#82cfff; --ok:#22c55e; --warn:#f59e0b; --bad:#ef4444; }
html,body,.stApp{background:var(--bg); color:var(--text);}
section[data-testid="stSidebar"] {background: #11131a;}
.block-container {padding-top:1.2rem; padding-bottom:2rem;}
.card {background:var(--card); border:1px solid #202536; border-radius:14px; padding:16px;}
.badge {display:inline-flex; gap:8px; align-items:center; font-size:0.85rem; padding:6px 10px; border-radius:999px; background:#102a43; color:#b3e1ff; border:1px solid #1e3a5f;}
.kpi {display:grid; grid-template-columns:repeat(3,1fr); gap:12px;}
.kpi>div{background:#121520;border:1px solid #22263a;border-radius:12px;padding:12px;text-align:center}
.kpi .big{font-size:1.25rem;font-weight:700}
.card h3{margin:0 0 8px 0}
.card small, .muted{color:var(--muted)}
.btn-ghost {border:1px dashed #2a3147; padding:8px 12px; border-radius:10px;}
.ev {background:#10141f; border:1px solid #22263a; border-radius:12px; padding:10px; margin-bottom:8px}
.ev strong{display:block; margin-bottom:4px}
.reco {background:#132f18; color:#b7f7c2; border:1px solid #1e4d26}
.lock {opacity:.55; filter:grayscale(25%)}
.grid7 {display:grid; grid-template-columns:repeat(7,1fr); gap:10px;}
.grid7 .day {background:var(--card); border:1px solid #202536; border-radius:14px; padding:10px; min-height:160px}
.grid7 .day h4{margin:.25rem 0 .5rem 0; font-size:0.95rem}
.footer-actions{display:flex; gap:10px; flex-wrap:wrap}
</style>
"""
st.markdown(BASE_CSS, unsafe_allow_html=True)

# ----------------------------- PLANS & LIMITS -----------------------------
PLANS = {
    "Starter": {"max_add_per_day": 5, "performance": False, "metrics": False, "export": True},
    "Pro":     {"max_add_per_day": 30, "performance": True,  "metrics": True,  "export": True},
    "Pro+":    {"max_add_per_day": 200, "performance": True,  "metrics": True,  "export": True},
}

# ----------------------------- STATE INIT -----------------------------
def init_state():
    ss = st.session_state
    ss.setdefault("user", {
        "brand": "Minha Marca",
        "niche": "Moda",
        "tone": "profissional",
        "plan": "Starter",
        "text_credits": 100,       # apenas contador simbólico aqui
        "image_credits": 0,
        "month_additions": 0,      # total do mês (visível no sidebar)
        "today_additions": 0,      # total do dia (limites por plano)
        "followers": 0, "engagement": 0.0, "reach": 0
    })
    ss.setdefault("planner", [])          # eventos futuros/planeados
    ss.setdefault("done", [])             # eventos concluídos
    ss.setdefault("evento_selecionado", None)
    ss.setdefault("week_anchor", date.today())  # âncora da semana a mostrar
    ss.setdefault("last_credit_snapshot", {"text_credits": ss["user"]["text_credits"]})

init_state()

# ----------------------------- UTILS -----------------------------
def unique_id() -> str:
    return uuid.uuid4().hex[:12]

def week_bounds(anchor: date):
    # segunda-feira como início
    start = anchor - timedelta(days=anchor.weekday())
    end = start + timedelta(days=6)
    return start, end

def events_in_week(start: date, end: date, events):
    out = []
    for ev in events:
        try:
            d = datetime.strptime(ev["day"], "%Y-%m-%d").date()
        except Exception:
            # fallback para "YYYY/MM/DD"
            d = datetime.strptime(ev["day"].replace("/","-"), "%Y-%m-%d").date()
        if start <= d <= end:
            out.append(ev)
    return out

def safe_rerun():
    # evitar experimental_rerun
    st.rerun()

def debit_text_credit(n=1):
    # debita n créditos de texto imediatamente ao adicionar ao planner
    u = st.session_state["user"]
    u["text_credits"] = max(0, u["text_credits"] - n)

def can_add_today():
    plan = st.session_state["user"]["plan"]
    limit = PLANS[plan]["max_add_per_day"]
    return st.session_state["user"]["today_additions"] < limit

def register_addition():
    st.session_state["user"]["today_additions"] += 1
    st.session_state["user"]["month_additions"] += 1

def add_event(ev: dict):
    st.session_state["planner"].append(ev)
    register_addition()
    debit_text_credit(1)

def remove_event(ev_id: str):
    st.session_state["planner"] = [e for e in st.session_state["planner"] if e["id"] != ev_id]

def conclude_event(ev_id: str):
    ev = next((e for e in st.session_state["planner"] if e["id"] == ev_id), None)
    if ev:
        st.session_state["done"].append({**ev, "completed_at": datetime.utcnow().isoformat()})
        remove_event(ev_id)

# ----------------------------- SIDEBAR -----------------------------
with st.sidebar:
    st.markdown("### Plano & Perfil")
    u = st.session_state["user"]

    plan = st.selectbox("Plano", ["Starter","Pro","Pro+"], index=["Starter","Pro","Pro+"].index(u["plan"]), key="__plan_select")
    u["plan"] = plan

    st.caption(f"**{plan}** — limite diário: **{PLANS[plan]['max_add_per_day']}** adições")

    st.progress(min(1.0, u["month_additions"]/420) if plan=="Starter" else min(1.0, u["month_additions"]/1000))
    st.caption(f"Este mês: {u['month_additions']}/{'420' if plan=='Starter' else '1000'} • Hoje: {u['today_additions']}/{PLANS[plan]['max_add_per_day']}")

    u["brand"] = st.text_input("Nome da marca", value=u["brand"])
    u["niche"] = st.text_input("Nicho/tema", value=u["niche"])
    u["tone"]  = st.selectbox("Tom", ["profissional","casual","premium"], index=["profissional","casual","premium"].index(u["tone"]))

    st.markdown("#### Métricas da conta")
    colA,colB,colC = st.columns(3)
    with colA: u["followers"] = st.number_input("Seguidores", value=int(u["followers"]), step=100)
    with colB: u["engagement"] = st.number_input("Engaj. %", value=float(u["engagement"]), step=0.1, format="%.1f")
    with colC: u["reach"] = st.number_input("Alcance", value=int(u["reach"]), step=100)

# ----------------------------- HEADER -----------------------------
st.markdown(f"## ContentForge 7.9.3 · Weekly Planner")
st.caption("Planner semanal 7 dias • Créditos descontados ao adicionar • Clique abre detalhe • Concluir → sai do planner e entra nas métricas")

# ----------------------------- TABS -----------------------------
tabs = ["Gerar","Planner (Semanal)","Performance","Export"]
tab1, tab2, tab3, tab4 = st.tabs(tabs)

# ============================= TAB 1 — GERAR (entrada rápida) =============================
with tab1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("#### ✨ Adicionar post ao planner (rápido)")

    col1,col2,col3,col4 = st.columns([2,1,1,1])
    with col1:
        title = st.text_input("Título", key="gen_title", placeholder="Ex.: Apresenta a nova coleção")
    with col2:
        platform = st.selectbox("Plataforma", ["instagram","tiktok","facebook","linkedin"], key="gen_platform")
    with col3:
        day = st.date_input("Dia", value=date.today(), key="gen_day")
    with col4:
        hh = st.time_input("Hora", value=time(18,0), key="gen_time")

    caption = st.text_area("Legenda/descrição", key="gen_caption", placeholder="Uma legenda curta e clara…")
    tags = st.text_input("Hashtags (separadas por espaço)", key="gen_tags", placeholder="#moda #ootd #outono")

    can_add = can_add_today()
    if not can_add:
        st.warning(f"Chegaste ao limite diário do plano **{u['plan']}**. Mais amanhã ou faz upgrade. 🙏")
    btn = st.button("➕ Adicionar ao planner", disabled=not(can_add and title and caption))

    if btn and can_add and title and caption:
        ev = {
            "id": unique_id(),
            "title": title,
            "platform": platform,
            "day": day.strftime("%Y-%m-%d"),
            "time": hh.strftime("%H:%M"),
            "caption": caption.strip(),
            "hashtags": [t for t in tags.split() if t.startswith("#")] if tags else [],
            "score": 7.0, "virality": 7.2, "brandfit": 6.8  # mock scoring
        }
        add_event(ev)
        st.success("Post adicionado ✅ (crédito de texto debitado).")
        safe_rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ============================= TAB 2 — PLANNER SEMANAL =============================
with tab2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("#### 🗓️ Semana")

    c1,c2,c3 = st.columns([1,1,4])
    with c1:
        if st.button("« Semana anterior"):
            st.session_state["week_anchor"] = st.session_state["week_anchor"] - timedelta(days=7)
            safe_rerun()
    with c2:
        if st.button("Próxima semana »"):
            st.session_state["week_anchor"] = st.session_state["week_anchor"] + timedelta(days=7)
            safe_rerun()
    with c3:
        wk_anchor = st.date_input("Âncora", value=st.session_state["week_anchor"], key=f"wkanchor_{st.session_state['week_anchor']}")
        st.session_state["week_anchor"] = wk_anchor

    start, end = week_bounds(st.session_state["week_anchor"])
    st.caption(f"De **{start.strftime('%d/%m')}** a **{end.strftime('%d/%m')}**")

    # ---- GRID 7 DIAS ----
    week_events = events_in_week(start, end, st.session_state["planner"])
    by_day = { (start + timedelta(days=i)).strftime("%Y-%m-%d"): [] for i in range(7) }
    for ev in week_events:
        by_day[ev["day"]].append(ev)
    for k in by_day:
        by_day[k].sort(key=lambda e: e["time"])

    st.markdown('<div class="grid7">', unsafe_allow_html=True)
    for i in range(7):
        d = start + timedelta(days=i)
        key_day = d.strftime("%Y-%m-%d")
        st.markdown('<div class="day">', unsafe_allow_html=True)
        st.markdown(f"<h4>{d.strftime('%a %d/%m')}</h4>", unsafe_allow_html=True)
        if by_day[key_day]:
            for ev in by_day[key_day]:
                # botão único por evento → guarda evento selecionado e abre detalhe
                bkey = f"open_{ev['id']}"
                if st.button(f"📌 {ev['time']} — {ev['title']}", key=bkey, use_container_width=True):
                    st.session_state["evento_selecionado"] = ev
                    safe_rerun()
        else:
            st.caption("Sem posts.")
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ---- DETALHE (MODAL/EXPANDER) ----
    sel = st.session_state["evento_selecionado"]
    if sel:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown(f"### ✨ {sel['title']}")
        colx, coly, colz = st.columns(3)
        with colx: st.write(f"**Plataforma:** {sel['platform']}")
        with coly: st.write(f"**Dia:** {sel['day']}")
        with colz: st.write(f"**Hora:** {sel['time']}")
        st.write("**Legenda**")
        st.write(sel["caption"])
        if sel.get("hashtags"):
            st.write("**Hashtags**")
            st.code(" ".join(sel["hashtags"]))

        c1,c2,c3 = st.columns([1,1,2])
        with c1:
            if st.button("✅ Concluído", key=f"done_{sel['id']}"):
                conclude_event(sel["id"])
                st.session_state["evento_selecionado"] = None
                st.success("Marcado como concluído. Foi movido para métricas.")
                safe_rerun()
        with c2:
            if st.button("🗑️ Remover", key=f"rm_{sel['id']}"):
                remove_event(sel["id"])
                st.session_state["evento_selecionado"] = None
                st.warning("Removido do planner.")
                safe_rerun()
        with c3:
            if st.button("Fechar detalhe", key=f"close_{sel['id']}"):
                st.session_state["evento_selecionado"] = None
                safe_rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# ============================= TAB 3 — PERFORMANCE (gated) =============================
with tab3:
    if not PLANS[u["plan"]]["performance"]:
        st.markdown('<div class="card lock">', unsafe_allow_html=True)
        st.markdown("### 🔒 Performance (Pro/Pro+)")
        st.caption("Vê métricas de concluídos, CTR estimado, aprendizagens por copy e hora. Faz upgrade para desbloquear.")
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### 📈 Performance (simulada em app demo)")
        done = st.session_state["done"]
        total = len(done)
        avg_score = round(sum([e.get("score",7.0) for e in done])/total,2) if total else 0
        avg_v = round(sum([e.get("virality",7.0) for e in done])/total,2) if total else 0
        st.markdown('<div class="kpi">', unsafe_allow_html=True)
        st.markdown(f'<div><div class="muted">Concluídos</div><div class="big">{total}</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div><div class="muted">Score médio</div><div class="big">{avg_score}</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div><div class="muted">Virality média</div><div class="big">{avg_v}</div></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        if total:
            df = pd.DataFrame([{
                "dia": e["day"], "hora": e["time"], "plataforma": e["platform"],
                "título": e["title"], "score": e.get("score",7.0), "virality": e.get("virality",7.0)
            } for e in done]).sort_values(["dia","hora"])
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("Ainda não há posts concluídos.")
        st.markdown('</div>', unsafe_allow_html=True)

# ============================= TAB 4 — EXPORT (gated por plano, mas on por todos aqui) =============================
with tab4:
    can_export = PLANS[u["plan"]]["export"]
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### ⤵️ Exportar planner (JSON)")
    data = {"planner": st.session_state["planner"], "done": st.session_state["done"]}
    payload = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
    st.download_button("Download .json", data=payload, file_name="planner.json", mime="application/json", disabled=not can_export)
    st.caption("No Pro/Pro+ podes também exportar CSV/ICS (aqui mantivemos JSON para demo).")
    st.markdown('</div>', unsafe_allow_html=True)
