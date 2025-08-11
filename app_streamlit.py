# app_streamlit.py
# -*- coding: utf-8 -*-
"""
Protótipo de Avaliação em Streamlit
Como rodar:
1) pip install streamlit pandas
2) streamlit run app_streamlit.py
"""

import json, sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict
import pandas as pd
import streamlit as st

# ===== Aparência (cores Schumann) =====
BRAND_PRIMARY = "#003366"   # azul
BRAND_ACCENT  = "#f59e0b"   # amarelo
LOGO_URL = "https://static.wixstatic.com/media/27e2e9_926cd3db00704f679c4a5b7431680df8~mv2.png/v1/fill/w_145%2Ch_76%2Cal_c%2Cq_85%2Cusm_0.66_1.00_0.01%2Cenc_avif%2Cquality_auto/Schumann00000.png"

st.set_page_config(page_title="Avaliação – Produção (Protótipo)", page_icon="📝", layout="wide")
st.markdown(f"""
<style>
  .stAppHeader {{ background: {BRAND_PRIMARY} !important; }}
  .stAppHeader h1, .stAppHeader h2, .stAppHeader h3, .stAppHeader p {{ color: white !important; }}
  .accent-btn button {{ background: {BRAND_ACCENT} !important; border-color: {BRAND_ACCENT} !important; color: #111 !important; }}
  .pill {{ background:{BRAND_ACCENT}; color:#111; padding:2px 8px; border-radius:999px; font-size:.85rem; }}
</style>
""", unsafe_allow_html=True)

# ===== Critérios =====
CRITERIA_LEADER = [
    ("gestaoEquipe","Gestão da Equipe","Lidera, desenvolve e motiva a equipe; lida bem com conflitos."),
    ("resultados","Compromisso com Resultados","Entrega metas, cumpre prazos e mantém qualidade."),
    ("comunicacao","Comunicação","Clareza nas informações; dá feedbacks."),
    ("decisao","Tomada de Decisão","Age com agilidade e responsabilidade."),
    ("recursos","Gestão de Recursos","Usa bem materiais, pessoas e tempo."),
    ("disciplina","Disciplina e Organização","Mantém organização e rotinas."),
    ("processos","Conformidade com Processos","Garante procedimentos, segurança e 5S."),
    ("relatorios","Relatórios e Indicadores","Analisa OEE, produtividade, refugos, paradas."),
    ("interacao","Interação com outras áreas","Colabora com PCP, manutenção, engenharia, logística."),
    ("desenvolvimento","Desenvolvimento Técnico","Evolui tecnicamente e sugere melhorias."),
]

CRITERIA_EMP = [
    ("assiduidade","Assiduidade e Pontualidade","Comparece com regularidade e pontualidade."),
    ("disciplina","Disciplina e Normas","Segue regras, procedimentos e orientações."),
    ("comprometimento","Comprometimento","Mostra interesse e responsabilidade."),
    ("produtividade","Produtividade","Agilidade, qualidade e metas."),
    ("equipe","Trabalho em Equipe","Colabora e respeita."),
    ("comunicacao","Comunicação","Expressa-se com clareza; escuta ativamente."),
    ("organizacao","Organização","Posto limpo e organizado."),
    ("iniciativa","Iniciativa e Proatividade","Atua sem ordens constantes."),
    ("aprendizado","Capacidade de Aprendizado","Aprende e aplica novidades."),
    ("seguranca","Segurança do Trabalho","Cumpre normas e usa EPIs."),
]

def average_score(d: Dict[str, int]) -> float:
    vals = [v for v in d.values() if isinstance(v, (int, float))]
    return round(sum(vals)/len(vals), 2) if vals else 0.0

def classify(score: float) -> str:
    if score == 0: return "—"
    if score < 2: return "🔴 Insatisfatório"
    if score < 3: return "🟡 Regular"
    if score < 4.25: return "🟢 Bom"
    return "🟢🟢 Excelente"

# ===== SQLite simples (opcional) =====
DB_PATH = Path("avaliacoes.db")

def init_db():
    with sqlite3.connect(DB_PATH) as con:
        con.execute("""
        CREATE TABLE IF NOT EXISTS avaliacoes(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          tipo TEXT NOT NULL,
          payload TEXT NOT NULL,
          created_at TEXT NOT NULL
        );
        """)

def insert_eval(tipo: str, payload: dict):
    with sqlite3.connect(DB_PATH) as con:
        con.execute("INSERT INTO avaliacoes (tipo,payload,created_at) VALUES (?,?,?)",
                    (tipo, json.dumps(payload, ensure_ascii=False), datetime.utcnow().isoformat()))

