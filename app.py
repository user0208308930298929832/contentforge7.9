
import streamlit as st
import pandas as pd
import random
from datetime import date, datetime, time, timedelta

st.set_page_config(page_title="ContentForge 7.9 • Weekly Planner", layout="wide")

ss = st.session_state
if "posts" not in ss: ss.posts = []
if "schedule" not in ss: ss.schedule = []
if "completed" not in ss: ss.completed = []
if "seed" not in ss: ss.seed = 20251111
if "plano" not in ss: ss.plano = "Starter"
if "gen_count_month" not in ss: ss.gen_count_month = 0
if "daily_usage" not in ss: ss.daily_usage = {"date": date.today(), "count": 0}
if "week_offset" not in ss: ss.week_offset = 0
random.seed(ss.seed)

PLANS = {
    "Starter": {"price":"9.99 €", "month_limit": 20, "daily_limit": 5, "desc":"5 adições/dia, 20/mês"},
    "Pro":     {"price":"24.99 €", "month_limit": 100000, "daily_limit": 100000, "desc":"Ilimitado, métricas & performance"},
    "Prime":   {"price":"49.99 €", "month_limit": 200000, "daily_limit": 200000, "desc":"Tudo + IA visual + API real (futuro)"}
}

def reset_daily_if_needed():
    if ss.daily_usage["date"] != date.today():
        ss.daily_usage = {"date": date.today(), "count": 0}

def check_add_credits():
    reset_daily_if_needed()
    if ss.plano == "Starter":
        if ss.daily_usage["count"] >= PLANS["Starter"]["daily_limit"]:
            st.error(f"🚫 Limite diário atingido ({PLANS['Starter']['daily_limit']} adições ao planner/dia no Starter).")
            st.info("💡 Faz upgrade para **Pro** para remover limites.")
            st.stop()
        if ss.gen_count_month >= PLANS["Starter"]["month_limit"]:
            st.error("🚫 Atingiste o limite mensal (20 adições ao planner no Starter).")
            st.button("🚀 Fazer upgrade agora")
            st.stop()

def spend_credit(n:int=1):
    reset_daily_if_needed()
    ss.daily_usage["count"] += n
    ss.gen_count_month += n

def cleanse_username(url:str) -> str:
    if not url: return "teuperfil"
    u = url.split("?")[0].strip("/")
    if u.endswith("/"):
        u = u[:-1]
    name = u.split("/")[-1] if "/" in u else u
    return name or "teuperfil"

def simulate_metrics(username:str, followers_hint=None):
    base_hash = sum(ord(c) for c in username) % 10000
    followers = followers_hint if followers_hint else 2500 + (base_hash % 4000)
    if followers < 5000:
        eng = round(random.uniform(2.8, 4.5), 1)
        reach = int(followers * random.uniform(0.18, 0.32))
    else:
        eng = round(random.uniform(2.2, 3.8), 1)
        reach = int(followers * random.uniform(0.15, 0.28))
    return followers, eng, reach

def check_access(required_plan:str):
    hierarchy = ["Starter", "Pro", "Prime"]
    if hierarchy.index(ss.plano) < hierarchy.index(required_plan):
        st.warning(f"🔒 Disponível apenas para planos **{required_plan}** ou superior.")
        st.info("💡 Faz upgrade para desbloquear esta funcionalidade.")
        st.button("🚀 Fazer upgrade agora", key=f"upgrade_{required_plan}")
        st.stop()

def toast(msg, icon="✅"):
    try:
        st.toast(f"{icon} {msg}")
    except Exception:
        st.success(msg)

st.sidebar.header("Plano & Perfil")
ss.plano = st.sidebar.selectbox("Plano", list(PLANS.keys()), index={"Starter":0,"Pro":1,"Prime":2}[ss.plano])
st.sidebar.caption(f"**{ss.plano}** — {PLANS[ss.plano]['price']} / mês · {PLANS[ss.plano]['desc']}")
st.sidebar.progress(min(1.0, ss.gen_count_month / max(1, PLANS[ss.plano]["month_limit"])))
st.sidebar.caption(f"Este mês: **{ss.gen_count_month}/{PLANS[ss.plano]['month_limit']}**")
st.sidebar.caption(f"Hoje: **{ss.daily_usage['count']}/{PLANS[ss.plano]['daily_limit']}**")

