-- =====================================================================
-- E2.4 — SCRIPT DE CRIAÇÃO DO BANCO (SIRCA — Instituto Semear)
-- Projeto Integrador 2026/2 — Equipe D — Ciclo 2
-- PostgreSQL. Normalizado até a 3ª Forma Normal (RF-06).
--
-- Rastreabilidade: cada tabela/constraint traz, em comentário, o
-- requisito, regra ou pergunta de negócio do Edital que a motiva,
-- e a referência ao documento do Ciclo 1 de onde o campo saiu.
-- =====================================================================

-- ---------------------------------------------------------------------
-- 1. FAMILIA
-- Campos conforme Dossiê §4 (CadastroFamilias) + E1.5 (modelo lógico
-- preliminar, já entregue no Ciclo 1).
-- CPF, Telefone e Data_Nasc_Resp não constam da lista do Dossiê §4 e
-- nenhuma das dez perguntas de negócio os exige; foram acrescentados
-- pela equipe no E1.5 e mantidos aqui por continuidade da entrega.
-- Obs é texto livre: não armazenar nele nenhum fato que uma consulta
-- precise ler (endereço, telefone, benefício) — isso reabriria a
-- violação de 1FN discutida no Ciclo 2 (campo com mais de um fato).
-- ---------------------------------------------------------------------
CREATE TABLE FAMILIA (
    Cod_Familia         VARCHAR(10)   PRIMARY KEY,
    Logradouro          VARCHAR(120),             -- NULL = endereço não informado na base (traço, n/i)
    Numero              VARCHAR(10),
    Bairro              VARCHAR(80),              -- NULL = bairro não informado ("??")
    CPF                 VARCHAR(14),              -- ver nota acima
    Data_Nasc_Resp       DATE,
    N_Dependentes       SMALLINT      CHECK (N_Dependentes >= 0),
    Renda_Familiar      NUMERIC(10,2) CHECK (Renda_Familiar >= 0),
    Telefone            VARCHAR(20),
    Nome_do_Responsavel VARCHAR(120)  NOT NULL,
    Data_Cadastro       DATE          NOT NULL,
    Situacao_Cadastral  VARCHAR(20)   NOT NULL
                         CHECK (Situacao_Cadastral IN ('ativa','inativa')),
                         -- RF-família ativa/inativa sustenta a PN-04
                         -- (famílias ATIVAS por bairro)
    Obs                 TEXT
);

-- ---------------------------------------------------------------------
-- 2. PARTICIPANTE
-- Campos conforme Dossiê §4 (nome, família, nascimento, escola, turma,
-- data de entrada) + E1.5. "Turma" do Dossiê é a turma ESCOLAR do
-- participante — renomeada Turma_Escolar para não colidir com o
-- sentido de "Turma" fixado no glossário (E1.4, conflito CF-01: Turma
-- = grupo de inscritos de uma oficina em um horário específico).
-- Data_Situacao é o campo que faltava para a RN-04 funcionar.
-- ---------------------------------------------------------------------
CREATE TABLE PARTICIPANTE (
    Cod_Participante      VARCHAR(10)  PRIMARY KEY,
    Cod_Familia           VARCHAR(10)  NOT NULL
                           REFERENCES FAMILIA (Cod_Familia),
    Nome                  VARCHAR(120) NOT NULL,
    Data_Nascimento       DATE         NOT NULL,
    Situacao_de_Matricula VARCHAR(20)  NOT NULL
                           CHECK (Situacao_de_Matricula IN
                                  ('matriculado','desligado','fila_espera')),
    Escola                VARCHAR(120),
    Turma_Escolar         VARCHAR(20),   -- Dossiê §4: "turma" (escolar)
    Ano_Escolar           VARCHAR(20),
    Data_Entrada          DATE         NOT NULL,
    Data_Situacao         DATE           -- RN-04: data do desligamento.
    -- A base do Instituto NÃO registra a data de desligamento/transferência
    -- (só a situação atual). Por isso a data é opcional na carga inicial e
    -- a RN-04 só é aplicada quando ela existir; a obrigatoriedade passa a
    -- valer nos lançamentos feitos pelo sistema. Pendência: "A confirmar"
    -- com o Instituto (data de desligamento).
);