def load_all() -> pd.DataFrame:
    if not DB_PATH.exists():
        return pd.DataFrame(columns=["id","tipo","payload","created_at"])
    with sqlite3.connect(DB_PATH) as con:
        return pd.read_sql_query("SELECT * FROM avaliacoes ORDER BY id DESC", con)

# ===== Cabeçalho =====
cl, ct = st.columns([1,6])
with cl: st.image(LOGO_URL, use_container_width=True)
with ct:
    st.markdown("<h2 style='margin-bottom:0'>Ferramenta de Avaliação – Produção</h2>", unsafe_allow_html=True)
    st.caption("Protótipo em Streamlit para validar aparência e funções")

st.sidebar.header("Opções")
use_sqlite = st.sidebar.checkbox("Salvar em SQLite local (avaliacoes.db)", value=True)
if use_sqlite: init_db()

st.sidebar.divider()
st.sidebar.write("Exportações")
df_all = load_all()
if not df_all.empty:
    rows = []
    for _, r in df_all.iterrows():
        p = json.loads(r["payload"]) if isinstance(r["payload"], str) else r["payload"]
        rows.append({
            "id": r["id"],
            "tipo": r["tipo"],
            "nome": (p.get("info",{}).get("nome") or p.get("info",{}).get("avaliado_nome")),
            "setor_area": (p.get("info",{}).get("setor") or p.get("info",{}).get("area")),
            "periodo": p.get("info",{}).get("periodo",""),
            "score": p.get("score",0),
            "classificacao": p.get("classificacao",""),
            "created_at": r["created_at"],
        })
    st.sidebar.download_button(
        "Baixar CSV (histórico)",
        data=pd.DataFrame(rows).to_csv(index=False).encode("utf-8-sig"),
        file_name=f"avaliacoes_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv",
        use_container_width=True
    )
else:
    st.sidebar.info("Sem histórico ainda. Salve pelo menos uma avaliação.")

tab_lider, tab_emp, tab_hist = st.tabs(["Líder de Produção","Liderados","Histórico"])

with tab_lider:
    st.subheader("Avaliação – Líder de Produção")
    c1,c2,c3,c4 = st.columns(4)
    nome = c1.text_input("Nome do Líder *")
    area = c2.text_input("Área/Setor")
    periodo = c3.text_input("Período Avaliado (ex: 01/07 a 31/07/2025)")
    avaliadores = c4.text_input("Avaliador(es)")

    st.markdown("#### Critérios (1 a 5)")
    scores = {}
    for key, label, desc in CRITERIA_LEADER:
        L, R = st.columns([2,1])
        with L: st.markdown(f"**{label}**  \n<small>{desc}</small>", unsafe_allow_html=True)
        with R: scores[key] = st.radio("", [1,2,3,4,5], horizontal=True, key=f"ldr_{key}")

    st.markdown("#### Avaliação Qualitativa")
    q1,q2,q3 = st.columns(3)
    fortes = q1.text_area("Pontos Fortes")
    melhorias = q2.text_area("Oportunidades de Melhoria")
    acoes = q3.text_area("Ações para o Próximo Período")

    st.markdown("#### KPIs")
    k1,k2,k3,k4,k5 = st.columns(5)
    oee = k1.text_input("OEE (%)")
    horas_extras = k2.text_input("Horas Extras (média mensal)")
    refugos = k3.text_input("Refugos (%)")
    atraso_planejado = k4.text_input("Horas em Atraso vs Planejado")
    absenteismo = k5.text_input("Absenteísmo (%)")

    st.markdown("#### Frequência e Participação")
    f1,f2,f3 = st.columns(3)
    reunioes = f1.text_input("Participa de reuniões? (ex: Sim, diariamente)")
    prazos = f2.text_input("Cumpre prazos de relatórios?")
    priorizacao = f3.text_input("Sabe priorizar demandas?")

    score = average_score(scores)
    classificacao = classify(score)
    m1,m2 = st.columns(2)
    m1.metric("Nota Final (média)", f"{score:.2f}")
    m2.metric("Classificação", classificacao)

    payload = {
        "tipo":"avaliacao_lider_producao",
        "info":{"nome":nome,"area":area,"periodo":periodo,"avaliadores":avaliadores},
        "scores":scores, "score":score, "classificacao":classificacao,
        "qualit":{"fortes":fortes,"melhorias":melhorias,"acoes":acoes},
        "kpi":{"oee":oee,"horasExtras":horas_extras,"refugos":refugos,
               "atrasoPlanejado":atraso_planejado,"absenteismo":absenteismo},
        "freq":{"reunioes":reunioes,"prazos":prazos,"priorizacao":priorizacao},
        "timestamp": datetime.utcnow().isoformat()
    }

    b1,b2,b3 = st.columns(3)
    with b1:
        st.download_button("Baixar JSON",
            data=json.dumps(payload, ensure_ascii=False, indent=2),
            file_name=f"avaliacao_lider_{nome or 'sem_nome'}.json",
            use_container_width=True)
    with b2:
        if st.button("Salvar (SQLite)", use_container_width=True, type="primary"):
            if use_sqlite: insert_eval("lider", payload); st.success("Salvo no SQLite.")
            else: st.warning("Ative o SQLite na barra lateral para persistir.")
    with b3:
        if st.button("Limpar formulário", use_container_width=True):
            for key,_,_ in CRITERIA_LEADER: st.session_state[f"ldr_{key}"]=1
            st.experimental_rerun()