st.sidebar.markdown("---")
brand = st.sidebar.text_input("Nome da marca", value=ss.get("brand","Minha Marca"))
niche = st.sidebar.text_input("Nicho/tema", value=ss.get("niche","moda sustentável"))
tone  = st.sidebar.selectbox("Tom", ["profissional","casual","premium","divertido"], index=0)

st.sidebar.markdown("---")
st.sidebar.subheader("📊 Métricas da conta")
with st.sidebar.expander("Ligação por link (simulada) — IG/TikTok"):
    url = st.text_input("URL do perfil", placeholder="https://instagram.com/_loukisses_/")
    followers_hint = st.number_input("Seguidores (opcional)", min_value=0, value=3224, step=100)
    if st.button("Atualizar métricas", key="upd_metrics"):
        uname = cleanse_username(url)
        f,e,r = simulate_metrics(uname, followers_hint if followers_hint>0 else None)
        ss.followers, ss.eng_rate, ss.reach_avg = f, e, r
        toast(f"Métricas simuladas para @{uname} atualizadas.", "📈")

c1,c2,c3 = st.sidebar.columns(3)
c1.metric("Seguidores", value=ss.get("followers", 3224))
c2.metric("Engaj. %", value=ss.get("eng_rate", 3.2))
c3.metric("Alcance", value=ss.get("reach_avg", 845))

st.title("ContentForge 7.9 • Weekly Planner")
st.caption("Planner semanal 7 dias • Créditos só ao adicionar • Modal detalhado • Concluir → métricas reais")

tabs = st.tabs(["✨ Gerar", "📅 Planner (Semanal)", "📈 Performance", "📤 Export"])

# --- Creative Caption Engine ---
PREPS = {"de","da","do","d","a","e","em","para","por"}

def clean_snippet(s: str, max_words: int = 12) -> str:
    if not s: return ""
    w = s.strip().split()
    w = w[:max_words]
    if w and w[-1].lower() in PREPS: w = w[:-1]
    return " ".join(w)

def make_title(platform, brief, niche):
    base = clean_snippet(brief or f"Ideias para {niche}", 12)
    verb = random.choice({"instagram":["Mostra","Apresenta","Revela","Partilha"],
                          "tiktok":["Grava","Mostra","Explica","Desafia"]}.get(platform,["Mostra"]))
    return f"{verb} {base}".capitalize()

def gen_caption_creative(brand, niche, tone, brief):
    tone_hooks = {
        "profissional": ["O essencial funciona sempre.","Clareza sem ruído.","Qualidade acima de tudo."],
        "casual": ["Sem rodeios — direto ao ponto.","Mais real, menos perfeição.","Bora tornar isto simples."],
        "premium": ["Detalhes que elevam o look.","Elegância é eliminar o excesso.","Feito para durar."],
        "divertido": ["Traz energia para o feed! 😄","Um toque de humor muda tudo.","Faz scroll valer a pena!"],
    }
    hook = random.choice(tone_hooks.get(tone, ["Vamos a isto."]))
    story_bits = [
        "Há peças que aquecem mais do que o corpo — aquecem o estilo.",
        "Começou com uma peça que queríamos guardar para sempre.",
        "Tecido que pede luz natural. Corte que pede movimento.",
        "Feito para o teu dia normal parecer especial."
    ]
    story = random.choice(story_bits)
    core = brief if brief else f"O lado real de {brand} no nicho de {niche}."
    ctas = [
        "Qual combina mais contigo? 👀",
        "Fica de olho nas novidades.",
        "Diz-nos nos comentários o teu favorito.",
        "Pronta para o próximo look?"
    ]
    cta = random.choice(ctas)
    return f"{hook} {story} {core} {cta}"

def hashtag_miner(niche, brief):
    base = list({*(niche.lower().split()[:3]), *(brief.lower().split()[:4] if brief else [])})
    pool = base + ["modaportuguesa","slowfashion","ootd","lookinspo","tendencias","autumn","casacos","lifestyle","pt"]
    random.shuffle(pool)
    tags = [f"#{t}" for t in pool[:12]]
    top3 = tags[:3]
    rest = tags[3:]
    return top3, rest

