# -*- coding: utf-8 -*-
"""
Programa de conferência da qualidade da informação — Instituto Semear (SIRCA)
-----------------------------------------------------------------------------
Lê as planilhas operacionais e as duas exportações em CSV, mede seis dimensões
de qualidade (completude, consistência, unicidade, conformidade de formato,
atualidade e concordância entre fontes) ANTES do tratamento e DEPOIS dele, e
grava os números em resultado_qualidade.json.

Uso:  python qualidade_informacao.py <pasta_dos_arquivos> [data_referencia AAAA-MM-DD]

Todas as regras de verificação e de tratamento estão neste arquivo, em
português, para que a mesma medição possa ser repetida em outra data.
NENHUM dado pessoal é gravado na saída: só contagens e percentuais.
"""
import json, re, sys, unicodedata
from datetime import datetime, date
import pandas as pd

PASTA = sys.argv[1] if len(sys.argv) > 1 else "."
DATA_REF = datetime.strptime(sys.argv[2], "%Y-%m-%d") if len(sys.argv) > 2 else datetime(2026, 7, 31)
XLSX = f"{PASTA}/Instituto_Semear_planilhas_operacionais_2024-2026.xlsx"
CSV_ANTIGO = f"{PASTA}/frequencia_export_sistema_antigo.csv"
CSV_DOA = f"{PASTA}/doacoes_2026.csv"

# ------------------------------------------------------------------ parâmetros
VAZIOS = {"", "nan", "none", "nao informado", "n/i", "ni", "-", "—", "?", "n.i.", "null"}
PARTICULAS = {"da", "de", "do", "das", "dos", "e"}
# Mapa de presença após consolidação: X/x = presente; traço (-) = falta.
# Somente campos vazios permanecem como "a confirmar".
MAPA_PRESENCA = {
    "p": "presente", "presente": "presente", "1": "presente",
    "x": "presente",                         # regra consolidada: X/x = presença
    "f": "falta", "falta": "falta", "faltou": "falta", "0": "falta",
    "-": "falta",                            # regra consolidada: traço = falta
    "j": "falta justificada", "justificada": "falta justificada",
}
VALORES_OFICIAIS = {"presente", "falta", "falta justificada"}
MESES = {"jan": 1, "fev": 2, "mar": 3, "abr": 4, "mai": 5, "jun": 6,
         "jul": 7, "ago": 8, "set": 9, "out": 10, "nov": 11, "dez": 12}


# ------------------------------------------------------------------ utilidades
def sem_acento(s):
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


def norm_texto(s):
    return re.sub(r"\s+", " ", sem_acento(str(s)).strip().lower())


def norm_nome(s):
    return " ".join(t for t in norm_texto(s).split() if t not in PARTICULAS)


def vazio(v):
    return v is None or (isinstance(v, float) and pd.isna(v)) or norm_texto(v) in VAZIOS


def pct(a, b):
    return round(100.0 * a / b, 1) if b else None


def formato_data(s):
    if vazio(s):
        return "vazio"
    s = str(s).strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s): return "AAAA-MM-DD"
    if re.fullmatch(r"\d{2}/\d{2}/\d{4}", s): return "DD/MM/AAAA"
    if re.fullmatch(r"\d{2}/\d{2}/\d{2}", s): return "DD/MM/AA"
    if re.fullmatch(r"\d{2}-\d{2}-\d{2}", s): return "DD-MM-AA"
    if re.fullmatch(r"\d{1,2} de [A-Za-zçÇ]+\.? de \d{4}", s, re.I): return "D de mês de AAAA"
    if re.fullmatch(r"\d{2}/\d{4}", s): return "MM/AAAA"
    return "outro"


def ler_data(s):
    f = formato_data(s)
    s = str(s).strip() if not vazio(s) else ""
    try:
        if f == "AAAA-MM-DD": return datetime.strptime(s, "%Y-%m-%d")
        if f == "DD/MM/AAAA": return datetime.strptime(s, "%d/%m/%Y")
        if f == "DD/MM/AA": return datetime.strptime(s, "%d/%m/%y")
        if f == "DD-MM-AA": return datetime.strptime(s, "%d-%m-%y")
        if f == "D de mês de AAAA":
            m = re.fullmatch(r"(\d{1,2}) de ([A-Za-zçÇ]+)\.? de (\d{4})", s, re.I)
            return datetime(int(m[3]), MESES[sem_acento(m[2]).lower()[:3]], int(m[1]))
    except (ValueError, KeyError):
        return None
    return None


def periodo(serie):
    d = serie.apply(ler_data).dropna()
    return (d.min().strftime("%d/%m/%Y"), d.max().strftime("%d/%m/%Y")) if len(d) else (None, None)