-- ---------------------------------------------------------------------
-- 3. OFICINEIRO
-- Separado de OFICINA desde o E1.5 (decisão correta: nome e título do
-- educador não dependem da oficina, e sim do próprio educador —
-- evita a dependência parcial vista nos exercícios do Ciclo 2).
-- ---------------------------------------------------------------------
CREATE TABLE OFICINEIRO (
    Cod_Oficineiro      VARCHAR(10)  PRIMARY KEY,
    Nome_do_Oficineiro  VARCHAR(120) NOT NULL,
    Titulo               VARCHAR(80)
);

-- ---------------------------------------------------------------------
-- 4. OFICINA
-- Campos conforme Dossiê §4 (código, nome, oficineiro, dia, horário,
-- sala, vagas) + E1.5 (Inicio, Fim, Periodo).
-- ---------------------------------------------------------------------
CREATE TABLE OFICINA (
    Cod_Oficina      VARCHAR(10)  PRIMARY KEY,
    Nome_da_Oficina  VARCHAR(120) NOT NULL,
    Vagas            SMALLINT     NOT NULL CHECK (Vagas > 0),  -- usada na PN-06
    Inicio           DATE,
    Fim              DATE,
    Hora_Inicio      TIME         NOT NULL,
    Hora_Fim         TIME         NOT NULL,
    Dia              VARCHAR(20)  NOT NULL,
    Sala             VARCHAR(20)  NOT NULL,
    Periodo          VARCHAR(20),   -- manhã/tarde — Dossiê: "dois turnos"
    Cod_Oficineiro   VARCHAR(10)  NOT NULL
                     REFERENCES OFICINEIRO (Cod_Oficineiro),
    CHECK (Hora_Fim > Hora_Inicio)
);

-- ---------------------------------------------------------------------
-- 5. FREQUENCIA
-- Nomeada FREQUENCIA (não FREQUENTA) para bater com o nome que o
-- RF-06 usa ao listar as seis entidades obrigatórias: "família,
-- participante, oficina, FREQUÊNCIA, doação e encaminhamento".
--
-- RF-07: as duas FKs, sem ON DELETE CASCADE, fazem o banco recusar
--        presença de participante ou oficina inexistente (o teste
--        ao vivo da banca final é inserir um OF13 ou P999 e ver a
--        rejeição).
-- RF-10: Registrado_Por (quem) + Data_Hora_Lancamento (quando).
-- RN-01: domínio fechado em três valores. A base bruta tem 15 marcas
--        distintas (apuração real da equipe, EV-07 do E1.2) — a
--        conversão de cada marca para um dos três valores é feita na
--        CARGA (ver E2.4, seção 5.1), não aqui; aqui só se garante que nada
--        fora do domínio permanece após a carga.
-- RN-03: UNIQUE nas três colunas que identificam um registro de
--        presença no mundo real.
-- ---------------------------------------------------------------------
CREATE TABLE FREQUENCIA (
    Cod_Frequencia        SERIAL       PRIMARY KEY,
    Cod_Participante      VARCHAR(10)  NOT NULL
                           REFERENCES PARTICIPANTE (Cod_Participante),
    Cod_Oficina            VARCHAR(10)  NOT NULL
                           REFERENCES OFICINA (Cod_Oficina),
    Data_Frequencia        DATE         NOT NULL,   -- data do encontro
    Presenca               VARCHAR(20)  NOT NULL
                           CHECK (Presenca IN ('presente','falta','falta_justificada')),
    Registrado_Por         VARCHAR(80)  NOT NULL,   -- quem lançou (RF-10)
    Data_Hora_Lancamento   TIMESTAMP    NOT NULL DEFAULT now(),  -- quando (RF-10)
    CONSTRAINT uq_frequencia
        UNIQUE (Cod_Participante, Cod_Oficina, Data_Frequencia)  -- RN-03
);