def score_engine(brief, niche, tone, platform, plan):
    base = 6.0
    if tone=="premium": base += 0.5
    if tone=="divertido": base += random.uniform(0.3,0.6)
    if plan=="Prime": base += 0.6
    elif plan=="Pro": base += 0.3
    if platform=="tiktok":
        vir = base + random.uniform(0.6,1.2)
        fit = base + random.uniform(-0.2,0.4)
    else:
        vir = base + random.uniform(-0.2,0.6)
        fit = base + random.uniform(0.2,0.8)
    basis = (brief or niche)
    diversity = len(set(basis.split())) / (len(basis.split())+1)
    vir += diversity * 1.2
    fit += len(niche.split()) * 0.05
    vir = round(min(10, max(5, vir)),2)
    fit = round(min(10, max(5, fit)),2)
    score = round(vir*0.6 + fit*0.4, 2)
    reach_avg = ss.get("reach_avg",845)
    eng_rate = ss.get("eng_rate",3.2)
    reach = int(reach_avg * (score/8.0))
    eng = round(max(0.0, eng_rate + (score-7.5)*3.5),1)
    return vir, fit, score, reach, eng

def uniq(prefix, i):
    return f"{prefix}_{i}_{random.randint(1000,9999)}"

# --- Tab: Generate ---
with tabs[0]:
    st.subheader("Geração inteligente (Creative Engine v2)")
    st.caption("💡 Só usas créditos quando **adicionas ao Planner**. Gerar é grátis.")
    colA,colB = st.columns([3,2])
    with colA:
        platforms = st.multiselect("Plataformas", ["instagram","tiktok"], default=["instagram","tiktok"])
        brief = st.text_input("O que queres comunicar hoje?", placeholder="Ex.: Casacos novos da coleção de outono…")
        extra  = st.text_area("Informação extra (opcional)", placeholder="Público, oferta, objecção...")
    with colB:
        qty = st.slider("Ideias por plataforma", 1, 10, 4)
        st.info("Dica: escreve um brief claro para variação máxima.")
        if ss.plano=="Starter":
            st.caption("Limites aplicam-se apenas ao **Adicionar ao Planner** (5/dia • 20/mês).")
    if st.button("⚡ Gerar agora", type="primary"):
        ss.posts = []
        for p in platforms:
            for _ in range(qty):
                title = make_title(p, brief, niche)
                caption = gen_caption_creative(brand, niche, tone, brief)
                top3, rest = hashtag_miner(niche, brief or "")
                vir, fit, score, reach, eng = score_engine(brief or "", niche, tone, p, ss.plano)
                ss.posts.append({
                    "platform": p, "title": title, "caption": caption,
                    "top3": top3, "tags_rest": rest,
                    "virality": vir, "brand_fit": fit, "score": score, "reach": reach, "eng": eng
                })
        for p in platforms:
            subset = [x for x in ss.posts if x["platform"]==p]
            if subset:
                max(subset, key=lambda x: x["score"])["recommended"] = True
        toast("Conteúdo gerado", "⚡")

    cols = st.columns(2)
    for i,post in enumerate(ss.posts):
        col = cols[i % 2]
        with col:
            with st.container(border=True):
                st.markdown(f"**📱 {post['platform'].capitalize()} — {post['title']}**")
                if post.get("recommended"):
                    st.markdown("<div style='display:inline-block; background:#ffd700; color:#111; padding:2px 8px; border-radius:10px; font-weight:600; font-size:0.8rem; margin:4px 0;'>🌟 Nossa recomendação</div>", unsafe_allow_html=True)
                st.write(post["caption"])
                st.caption("Hashtags:  " + " ".join([f"`{t}`" for t in post["top3"]]))
                if post["tags_rest"]:
                    with st.expander(f"Ver todas (+{len(post['tags_rest'])})"):
                        st.code(" ".join(post["top3"] + post["tags_rest"]), language=None)
                k1,k2,k3 = st.columns(3)
                with k1: st.metric("Virality", post["virality"])
                with k2: st.metric("Brand-fit", post["brand_fit"])
                with k3: st.metric("Score", post["score"])
                k4,k5 = st.columns(2)
                with k4: st.caption(f"👀 Alcance: ~{post['reach']:,}".replace(",", "."))
                with k5: st.caption(f"💬 Engaj.: ~{post['eng']}%")

                c1, c2, c3 = st.columns([2,2,1])
                dkey = uniq("d", i); tkey = uniq("t", i)
                with c1:
                    day = st.date_input("📅", value=date.today(), key=dkey, label_visibility="collapsed")
                with c2:
                    hour = st.time_input("⏰", value=time(18,0), key=tkey, label_visibility="collapsed")
                with c3:
                    if st.button("➕", key=uniq("add", i), help="Adicionar ao Planner"):
                        check_add_credits()
                        ss.schedule.append({
                            "day": day.isoformat(), "time": hour.strftime("%H:%M"),
                            "platform": post["platform"], "title": post["title"],
                            "caption": post["caption"], "hashtags": " ".join(post["top3"] + post["tags_rest"]),
                            "score": post["score"], "eng": post["eng"]
                        })
                        spend_credit(1)
                        toast("Adicionado ao Planner (1 crédito usado)", "🗓️")
                        st.experimental_rerun()