# ------------------------------------------------------------------ carga
xls = pd.ExcelFile(XLSX)
bruto = {s: xls.parse(s, dtype=str) for s in xls.sheet_names}
csv_ant = pd.read_csv(CSV_ANTIGO, encoding="latin1", sep=";", dtype=str)
csv_doa = pd.read_csv(CSV_DOA, encoding="utf-8", dtype=str)

R = {"data_referencia": DATA_REF.strftime("%d/%m/%Y")}

# ---- linhas de recado / em branco (regra de tratamento T1)
fam = bruto["CadastroFamilias"]
fam_recado = ~fam["Cod"].astype(str).str.match(r"^F\d{3}$", na=False)
fam_ok = fam[~fam_recado].copy()
par = bruto["Participantes"]
par_branco = par.isna().all(axis=1)
par_ok = par[~par_branco].copy()
ofi = bruto["Oficinas"].copy()
fre = bruto["Frequencia"]
fre_recado = fre["Oficina"].isna() & fre["Participante"].isna()   # linha sem oficina e sem participante (recado ou em branco)
fre_ok = fre[~fre_recado].copy()
doa = bruto["Doacoes"].copy()
enc = bruto["Encaminhamentos"].copy()

R["inventario"] = {
    "CadastroFamilias": dict(linhas_brutas=len(fam), recado=int(fam_recado.sum()), registros=len(fam_ok), campos=fam.shape[1]),
    "Participantes": dict(linhas_brutas=len(par), recado=int(par_branco.sum()), registros=len(par_ok), campos=par.shape[1]),
    "Oficinas": dict(linhas_brutas=len(ofi), recado=0, registros=len(ofi), campos=ofi.shape[1]),
    "Frequencia": dict(linhas_brutas=len(fre), recado=int(fre_recado.sum()), registros=len(fre_ok), campos=fre.shape[1]),
    "Doacoes": dict(linhas_brutas=len(doa), recado=0, registros=len(doa), campos=doa.shape[1]),
    "Encaminhamentos": dict(linhas_brutas=len(enc), recado=0, registros=len(enc), campos=enc.shape[1]),
    "CSV sistema antigo (frequência)": dict(linhas_brutas=len(csv_ant), recado=0, registros=len(csv_ant), campos=csv_ant.shape[1]),
    "CSV doações 2026": dict(linhas_brutas=len(csv_doa), recado=0, registros=len(csv_doa), campos=csv_doa.shape[1]),
}
R["periodos"] = {
    "CadastroFamilias (data de cadastro)": periodo(fam_ok["Data Cadastro"]),
    "Participantes (data de entrada)": periodo(par_ok["Data Entrada"]),
    "Frequencia (data)": periodo(fre_ok["Data"]),
    "Doacoes (data)": periodo(doa["Data"]),
    "Encaminhamentos (data)": periodo(enc["Data"]),
    "CSV sistema antigo (data)": periodo(csv_ant["DATA"]),
    "CSV doações 2026 (data)": periodo(csv_doa["Data"]),
}

# ------------------------------------------------------------------ 1) COMPLETUDE
OBRIG = {
    "CadastroFamilias": (fam_ok, ["Cod", "Nome do Responsável", "Endereço", "Bairro", "Nº Dependentes", "Renda Familiar", "Data Cadastro", "Situação"]),
    "Participantes": (par_ok, ["Cod", "Nome", "Cod Familia", "Nascimento", "Escola", "Turma/Ano", "Data Entrada", "Situação"]),
    "Oficinas": (ofi, ["Cod", "Oficina", "Oficineiro", "Dia", "Horário", "Sala", "Vagas", "Início", "Fim"]),
    "Frequencia": (fre_ok, ["Data", "Oficina", "Participante", "Presença", "Registrado por"]),
    "Doacoes": (doa, ["Data", "Doador", "Tipo", "Item", "Quantidade", "Unidade", "Destino", "Valor Estimado"]),
    "Encaminhamentos": (enc, ["Data", "Participante", "Serviço", "Órgão", "Situação", "Retorno"]),
}
comp = {}
for nome, (df, campos) in OBRIG.items():
    celulas = len(df) * len(campos)
    cheias = sum(int((~df[c].apply(vazio)).sum()) for c in campos)
    por_campo = {c: dict(vazios=int(df[c].apply(vazio).sum()), preenchido_pct=pct(int((~df[c].apply(vazio)).sum()), len(df))) for c in campos}
    comp[nome] = dict(celulas=celulas, preenchidas=cheias, completude_pct=pct(cheias, celulas), campos=por_campo)
