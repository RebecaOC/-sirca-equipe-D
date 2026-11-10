#!/usr/bin/env python3
# =====================================================================
# E2.4 — CARGA DA BASE REAL (SIRCA — Instituto Semear — Equipe D)
#
# Lê a base bruta oficial (Instituto_Semear_planilhas_operacionais_2024-2026.xlsx),
# trata, valida (RF-07, RN-01, RN-03, RN-04) e carrega no PostgreSQL.
# Todo registro que viola regra vai para CARGA_REJEICAO (RNF-01):
# nada é descartado em silêncio.
#
# Uso:   python3 E2.4_carga_base_real.py  <base.xlsx>  <banco>
# Requer: openpyxl e o cliente `psql` no PATH (sem driver Python).
# ATENÇÃO (Dossiê §7): a base NÃO deve ser publicada em repositório aberto;
# este script não a contém — ele só a lê do caminho informado.
# =====================================================================
import sys, re, csv, os, subprocess, tempfile, unicodedata, calendar, collections
import openpyxl
from datetime import date

XLSX, DB = sys.argv[1], sys.argv[2]
HERE = os.path.dirname(os.path.abspath(__file__))
DDL = os.path.join(HERE, 'E2.4_script_criacao_banco.sql')

# ---------- Tabela de conversão das marcas (RN-01) ----------------------
# Documentada no E2.4 §5.1. Marcas sem equivalente seguro -> rejeitadas.
CONV = {
    'presente': 'presente', 'p': 'presente', '1': 'presente', 'x': 'presente',
    'falta': 'falta', 'f': 'falta', 'faltou': 'falta', '0': 'falta',
    'justificada': 'falta_justificada', 'j': 'falta_justificada',
}  # '-' e célula vazia: sem equivalente definido -> RN-01 (rejeita)

MESES = {'jan':1,'fev':2,'mar':3,'abr':4,'mai':5,'jun':6,'jul':7,'ago':8,'set':9,'out':10,'nov':11,'dez':12}