# --- Helpers: week dates ---
def monday_of_week(offset:int=0) -> date:
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    return monday + timedelta(days=7*offset)

def week_days(offset:int=0):
    m = monday_of_week(offset)
    return [m + timedelta(days=i) for i in range(7)]

def posts_for_day(day_iso:str):
    return [ev for ev in ss.schedule if ev["day"] == day_iso]

# --- Tab: Weekly Planner ---
with tabs[1]:
    st.subheader("Planner semanal (7 dias)")
    left, mid, right = st.columns([1,3,1])
    with left:
        if st.button("⏮️ Semana anterior"):
            ss.week_offset -= 1
            st.experimental_rerun()
    with mid:
        m = monday_of_week(ss.week_offset)
        st.markdown(f"### 📆 Semana de **{m.strftime('%d/%m')}** a **{(m+timedelta(days=6)).strftime('%d/%m')}**")
    with right:
        if st.button("Semana seguinte ⏭️"):
            ss.week_offset += 1
            st.experimental_rerun()

    days = week_days(ss.week_offset)
    cols = st.columns(7)
    for i, d in enumerate(days):
        with cols[i]:
            st.markdown(f"**{d.strftime('%a %d/%m')}**")
            todays = posts_for_day(d.isoformat())
            if todays:
                for j,ev in enumerate(sorted(todays, key=lambda x: x['time'])):
                    key_btn = f"open_{i}_{j}_{hash(ev['title'])%9999}"
                    if st.button(f"🕒 {ev['time']} · {ev['platform']} · {ev['title'][:18]}", key=key_btn):
                        ss["selected_ev"] = {"day": d.isoformat(), "index": j, "ev": ev}
                        st.experimental_rerun()
            else:
                st.caption("—")
            with st.popover("➕"):
                hh = st.time_input("Hora", time(18,0), key=f"ti_{i}")
                if ss.posts:
                    idx = st.selectbox("Usar ideia gerada", list(range(len(ss.posts))), format_func=lambda k: ss.posts[k]["title"][:40], key=f"sel_{i}")
                    if st.button("Adicionar", key=f"add_day_{i}"):
                        check_add_credits()
                        post = ss.posts[idx]
                        ss.schedule.append({
                            "day": d.isoformat(), "time": hh.strftime("%H:%M"),
                            "platform": post["platform"], "title": post["title"],
                            "caption": post["caption"], "hashtags": " ".join(post["top3"] + post["tags_rest"]),
                            "score": post["score"], "eng": post["eng"]
                        })
                        spend_credit(1)
                        toast(f"Adicionado a {d.strftime('%a %d/%m')} (1 crédito)", "🗓️")
                        st.experimental_rerun()
                else:
                    st.info("Gera ideias na aba ✨ para adicionar.")

    if "selected_ev" in ss and ss.selected_ev:
        sel = ss.selected_ev
        ev = sel["ev"]
        with st.modal(f"{ev['day']} {ev['time']} · {ev['platform']} — {ev['title']}", key="modal_ev"):
            st.write("**Legenda**")
            st.write(ev["caption"])
            st.write("**Hashtags**")
            st.code(ev["hashtags"])
            colA,colB,colC = st.columns(3)
            with colA:
                new_day = st.date_input("Mover para o dia", value=datetime.fromisoformat(ev["day"]).date())
                new_time = st.time_input("Hora", value=datetime.strptime(ev["time"], "%H:%M").time())
                if st.button("Mover"):
                    for item in ss.schedule:
                        if item is ev:
                            item["day"] = new_day.isoformat()
                            item["time"] = new_time.strftime("%H:%M")
                            break
                    toast("Movido.", "↔️")
                    ss.selected_ev = None
                    st.experimental_rerun()
            with colB:
                if st.button("✅ Concluído"):
                    reach_pred = ss.get("reach_avg", 845) * (float(ev.get("score",7))/8.0)
                    alcance_real = int(reach_pred * random.uniform(0.85, 1.25))
                    eng_real = round(max(0.0, float(ev.get("eng",3.0)) + random.uniform(-0.5, 1.2)), 1)
                    likes = int(alcance_real * eng_real/100 * random.uniform(0.7, 1.3))
                    comentarios = int(likes * random.uniform(0.03, 0.08))
                    partilhas = int(likes * random.uniform(0.01, 0.05))
                    ss.completed.append({
                        "day": ev["day"], "time": ev["time"], "platform": ev["platform"],
                        "title": ev["title"], "alcance_real": alcance_real, "eng_real": eng_real,
                        "likes": likes, "comentarios": comentarios, "partilhas": partilhas
                    })
                    ss.schedule.remove(ev)
                    toast("Marcado como concluído", "✔️")
                    ss.selected_ev = None
                    st.experimental_rerun()
            with colC:
                if st.button("🗑️ Remover"):
                    ss.schedule.remove(ev)
                    toast("Removido do planner", "🗑️")
                    ss.selected_ev = None
                    st.experimental_rerun()