R["completude"] = comp

# ------------------------------------------------------------------ 2) CONFORMIDADE DE FORMATO
conf = {}
for nome, serie in {"Frequencia.Data": fre_ok["Data"], "Doacoes.Data": doa["Data"], "Encaminhamentos.Data": enc["Data"],
                    "Participantes.Data Entrada": par_ok["Data Entrada"], "Participantes.Nascimento": par_ok["Nascimento"],
                    "CadastroFamilias.Data Cadastro": fam_ok["Data Cadastro"], "CadastroFamilias.Nascimento": fam_ok["Nascimento"],
                    "CSV antigo.DATA": csv_ant["DATA"], "CSV doações.Data": csv_doa["Data"]}.items():
    fm = serie.apply(formato_data)
    nao_vazio = int((fm != "vazio").sum())
    conf[nome] = dict(formatos=fm[fm != "vazio"].value_counts().to_dict(), preenchidos=nao_vazio,
                      iso=int((fm == "AAAA-MM-DD").sum()), iso_pct=pct(int((fm == "AAAA-MM-DD").sum()), nao_vazio),
                      leitura_ok=int(serie.apply(lambda s: ler_data(s) is not None).sum()))
R["conformidade_data"] = conf

# presença
pres = fre_ok["Presença"]
pres_n = pres.apply(lambda v: "" if vazio(v) and norm_texto(v) != "-" else norm_texto(v))
bruto_vals = pres.fillna("(vazio)").value_counts().to_dict()
oficial_bruto = int(pres.apply(lambda v: (not pd.isna(v)) and norm_texto(v) in VALORES_OFICIAIS).sum())


def classe_presenca(v):
    if pd.isna(v): return "a confirmar"
    k = norm_texto(v)
    if k in MAPA_PRESENCA: return MAPA_PRESENCA[k]
    return "a confirmar"


cls = pres.apply(classe_presenca)
R["presenca"] = dict(
    total=len(pres), marcas_distintas_preenchidas=int(pres.dropna().nunique()), vazias=int(pres.isna().sum()),
    distribuicao_bruta=bruto_vals, valores_oficiais_antes=oficial_bruto, oficiais_antes_pct=pct(oficial_bruto, len(pres)),
    convertidas=int((cls != "a confirmar").sum()), convertidas_pct=pct(int((cls != "a confirmar").sum()), len(pres)),
    a_confirmar=int((cls == "a confirmar").sum()), a_confirmar_pct=pct(int((cls == "a confirmar").sum()), len(pres)),
    por_classe=cls.value_counts().to_dict(),
    detalhe_consolidacao={"X ou x convertidos em presença": int(pres.apply(lambda v: (not pd.isna(v)) and norm_texto(v) == "x").sum()),
                          "traço (-) convertido em falta": int(pres.apply(lambda v: (not pd.isna(v)) and str(v).strip() == "-").sum()),
                          "campos vazios pendentes": int(pres.isna().sum())},
    grafias_registrado_por=int(fre_ok["Registrado por"].dropna().nunique()))