def sem_acento(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')

def nome_norm(s):
    return re.sub(r'\s+', ' ', sem_acento(str(s)).strip().lower())

def vazio(v):
    return v is None or str(v).strip().lower() in ('', '-', 'n/i', 'nao informado', 'não informado', '??', 'none')

def pdata(v):
    """Aceita os 5 formatos da base. Ano com 2 dígitos: <=26 -> 20xx, senão 19xx."""
    if v is None: return None
    if hasattr(v, 'year'): return date(v.year, v.month, v.day)
    s = str(v).strip().lower()
    m = re.fullmatch(r'(\d{4})-(\d{2})-(\d{2})', s)
    if m: y, mo, d = map(int, m.groups())
    else:
        m = re.fullmatch(r'(\d{1,2})[/-](\d{1,2})[/-](\d{2}|\d{4})', s)
        if m:
            d, mo, y = map(int, m.groups())
            if y < 100: y += 2000 if y <= 26 else 1900
        else:
            m = re.fullmatch(r'(\d{1,2}) de ([a-zç]{3}) de (\d{4})', s)
            if not m or m.group(2) not in MESES: return None
            d, mo, y = int(m.group(1)), MESES[m.group(2)], int(m.group(3))
    try: return date(y, mo, d)
    except ValueError: return None

def pdinheiro(v):
    if v is None: return None
    if isinstance(v, (int, float)): return float(v)
    s = re.sub(r'[Rr]\$|\s', '', str(v))
    if not re.fullmatch(r'[\d.,]+', s): return None
    if ',' in s: s = s.replace('.', '').replace(',', '.')
    return float(s)

def nome_proprio(n):
    # só normaliza caixa quando o nome veio todo em maiúsculas ou todo em minúsculas
    if not (n.isupper() or n.islower()): return n
    return ' '.join(w if w in ('de','da','do','dos','das','e') else w.capitalize() for w in n.lower().split())

def limpa(v):
    return re.sub(r'\s+', ' ', str(v)).strip() if v is not None else None

wb = openpyxl.load_workbook(XLSX, data_only=True)
def linhas(nome):
    # (nº da linha na planilha, tupla)  — cabeçalho é a linha 1
    return [(i, r) for i, r in enumerate(wb[nome].iter_rows(values_only=True), 1) if i > 1]
def bruto(r): return ' | '.join('' if x is None else str(x) for x in r)

rej = []     # (arquivo, linha, bruto, regra, motivo)
cont = collections.Counter()   # contadores do relatório
def rejeita(arq, i, r, regra, motivo):
    rej.append((arq, i, bruto(r), regra, motivo)); cont[(arq, regra)] += 1

# ---------- OFICINEIRO / OFICINA ---------------------------------------
oficineiros, ofi_idx, oficinas, of_nome = {}, {}, [], {}
for i, r in linhas('Oficinas'):
    cod, nome, ofn, dia, hor, sala, vagas, ini, fim = r
    m = re.match(r'(Prof\.|Ed\.)\s+(.*)', limpa(ofn))
    titulo, onome = (m.group(1), m.group(2)) if m else (None, limpa(ofn))
    if onome not in oficineiros: oficineiros[onome] = ('OFI%02d' % (len(oficineiros)+1), titulo)
    h = re.fullmatch(r'(\d{2}:\d{2}) às (\d{2}:\d{2})', limpa(hor))
    def mes(v, ultimo):
        m = re.fullmatch(r'(\d{2})/(\d{4})', str(v or '').strip())
        if not m: return None
        mo, y = int(m.group(1)), int(m.group(2))
        return date(y, mo, calendar.monthrange(y, mo)[1] if ultimo else 1)
    periodo = 'manhã' if int(h.group(1)[:2]) < 12 else 'tarde'
    oficinas.append((cod.strip(), limpa(nome), vagas, mes(ini, False), mes(fim, True),
                     h.group(1), h.group(2), limpa(dia), limpa(sala), periodo, oficineiros[onome][0]))
    of_nome[nome_norm(nome)] = cod.strip()
of_cods = {o[0] for o in oficinas}

# ---------- FAMILIA -----------------------------------------------------
SIT_FAM = {'ativo': 'ativa', 'inativo': 'inativa', 'desligado': 'inativa'}
familias = {}
for i, r in linhas('CadastroFamilias'):
    cod, nome, cpf, nasc, end, bairro, tel, dep, renda, dcad, sit, obs = r
    if all(x is None for x in r): rejeita('CadastroFamilias', i, r, 'linha_recado', 'linha em branco'); continue
    cod = limpa(cod).upper() if cod else None
    dc = pdata(dcad)
    if not cod or not limpa(nome) or dc is None or limpa(sit or '').lower() not in SIT_FAM:
        rejeita('CadastroFamilias', i, r, 'outro', 'campo obrigatório ausente/ilegível (código, nome, data de cadastro ou situação)'); continue
    if cod in familias:
        rejeita('CadastroFamilias', i, r, 'outro', 'código de família repetido'); continue
    logr, num = None, None
    if not vazio(end):
        m = re.fullmatch(r'(.*?),\s*nº\s*(\S+)', limpa(end))
        logr, num = (m.group(1), m.group(2)) if m else (limpa(end), None)
    rd = pdinheiro(renda) if not vazio(renda) else None
    nd = int(dep) if dep is not None and str(dep).strip().isdigit() else None
    fone = None if vazio(tel) or re.search('[a-zA-Z]', str(tel)) else limpa(tel)
    familias[cod] = (cod, logr, num, None if vazio(bairro) else limpa(bairro), limpa(cpf), pdata(nasc),
                     nd, rd, fone, limpa(nome), dc, SIT_FAM[limpa(sit).lower()], limpa(obs))

# ---------- PARTICIPANTE ------------------------------------------------
SIT_PART = {'ativo': 'matriculado', 'desligado': 'desligado', 'transferido': 'desligado'}
part, alias = {}, {}          # alias: nome normalizado -> lista de códigos
nao_carregados = {}           # participantes rejeitados (código e nome) -> motivo, p/ explicar rejeições em cascata
semcodigo = []
def regista_alias(n, c): alias.setdefault(nome_norm(n), set()).add(c)
for i, r in linhas('Participantes'):
    cod, nome, cf, nasc, esc, turma, dent, sit = r
    if all(x is None for x in r): rejeita('Participantes', i, r, 'linha_recado', 'linha em branco'); continue
    if vazio(cod): semcodigo.append((i, r)); continue
    cod = limpa(cod).upper()
    if cod in part:
        rejeita('Participantes', i, r, 'outro', f'duplicidade: {cod} já carregado'); continue
    cf = limpa(cf).upper() if cf else None
    if cf not in familias:
        rejeita('Participantes', i, r, 'RF-07', f'Cod_Familia "{cf}" inexistente em FAMILIA')
        nao_carregados[cod] = nao_carregados[nome_norm(nome or '')] = cod; continue
    dn, de = pdata(nasc), pdata(dent)
    if dn is None or de is None or not limpa(nome) or limpa(sit or '').lower() not in SIT_PART:
        rejeita('Participantes', i, r, 'outro', 'campo obrigatório ausente/ilegível (nascimento, entrada, nome ou situação)'); continue
    escola = None if vazio(esc) else limpa(esc)
    ta = None if vazio(turma) else limpa(turma)
    part[cod] = (cod, cf, nome_proprio(limpa(nome)), dn,
                 SIT_PART[limpa(sit).lower()], escola, None, ta, de, None)
    regista_alias(nome, cod)
# linhas sem código = reentradas do mesmo participante (nome abreviado/caixa diferente)
def chave(cf, dn, nome):
    t = nome_norm(nome).replace('.', '').split()
    return (cf, dn, t[0], t[-1])
idx = {chave(p[1], p[3], p[2]): c for c, p in part.items()}
for i, r in semcodigo:
    cod, nome, cf, nasc, *_ = r
    alvo = idx.get(chave(limpa(cf or '').upper(), pdata(nasc), nome)) if nome else None
    if alvo:
        regista_alias(nome, alvo)
        rejeita('Participantes', i, r, 'outro', f'duplicidade: reentrada sem código de {alvo} (nome abreviado/caixa diferente)')
    else:
        rejeita('Participantes', i, r, 'outro', 'participante sem código e sem correspondente identificável')
amb = {n for n, cs in alias.items() if len(cs) > 1}

def acha_participante(v):
    if v is None or not limpa(v): return None, 'participante ausente'
    s = limpa(v)
    if re.fullmatch(r'[Pp]\d+', s) and s.upper() in nao_carregados or nome_norm(s) in nao_carregados:
        return None, 'participante %s não carregado (sua família não existe em FAMILIA)' % nao_carregados[s.upper() if re.fullmatch(r'[Pp]\d+', s) else nome_norm(s)]
    if re.fullmatch(r'[Pp]\d+', s):
        c = s.upper()
        return (c, None) if c in part else (None, f'Cod_Participante "{c}" inexistente em PARTICIPANTE')
    n = nome_norm(s)
    if n in amb: return None, f'nome "{s}" ambíguo (mais de um código)'
    cs = alias.get(n)
    if cs: return next(iter(cs)), None
    return None, f'participante "{s}" não localizado em PARTICIPANTE'

# ---------- FREQUENCIA --------------------------------------------------
freq, vistos = [], {}
REG = lambda s: {'neusa':'Neusa','marli':'Marli','coordenação':'Coordenação','coordenacao':'Coordenação'}.get(s.lower(), s.title()) if s else None
marcas = collections.Counter(); marcas_ok = collections.Counter(); marcas_rn01 = collections.Counter()
for i, r in linhas('Frequencia'):
    dt, of, p, marca, quem = r
    if all(x is None for x in r) or (isinstance(dt, str) and dt.startswith('OBS') and of is None):
        rejeita('Frequencia', i, r, 'linha_recado', 'linha em branco ou de recado, não é registro de presença'); continue
    marcas[str(marca).strip() if marca is not None else '(vazio)'] += 1
    d = pdata(dt)
    if d is None: rejeita('Frequencia', i, r, 'outro', 'data ilegível'); continue
    ofk = limpa(of).upper() if of else None
    ofc = ofk if ofk in of_cods else of_nome.get(nome_norm(of or ''))
    if not ofc: rejeita('Frequencia', i, r, 'RF-07', f'oficina "{limpa(of)}" inexistente em OFICINA'); continue
    pc, erro = acha_participante(p)
    if not pc: rejeita('Frequencia', i, r, 'RF-07', erro); continue
    v = CONV.get(str(marca).strip().lower()) if marca is not None else None
    if not v:
        marcas_rn01[str(marca).strip() if marca is not None else '(vazio)'] += 1
        rejeita('Frequencia', i, r, 'RN-01', f'marca "{marca}" sem equivalente nos 3 valores'); continue
    k = (pc, ofc, d)
    if k in vistos:
        rejeita('Frequencia', i, r, 'RN-03', f'repete (participante, oficina, data) da linha {vistos[k]}'); continue
    ds = part[pc][9]
    if ds is not None and d >= ds:
        rejeita('Frequencia', i, r, 'RN-04', 'frequência após a data de desligamento'); continue
    vistos[k] = i
    marcas_ok[str(marca).strip()] += 1
    freq.append((pc, ofc, d, v, REG(limpa(quem)) if quem and limpa(quem) != '?' else 'não informado (carga inicial)'))

# ---------- ENCAMINHAMENTO ----------------------------------------------
SIT_ENC = {'atendido': 'concluido', 'aguardando': 'em_andamento', 'encaminhado': 'aberto', 'sem retorno': 'aberto'}
enc = []
for i, r in linhas('Encaminhamentos'):
    dt, p, serv, org, sit, ret = r
    d = pdata(dt)
    pc, erro = acha_participante(p)
    if d is None or vazio(serv): rejeita('Encaminhamentos', i, r, 'outro', 'data ilegível ou serviço ausente'); continue
    if not pc: rejeita('Encaminhamentos', i, r, 'RF-07', erro); continue
    enc.append((pc, limpa(serv), None if vazio(org) else limpa(org), d,
                SIT_ENC.get(limpa(sit).lower()) if sit and not vazio(sit) else None,
                None if vazio(ret) else limpa(ret)))

# ---------- DOACAO -------------------------------------------------------
doa = []
for i, r in linhas('Doacoes'):
    dt, doador, tipo, item, qt, un, dest, val = r
    d = pdata(dt)
    if d is None or vazio(doador) or vazio(item) or vazio(tipo):
        rejeita('Doacoes', i, r, 'outro', 'campo obrigatório ausente/ilegível'); continue
    q = pdinheiro(qt) if qt is not None and not vazio(qt) and re.fullmatch(r'[\d.,]+', str(qt).strip()) else None
    m = re.fullmatch(r'Oficina (OF\d+)', limpa(dest or ''))
    codof = m.group(1) if m and m.group(1) in of_cods else None
    if m and not codof: rejeita('Doacoes', i, r, 'RF-07', f'oficina "{m.group(1)}" inexistente'); continue
    doa.append((codof, limpa(tipo), limpa(item), q, None if vazio(un) else limpa(un),
                None if vazio(dest) else limpa(dest), pdinheiro(val) if not vazio(val) else None, d, limpa(doador)))

# ---------- GRAVAÇÃO (CSV + \copy) ---------------------------------------
tmp = tempfile.mkdtemp()
def csvw(nome, linhas_):
    p = os.path.join(tmp, nome + '.csv')
    with open(p, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f); [w.writerow(['\\N' if x is None else x for x in l]) for l in linhas_]
    return p
def psql(sql):
    subprocess.run(['psql', '-d', DB, '-v', 'ON_ERROR_STOP=1', '-q', '-c', sql], check=True)
def copy(tab, cols, linhas_):
    psql(f"\\copy {tab} ({cols}) FROM '{csvw(tab, linhas_)}' WITH (FORMAT csv, NULL '\\N')")

psql('DROP SCHEMA public CASCADE; CREATE SCHEMA public;')
subprocess.run(['psql', '-d', DB, '-v', 'ON_ERROR_STOP=1', '-q', '-f', DDL], check=True)
copy('OFICINEIRO', 'Cod_Oficineiro,Nome_do_Oficineiro,Titulo', [(c, n, t) for n, (c, t) in oficineiros.items()])
copy('OFICINA', 'Cod_Oficina,Nome_da_Oficina,Vagas,Inicio,Fim,Hora_Inicio,Hora_Fim,Dia,Sala,Periodo,Cod_Oficineiro', oficinas)
copy('FAMILIA', 'Cod_Familia,Logradouro,Numero,Bairro,CPF,Data_Nasc_Resp,N_Dependentes,Renda_Familiar,Telefone,Nome_do_Responsavel,Data_Cadastro,Situacao_Cadastral,Obs', familias.values())
copy('PARTICIPANTE', 'Cod_Participante,Cod_Familia,Nome,Data_Nascimento,Situacao_de_Matricula,Escola,Turma_Escolar,Ano_Escolar,Data_Entrada,Data_Situacao', part.values())
copy('FREQUENCIA', 'Cod_Participante,Cod_Oficina,Data_Frequencia,Presenca,Registrado_Por', freq)
copy('ENCAMINHAMENTO', 'Cod_Participante,Servico,Orgao,Data_Encaminhamento,Situacao_do_Encaminhamento,Retorno', enc)
copy('DOACAO', 'Cod_Oficina,Tipo,Item,Quantidade,Unidade,Destino,Valor_Estimado,Data_Doacao,Doador', doa)
copy('CARGA_REJEICAO', 'Arquivo_Origem,Linha_Origem,Conteudo_Bruto,Regra_Violada,Motivo', rej)

print('MARCAS BRUTAS (Frequencia):', dict(marcas))
print('MARCAS ACEITAS:', dict(marcas_ok)); print('MARCAS REJEITADAS RN-01:', dict(marcas_rn01))
print('REJEIÇÕES POR ARQUIVO/REGRA:')
for k, v in sorted(cont.items()): print('  ', k, v)
print('CARREGADOS: oficineiro', len(oficineiros), 'oficina', len(oficinas), 'familia', len(familias),
      'participante', len(part), 'frequencia', len(freq), 'encaminhamento', len(enc), 'doacao', len(doa))