# --- Tab: Performance ---
with tabs[2]:
    check_access("Pro")
    st.subheader("Performance")
    if not ss.posts and not ss.completed:
        st.info("Gera ideias e conclui publicações para ver previsões e resultados reais.")
    else:
        if ss.posts:
            dfp = pd.DataFrame(ss.posts)
            col1,col2,col3 = st.columns(3)
            col1.metric("Score médio (prev.)", round(dfp["score"].mean(),2))
            col2.metric("Virality média (prev.)", round(dfp["virality"].mean(),2))
            col3.metric("Brand-fit médio (prev.)", round(dfp["brand_fit"].mean(),2))
            st.markdown("#### Previsão por post")
            st.dataframe(dfp[["platform","title","score","reach","eng"]], use_container_width=True, hide_index=True)
        st.markdown("---")
        st.markdown("### 📈 Resultados Reais (Publicados)")
        if not ss.completed:
            st.info("Ainda não há publicações concluídas.")
        else:
            dfr = pd.DataFrame(ss.completed)
            colA,colB,colC = st.columns(3)
            colA.metric("Posts concluídos", len(dfr))
            colB.metric("Alcance total", int(dfr["alcance_real"].sum()))
            colC.metric("Eng. médio real %", round(dfr["eng_real"].mean(),1))
            st.dataframe(dfr, use_container_width=True, hide_index=True)

# --- Tab: Export ---
with tabs[3]:
    st.subheader("Exportar CSV")
    posts_df = pd.DataFrame(ss.posts)
    cal_df = pd.DataFrame(ss.schedule)
    real_df = pd.DataFrame(ss.completed)
    cA,cB,cC = st.columns(3)
    with cA:
        if not posts_df.empty:
            st.download_button("⬇️ Posts (CSV)", posts_df.to_csv(index=False).encode("utf-8"),
                               file_name="posts.csv", mime="text/csv")
        else:
            st.info("Sem posts.")
    with cB:
        if not cal_df.empty:
            st.download_button("⬇️ Planner (CSV)", cal_df.to_csv(index=False).encode("utf-8"),
                               file_name="planner.csv", mime="text/csv")
        else:
            st.info("Sem itens no planner.")
    with cC:
        if not real_df.empty:
            st.download_button("⬇️ Resultados (CSV)", real_df.to_csv(index=False).encode("utf-8"),
                               file_name="resultados.csv", mime="text/csv")
        else:
            st.info("Sem resultados reais.")