# outros formatos
f_ = fam_ok
tel_dig = f_["Telefone"].apply(lambda v: len(re.sub(r"\D", "", str(v))) if not vazio(v) else None)
tel_ok = int(tel_dig.apply(lambda n: n in (10, 11) if n is not None else False).sum())
tel_pre = int((~f_["Telefone"].apply(vazio)).sum())
tel_formatos = f_["Telefone"].dropna().apply(lambda v: re.sub(r"\d", "9", str(v))).value_counts().to_dict()
renda = f_["Renda Familiar"]
renda_texto = int(renda.apply(lambda v: (not vazio(v)) and str(v).strip().startswith("R$")).sum())
renda_num = int(renda.apply(lambda v: (not vazio(v)) and bool(re.fullmatch(r"[\d.,]+", str(v).strip()))).sum())
cpf_ok = int(f_["CPF"].apply(lambda v: (not vazio(v)) and bool(re.fullmatch(r"\*{3}\.\d{3}\.\d{3}-\*{2}", str(v).strip()))).sum())
doa_val_txt = int(doa["Valor Estimado"].apply(lambda v: (not vazio(v)) and str(v).strip().startswith("R$")).sum())
doa_val_num = int(doa["Valor Estimado"].apply(lambda v: (not vazio(v)) and bool(re.fullmatch(r"[\d.,]+", str(v).strip()))).sum())
doa_qtd_num = int(doa["Quantidade"].apply(lambda v: (not vazio(v)) and bool(re.fullmatch(r"\d+([.,]\d+)?", str(v).strip()))).sum())
doa_qtd_pre = int((~doa["Quantidade"].apply(vazio)).sum())
unid = doa["Unidade"].dropna().str.strip()
unid_n = unid.apply(lambda u: {"un": "un", "unid.": "un", "unid": "un"}.get(u.lower(), u.lower()))
R["outros_formatos"] = dict(
    telefone=dict(preenchidos=tel_pre, validos_10_11_digitos=tel_ok, validos_pct=pct(tel_ok, tel_pre), formatos=tel_formatos),
    renda=dict(preenchidas=renda_num + renda_texto, numericas=renda_num, texto_com_R=renda_texto, numericas_pct=pct(renda_num, renda_num + renda_texto)),
    cpf=dict(preenchidos=int((~f_["CPF"].apply(vazio)).sum()), no_padrao_mascarado=cpf_ok),
    doacoes_valor=dict(preenchidos=doa_val_num + doa_val_txt, numericos=doa_val_num, texto_com_R=doa_val_txt),
    doacoes_quantidade=dict(preenchidas=doa_qtd_pre, numericas=doa_qtd_num, texto=doa_qtd_pre - doa_qtd_num),
    doacoes_unidade=dict(grafias_distintas=int(unid.nunique()), apos_unificar=int(unid_n.nunique())),
    situacao_participantes=dict(grafias=int(par_ok["Situação"].dropna().nunique()), apos_unificar=int(par_ok["Situação"].dropna().apply(norm_texto).nunique())),
    situacao_familias=dict(grafias=int(fam_ok["Situação"].dropna().nunique()), apos_unificar=int(fam_ok["Situação"].dropna().apply(norm_texto).nunique())),
    situacao_encaminhamentos=dict(grafias=int(enc["Situação"].dropna().nunique()), apos_unificar=int(enc["Situação"].dropna().apply(norm_texto).nunique())),
    doacoes_destino=dict(grafias=int(doa["Destino"].dropna().nunique()), apos_unificar=int(doa["Destino"].dropna().apply(norm_texto).nunique())),
    oficinas_inicio_fim=dict(formatos_fim=ofi["Fim"].dropna().apply(lambda v: "MM/AAAA" if re.fullmatch(r"\d{2}/\d{4}", str(v)) else "texto").value_counts().to_dict(),
                             fim_vazio=int(ofi["Fim"].isna().sum())),
)

# ------------------------------------------------------------------ 3) CONSISTÊNCIA (chaves e referências)
cod_of = set(ofi["Cod"].str.strip().str.upper())
nome_of = {norm_texto(n): c.strip().upper() for n, c in zip(ofi["Oficina"], ofi["Cod"])}
cod_fam = set(fam_ok["Cod"].str.strip().str.upper())

par_ok["cod_n"] = par_ok["Cod"].apply(lambda v: None if vazio(v) else str(v).strip().upper())
par_ok["nome_k"] = par_ok["Nome"].apply(lambda v: None if vazio(v) else norm_nome(v))
cod_par = set(par_ok["cod_n"].dropna())
# nome -> conjunto de códigos
nome2cod = {}
for k, c in zip(par_ok["nome_k"], par_ok["cod_n"]):
    if k and pd.notna(c):
        nome2cod.setdefault(k, set()).add(c)
nomes_sem_cod = set(par_ok.loc[par_ok["cod_n"].isna() & par_ok["nome_k"].notna(), "nome_k"])


def resolver_participante(v):
    """devolve (situação, código). situação: codigo_ok | codigo_orfao | nome_ok | nome_ambiguo | nome_sem_cadastro | vazio"""
    if vazio(v):
        return "vazio", None
    s = str(v).strip()
    if re.fullmatch(r"[Pp]\d{3}", s):
        c = s.upper()
        return ("codigo_ok", c) if c in cod_par else ("codigo_orfao", c)
    k = norm_nome(s)
    cods = nome2cod.get(k)
    if cods and len(cods) == 1:
        return "nome_ok", next(iter(cods))
    if cods and len(cods) > 1:
        return "nome_ambiguo", None
    return "nome_sem_cadastro", None


def resolver_oficina(v):
    if vazio(v):
        return "vazio", None
    s = str(v).strip()
    if re.fullmatch(r"OF\d{2}", s, re.I):
        c = s.upper()
        return ("codigo_ok", c) if c in cod_of else ("codigo_orfao", c)
    c = nome_of.get(norm_texto(s))
    return ("nome_ok", c) if c else ("nome_sem_cadastro", None)