-- ---------------------------------------------------------------------
-- 6. ENCAMINHAMENTO
-- Campos conforme Dossiê §4 (data, participante, serviço, órgão,
-- situação, retorno). Completo desde o E1.5, sem alteração.
-- ---------------------------------------------------------------------
CREATE TABLE ENCAMINHAMENTO (
    Cod_Encaminhamento       SERIAL       PRIMARY KEY,
    Cod_Participante         VARCHAR(10)  NOT NULL
                             REFERENCES PARTICIPANTE (Cod_Participante),
    Servico                  VARCHAR(120) NOT NULL,
    Orgao                    VARCHAR(120),
    Data_Encaminhamento      DATE         NOT NULL,
    Situacao_do_Encaminhamento VARCHAR(30)   -- NULL: situação vazia ou "-" na base
                             CHECK (Situacao_do_Encaminhamento IN
                                    ('aberto','em_andamento','concluido')),
    Retorno                  TEXT
);

-- ---------------------------------------------------------------------
-- 7. DOACAO
-- Campos conforme Dossiê §4 (data, doador, tipo, valor estimado,
-- destino) + E1.5 (Item, Quantidade, Unidade — mais granular, boa
-- prática de 1FN). FK para OFICINA é opcional, conforme o E1.5
-- (nem toda doação é destinada a uma oficina específica).
-- ---------------------------------------------------------------------
CREATE TABLE DOACAO (
    Cod_Doacao      SERIAL        PRIMARY KEY,
    Cod_Oficina     VARCHAR(10)   REFERENCES OFICINA (Cod_Oficina),  -- opcional
    Tipo            VARCHAR(40)   NOT NULL,
    Item            VARCHAR(120)  NOT NULL,
    Quantidade      NUMERIC(10,2) CHECK (Quantidade > 0),   -- NULL: "várias"/vazio
    Unidade         VARCHAR(20),
    Destino         VARCHAR(120),
    Valor_Estimado  NUMERIC(10,2) CHECK (Valor_Estimado >= 0),
    Data_Doacao     DATE          NOT NULL,
    Doador          VARCHAR(120)  NOT NULL
);

-- =====================================================================
-- 8. CARGA_REJEICAO — tabela de apoio para a RNF-01
--
-- RNF-01: "A carga inicial rejeita e reporta todo registro que viole
-- uma regra, sem descartar em silêncio." A base bruta tem registros
-- com participante/oficina inexistente (OF13, P999 — EV-08 do E1.2),
-- marcas de presença fora do domínio antes da conversão, e ao menos
-- 17 linhas de recado misturadas aos dados (identificadas pela
-- própria equipe na aba 1 do E1.7: "2.256 linhas - 17 linhas de
-- recado = 2.239 registros válidos"). Nenhuma dessas é descartada
-- sem registro: o processo de carga grava aqui o motivo da rejeição
-- antes de tentar o INSERT em FREQUENCIA.
-- =====================================================================
CREATE TABLE CARGA_REJEICAO (
    Id_Rejeicao      SERIAL       PRIMARY KEY,
    Arquivo_Origem   VARCHAR(60)  NOT NULL,   -- ex.: 'Frequencia.csv'
    Linha_Origem     INTEGER      NOT NULL,   -- nº da linha no arquivo bruto
    Conteudo_Bruto   TEXT         NOT NULL,   -- a linha como veio, sem alteração
    Regra_Violada    VARCHAR(20)  NOT NULL
                     CHECK (Regra_Violada IN
                            ('RF-07','RN-01','RN-03','RN-04','linha_recado','outro')),
    Motivo           TEXT         NOT NULL,
    Data_Carga       TIMESTAMP    NOT NULL DEFAULT now()
);

-- =====================================================================
-- NOTA DE PREMISSA — PN-06 (oficinas com menos de 60% das vagas
-- ocupadas): nenhum dos documentos do caso prevê uma tabela de
-- matrícula separada da frequência. A equipe adota, como premissa de
-- trabalho, que "ocupação da oficina" = contagem de participantes
-- DISTINTOS com ao menos um registro em FREQUENCIA para aquela
-- oficina no período. Se a organização confirmar que matrícula e
-- frequência são eventos diferentes, isso vira uma das cinco
-- perguntas da janela escrita da semana 9, e uma tabela MATRICULA
-- (Cod_Participante, Cod_Oficina, Data_Matricula) pode ser acrescentada
-- sem alterar as demais tabelas.
-- =====================================================================