with tab_emp:
    st.subheader("Avaliação – Liderados")
    c1,c2,c3,c4,c5 = st.columns(5)
    nome_e = c1.text_input("Nome do Colaborador *")
    funcao  = c2.text_input("Função/Cargo")
    setor   = c3.text_input("Setor")
    periodo_e = c4.text_input("Período Avaliado")
    lider_resp = c5.text_input("Líder Responsável")

    st.markdown("#### Critérios (1 a 5)")
    scores_e = {}
    for key, label, desc in CRITERIA_EMP:
        L, R = st.columns([2,1])
        with L: st.markdown(f"**{label}**  \n<small>{desc}</small>", unsafe_allow_html=True)
        with R: scores_e[key] = st.radio("", [1,2,3,4,5], horizontal=True, key=f"emp_{key}")

    st.markdown("#### Avaliação Qualitativa")
    qa,qb,qc = st.columns(3)
    fortes_e = qa.text_area("Pontos Fortes", key="emp_fortes")
    melhorias_e = qb.text_area("Oportunidades de Melhoria", key="emp_melh")
    evolucao_e = qc.text_area("Evolução desde a última avaliação", key="emp_evol")

    st.markdown("#### Indicadores (se aplicável)")
    dados_obj = st.text_area("Dados objetivos (produção, retrabalho, tempo, etc.)", key="emp_dados")

    st.markdown("#### Feedback do Colaborador (Opcional)")
    feedback = st.text_area("Comentários / sugestões", key="emp_feed")

    score_e = average_score(scores_e)
    classificacao_e = classify(score_e)
    m1,m2 = st.columns(2)
    m1.metric("Nota Final (média)", f"{score_e:.2f}")
    m2.metric("Classificação", classificacao_e)

    payload_e = {
        "tipo":"avaliacao_liderados",
        "info":{"nome":nome_e,"funcao":funcao,"setor":setor,"periodo":periodo_e,"lider":lider_resp},
        "scores":scores_e, "score":score_e, "classificacao":classificacao_e,
        "qualit":{"fortes":fortes_e,"melhorias":melhorias_e,"evolucao":evolucao_e},
        "indic":{"dados":dados_obj},
        "feedback":feedback,
        "timestamp": datetime.utcnow().isoformat()
    }

    b1,b2,b3 = st.columns(3)
    with b1:
        st.download_button("Baixar JSON",
            data=json.dumps(payload_e, ensure_ascii=False, indent=2),
            file_name=f"avaliacao_colaborador_{nome_e or 'sem_nome'}.json",
            use_container_width=True)
    with b2:
        if st.button("Salvar (SQLite)", use_container_width=True, type="primary", key="salvar_emp"):
            if use_sqlite: insert_eval("liderado", payload_e); st.success("Salvo no SQLite.")
            else: st.warning("Ative o SQLite na barra lateral para persistir.")
    with b3:
        if st.button("Limpar formulário", use_container_width=True, key="limpar_emp"):
            for key,_,_ in CRITERIA_EMP: st.session_state[f"emp_{key}"]=1
            st.experimental_rerun()

with tab_hist:
    st.subheader("Histórico (local)")
    df = load_all()
    if df.empty:
        st.info("Sem registros salvos ainda.")
    else:
        rows = []
        for _, r in df.iterrows():
            p = json.loads(r["payload"]) if isinstance(r["payload"], str) else r["payload"]
            rows.append({
                "ID": r["id"],
                "Tipo": r["tipo"],
                "Nome": p.get("info",{}).get("nome") or p.get("info",{}).get("avaliado_nome"),
                "Setor/Área": p.get("info",{}).get("setor") or p.get("info",{}).get("area"),
                "Período": p.get("info",{}).get("periodo",""),
                "Score": p.get("score",0),
                "Classificação": p.get("classificacao",""),
                "Criado em (UTC)": r["created_at"],
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True)
        st.caption("Os dados ficam no arquivo 'avaliacoes.db' na mesma pasta. Para backup, copie o arquivo ou exporte CSV na barra lateral.")