fre_ok["p_sit"], fre_ok["p_cod"] = zip(*fre_ok["Participante"].apply(resolver_participante))
fre_ok["o_sit"], fre_ok["o_cod"] = zip(*fre_ok["Oficina"].apply(resolver_oficina))
fre_ok["dt"] = fre_ok["Data"].apply(ler_data)
n = len(fre_ok)
ps, os_ = fre_ok["p_sit"].value_counts().to_dict(), fre_ok["o_sit"].value_counts().to_dict()
R["consistencia_frequencia"] = dict(
    total=n,
    participante=dict(situacoes=ps,
                      identificavel_antes=ps.get("codigo_ok", 0), identificavel_antes_pct=pct(ps.get("codigo_ok", 0), n),
                      identificavel_depois=ps.get("codigo_ok", 0) + ps.get("nome_ok", 0),
                      identificavel_depois_pct=pct(ps.get("codigo_ok", 0) + ps.get("nome_ok", 0), n),
                      rejeitados=n - ps.get("codigo_ok", 0) - ps.get("nome_ok", 0)),
    oficina=dict(situacoes=os_,
                 identificavel_antes=os_.get("codigo_ok", 0), identificavel_antes_pct=pct(os_.get("codigo_ok", 0), n),
                 identificavel_depois=os_.get("codigo_ok", 0) + os_.get("nome_ok", 0),
                 identificavel_depois_pct=pct(os_.get("codigo_ok", 0) + os_.get("nome_ok", 0), n),
                 rejeitados=n - os_.get("codigo_ok", 0) - os_.get("nome_ok", 0),
                 codigos_orfaos=sorted(fre_ok.loc[fre_ok["o_sit"] == "codigo_orfao", "o_cod"].unique().tolist()),
                 ocorrencias_orfas_codigo=int((fre_ok["o_sit"] == "codigo_orfao").sum()),
                 ocorrencias_nome_sem_cadastro=int((fre_ok["o_sit"] == "nome_sem_cadastro").sum())),
    codigos_participante_orfaos=sorted(fre_ok.loc[fre_ok["p_sit"] == "codigo_orfao", "p_cod"].unique().tolist()),
)
R["consistencia_frequencia"]["nome_so_existe_em_cadastro_sem_codigo"] = int(
    fre_ok["Participante"].apply(lambda v: (not vazio(v)) and not re.fullmatch(r"[Pp]\d{3}", str(v).strip()) and norm_nome(v) in nomes_sem_cod).sum())
R["consistencia_frequencia"]["participantes_cadastrados_sem_codigo"] = len(nomes_sem_cod)
aceitas = fre_ok[fre_ok["p_sit"].isin(["codigo_ok", "nome_ok"]) & fre_ok["o_sit"].isin(["codigo_ok", "nome_ok"]) & fre_ok["dt"].notna()].copy()
R["consistencia_frequencia"]["registros_aceitos_na_carga"] = len(aceitas)
R["consistencia_frequencia"]["registros_aceitos_pct"] = pct(len(aceitas), n)
R["consistencia_frequencia"]["registros_rejeitados"] = n - len(aceitas)
R["consistencia_frequencia"]["registros_integros_antes"] = int(
    ((fre_ok["p_sit"] == "codigo_ok") & (fre_ok["o_sit"] == "codigo_ok")).sum())
R["consistencia_frequencia"]["registros_integros_antes_pct"] = pct(R["consistencia_frequencia"]["registros_integros_antes"], n)

# ---- relatório de carga da Frequência: cada registro rejeitado recebe UM motivo (o primeiro que falhar)
def motivo(r):
    if r["p_sit"] == "vazio": return "M1 participante não informado"
    if r["p_sit"] in ("codigo_orfao", "nome_sem_cadastro", "nome_ambiguo"): return "M2 participante inexistente no cadastro"
    if r["o_sit"] in ("vazio", "codigo_orfao", "nome_sem_cadastro"): return "M3 oficina inexistente no cadastro"
    if r["dt"] is None or pd.isna(r["dt"]): return "M4 data ilegível"
    return None


fre_ok["motivo"] = fre_ok.apply(motivo, axis=1)
ok_mask = fre_ok["motivo"].isna()
chave_rn3 = fre_ok["p_cod"].fillna("") + "|" + fre_ok["o_cod"].fillna("") + "|" + fre_ok["dt"].dt.strftime("%Y-%m-%d").fillna("")
rep = ok_mask & chave_rn3.duplicated(keep="first")
fre_ok.loc[rep, "motivo"] = "M5 lançamento repetido (RN-03)"
por_motivo = fre_ok["motivo"].dropna().value_counts().sort_index().to_dict()
aceitos_final = int(fre_ok["motivo"].isna().sum())
R["carga_frequencia"] = dict(linhas_lidas=len(fre), linhas_de_recado=int(fre_recado.sum()), registros=len(fre_ok), aceitos=aceitos_final,
                             aceitos_pct=pct(aceitos_final, len(fre_ok)), rejeitados=len(fre_ok) - aceitos_final,
                             rejeitados_pct=pct(len(fre_ok) - aceitos_final, len(fre_ok)), por_motivo=por_motivo,
                             aceitos_com_presenca_a_confirmar=int(((fre_ok["motivo"].isna()) & (fre_ok["Presença"].apply(classe_presenca) == "a confirmar")).sum()))

# Participantes -> Famílias
cf = par_ok["Cod Familia"].apply(lambda v: None if vazio(v) or str(v).strip() in ("??",) else str(v).strip().upper())
com_fam = int(cf.notna().sum())
fam_ok_n = int(cf.apply(lambda c: c in cod_fam if c else False).sum())
R["consistencia_participantes_familia"] = dict(participantes=len(par_ok), com_codigo_familia=com_fam, apontam_familia_existente=fam_ok_n,
                                               sem_vinculo_utilizavel=len(par_ok) - fam_ok_n, vinculo_ok_pct=pct(fam_ok_n, len(par_ok)))
# Encaminhamentos -> Participantes
def resolver_enc(v):
    s, c = resolver_participante(v)
    return s
enc_sit = enc["Participante"].apply(resolver_enc).value_counts().to_dict()
enc_ok = enc_sit.get("codigo_ok", 0) + enc_sit.get("nome_ok", 0)
R["consistencia_encaminhamentos"] = dict(total=len(enc), situacoes=enc_sit, identificavel_antes=enc_sit.get("codigo_ok", 0),
                                         identificavel_antes_pct=pct(enc_sit.get("codigo_ok", 0), len(enc)),
                                         identificavel_depois=enc_ok, identificavel_depois_pct=pct(enc_ok, len(enc)))

# datas posteriores à data de referência
fut = {}
for nome, serie in {"Participantes.Data Entrada": par_ok["Data Entrada"], "Doacoes.Data": doa["Data"], "Encaminhamentos.Data": enc["Data"],
                    "CadastroFamilias.Data Cadastro": fam_ok["Data Cadastro"], "Frequencia.Data": fre_ok["Data"]}.items():
    d = serie.apply(ler_data).dropna()
    fut[nome] = dict(com_data=len(d), posteriores=int((d > DATA_REF).sum()))
R["datas_posteriores_a_referencia"] = fut

# Doações: tipo × item
ITEM_TIPO = {  # tipo esperado para cada item distinto encontrado na aba Doacoes (regra de verificação cruzada)
    "agasalhos": {"vestuário"}, "camisetas": {"vestuário"},
    "arroz 5kg": {"alimento"}, "cesta básica": {"alimento"}, "feijão": {"alimento"}, "leite": {"alimento"}, "óleo": {"alimento"},
    "bola": {"brinquedo"}, "quebra-cabeça": {"brinquedo"},
    "cadernos": {"material escolar"}, "lápis de cor": {"material escolar"},
    "material de limpeza": {"higiene"}, "sabonete": {"higiene"},
    "pix": {"dinheiro"}, "transferência": {"dinheiro"},
}
itens = sorted(doa["Item"].dropna().str.lower().str.strip().unique().tolist())
R["doacoes_itens_distintos"] = itens
conhecidos = doa[doa["Item"].str.lower().str.strip().isin(ITEM_TIPO)]
incoer = conhecidos[~conhecidos.apply(lambda r: norm_texto(r["Tipo"]) in {sem_acento(x) for x in ITEM_TIPO[r["Item"].lower().strip()]}, axis=1)]
R["doacoes_tipo_item"] = dict(avaliadas=len(conhecidos), incoerentes=len(incoer), incoerentes_pct=pct(len(incoer), len(conhecidos)),
                              itens_fora_do_mapa=sorted(set(itens) - set(ITEM_TIPO)))

# ------------------------------------------------------------------ 4) UNICIDADE
dup = {}
# participantes por nome normalizado
grp = par_ok[par_ok["nome_k"].notna()].groupby("nome_k").size()
g_dup = grp[grp > 1]
dup["Participantes (mesma pessoa, nome normalizado)"] = dict(registros=int(par_ok["nome_k"].notna().sum()), grupos_duplicados=int(len(g_dup)),
        registros_em_grupos=int(g_dup.sum()), registros_excedentes=int((g_dup - 1).sum()),
        unicos_depois=int(par_ok["nome_k"].nunique()))
cg = par_ok[par_ok["cod_n"].notna()].groupby("cod_n").size()
dup["Participantes (mesmo código em mais de uma linha)"] = dict(grupos=int((cg > 1).sum()), registros_em_grupos=int(cg[cg > 1].sum()))
dup["Participantes (sem código)"] = dict(registros=int(par_ok["cod_n"].isna().sum()))
# famílias por nome do responsável normalizado
fam_ok["nome_k"] = fam_ok["Nome do Responsável"].apply(lambda v: None if vazio(v) else norm_nome(v))
gf = fam_ok[fam_ok["nome_k"].notna()].groupby("nome_k").size()
dup["Famílias (responsável com nome normalizado igual)"] = dict(registros=int(fam_ok["nome_k"].notna().sum()), grupos_duplicados=int((gf > 1).sum()),
        registros_em_grupos=int(gf[gf > 1].sum()), registros_excedentes=int((gf[gf > 1] - 1).sum()))
# frequência RN-03 (após resolver)
chave = aceitas["p_cod"] + "|" + aceitas["o_cod"] + "|" + aceitas["dt"].dt.strftime("%Y-%m-%d")
cc = chave.value_counts()
dup["Frequência (mesmo participante, oficina e data — RN-03)"] = dict(registros_avaliados=len(aceitas), grupos_duplicados=int((cc > 1).sum()),
        registros_em_grupos=int(cc[cc > 1].sum()), registros_excedentes=int((cc[cc > 1] - 1).sum()))
# doações / encaminhamentos duplicados (todos os campos iguais após normalizar)
kd = doa.apply(lambda r: "|".join(norm_texto(x) for x in r.values), axis=1).value_counts()
dup["Doações (linhas idênticas após normalizar)"] = dict(registros=len(doa), grupos_duplicados=int((kd > 1).sum()), registros_excedentes=int((kd[kd > 1] - 1).sum()))
ke = enc.apply(lambda r: "|".join(norm_texto(x) for x in r.values), axis=1).value_counts()
dup["Encaminhamentos (linhas idênticas após normalizar)"] = dict(registros=len(enc), grupos_duplicados=int((ke > 1).sum()), registros_excedentes=int((ke[ke > 1] - 1).sum()))
R["unicidade"] = dup

# situação dos participantes (após unificar a caixa) e efeito da duplicidade
par_ok["sit_n"] = par_ok["Situação"].apply(lambda v: None if vazio(v) else norm_texto(v))
sit_linhas = par_ok["sit_n"].value_counts().to_dict()
primeiro = par_ok[par_ok["nome_k"].notna()].drop_duplicates("nome_k", keep="first")
conflito = 0
for k, g in par_ok[par_ok["nome_k"].notna()].groupby("nome_k"):
    if len(g) > 1 and g["sit_n"].nunique() > 1:
        conflito += 1
R["participantes_situacao"] = dict(linhas=sit_linhas, ativos_linhas=int(sit_linhas.get("ativo", 0)),
                                   ativos_pessoas_primeira_ocorrencia=int((primeiro["sit_n"] == "ativo").sum()),
                                   pessoas_duplicadas_com_situacao_diferente=conflito,
                                   saidas_sem_data=int(sit_linhas.get("desligado", 0) + sit_linhas.get("transferido", 0)),
                                   base_tem_coluna_data_de_saida=False)

# ------------------------------------------------------------------ 5) CONCORDÂNCIA ENTRE FONTES (planilha × exportação do sistema antigo)
csv_ant = csv_ant.copy()
csv_ant["p_sit"], csv_ant["p_cod"] = zip(*csv_ant["PARTICIPANTE"].apply(resolver_participante))
csv_ant["o_sit"], csv_ant["o_cod"] = zip(*csv_ant["OFICINA"].apply(resolver_oficina))
csv_ant["dt"] = csv_ant["DATA"].apply(ler_data)
a = fre_ok[fre_ok["dt"].notna() & fre_ok["p_cod"].notna() & fre_ok["o_cod"].notna()].copy()
b = csv_ant[csv_ant["dt"].notna() & csv_ant["p_cod"].notna() & csv_ant["o_cod"].notna()].copy()
for df_ in (a, b):
    df_["k"] = df_["p_cod"] + "|" + df_["o_cod"] + "|" + df_["dt"].dt.strftime("%Y-%m-%d")
ka, kb = a["k"].value_counts(), b["k"].value_counts()
comuns = int(sum(min(ka.get(k, 0), kb.get(k, 0)) for k in set(ka.index) | set(kb.index)))
# concordância da marca de presença entre fontes nas chaves comuns (chaves únicas dos dois lados)
ua = a.drop_duplicates("k", keep=False).set_index("k")
ub = b.drop_duplicates("k", keep=False).set_index("k")
chaves_u = ua.index.intersection(ub.index)
marca_igual = int(sum(norm_texto(ua.loc[k, "Presença"]) == norm_texto(ub.loc[k, "PRESENCA"]) if (not pd.isna(ua.loc[k, "Presença"]) and not pd.isna(ub.loc[k, "PRESENCA"])) else (pd.isna(ua.loc[k, "Presença"]) and pd.isna(ub.loc[k, "PRESENCA"])) for k in chaves_u))
R["concordancia_fontes"] = dict(
    registros_planilha=len(fre_ok), registros_exportacao=len(csv_ant),
    comparaveis_planilha=len(a), comparaveis_exportacao=len(b),
    lancamentos_em_comum=comuns, em_comum_pct_da_planilha=pct(comuns, len(fre_ok)),
    so_na_planilha=len(a) - comuns, so_na_exportacao=len(b) - comuns,
    chaves_unicas_comparadas=len(chaves_u), marca_igual=marca_igual, marca_igual_pct=pct(marca_igual, len(chaves_u)))

# ------------------------------------------------------------------ 6) ATUALIDADE
dts = fre_ok["dt"].dropna()
meses = sorted(dts.dt.strftime("%Y-%m").unique())
R["atualidade"] = dict(
    frequencia_primeiro=dts.min().strftime("%d/%m/%Y"), frequencia_ultimo=dts.max().strftime("%d/%m/%Y"), frequencia_meses_com_dado=len(meses),
    frequencia_por_ano={str(k): int(v) for k, v in dts.dt.year.value_counts().sort_index().items()},
    oficinas_inicio=sorted(ofi["Início"].dropna().unique().tolist()),
    oficinas_fim=ofi["Fim"].fillna("(vazio)").value_counts().to_dict(),
    frequencia_por_mes={k: int(v) for k, v in dts.dt.strftime("%Y-%m").value_counts().sort_index().items()},
    media_mensal=round(len(dts) / len(meses), 1),
    of08_setembro_2025=int(((fre_ok["o_cod"] == "OF08") & (fre_ok["dt"].dt.strftime("%Y-%m") == "2025-09")).sum()),
    of08_outros_meses_media=round(float(fre_ok[(fre_ok["o_cod"] == "OF08") & (fre_ok["dt"].dt.strftime("%Y-%m") != "2025-09")].groupby(fre_ok["dt"].dt.strftime("%Y-%m")).size().mean()), 1),
    base_tem_data_de_insercao=False)

# ------------------------------------------------------------------ 7) CSV doações 2026 × aba Doacoes
def chave_doa(df):
    return df.apply(lambda r: "|".join(norm_texto(x) for x in [r["Data"], r["Doador"], r["Tipo"], r["Item"], r["Valor Estimado"]]), axis=1)
doa["dt"] = doa["Data"].apply(ler_data); csv_doa["dt"] = csv_doa["Data"].apply(ler_data)
def k2(df):
    return df["dt"].dt.strftime("%Y-%m-%d").fillna("?") + "|" + df["Doador"].apply(norm_texto) + "|" + df["Tipo"].apply(norm_texto) + "|" + df["Item"].apply(norm_texto)
sa, sb = set(k2(doa)), set(k2(csv_doa))
doa26 = doa[doa["dt"].apply(lambda d: d is not None and d.year == 2026)]
R["doacoes_csv_2026"] = dict(
    linhas_csv=len(csv_doa), doacoes_2026_na_aba=len(doa26), linhas_csv_ja_na_aba=int(sum(1 for k in k2(csv_doa) if k in sa)),
    linhas_csv_novas=int(sum(1 for k in k2(csv_doa) if k not in sa)),
    csv_so_2026=bool(csv_doa["dt"].apply(lambda d: d is not None and d.year == 2026).all()))

R["situacoes"] = dict(
    participantes=par_ok["Situação"].dropna().apply(norm_texto).value_counts().to_dict(),
    participantes_sem_situacao=int(par_ok["Situação"].isna().sum()),
    familias=fam_ok["Situação"].dropna().apply(norm_texto).value_counts().to_dict(),
    encaminhamentos=enc["Situação"].dropna().apply(norm_texto).value_counts().to_dict())
R["telefone_inutilizavel"] = dict(vazios=int(f_["Telefone"].apply(vazio).sum()), sem_ddd=int(tel_dig.apply(lambda n: n == 9 if n is not None else False).sum()),
                                  texto=int(tel_pre - int(tel_dig.apply(lambda n: n is not None and n >= 9).sum())) )
json.dump(R, open("resultado_qualidade.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2, default=str)
print("ok -> resultado_qualidade.json")
