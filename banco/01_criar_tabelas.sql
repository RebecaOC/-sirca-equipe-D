-- =============================================================================
-- 01 - CRIACAO DAS TABELAS
-- Projeto Integrador 2026/2 - Instituto Semear
-- =============================================================================
-- Este script esta INCOMPLETO por design. A modelagem e trabalho da equipe.
-- Preencha a partir do modelo logico normalizado ate a terceira forma normal.
--
-- Regras que serao conferidas na avaliacao:
--   * toda tabela tem chave primaria explicita;
--   * todo relacionamento tem chave estrangeira declarada;
--   * campos obrigatorios usam NOT NULL;
--   * dominios fechados usam CHECK (exemplo: situacao, tipo de presenca);
--   * nomes em minusculas, sem acento, no singular.
-- =============================================================================

-- Exemplo completo, para servir de referencia de estilo -----------------------
CREATE TABLE oficina (
    id_oficina      VARCHAR(10)  NOT NULL,
    nome            VARCHAR(120) NOT NULL,
    oficineiro      VARCHAR(120),
    dia_semana      VARCHAR(10)  NOT NULL,
    hora_inicio     TIME,
    hora_fim        TIME,
    sala            VARCHAR(40),
    vagas           INTEGER      CHECK (vagas > 0),
    data_inicio     DATE,
    data_fim        DATE,
    CONSTRAINT pk_oficina PRIMARY KEY (id_oficina),
    CONSTRAINT ck_oficina_dia CHECK (dia_semana IN ('segunda','terca','quarta','quinta','sexta'))
);

-- A PARTIR DAQUI E COM VOCES --------------------------------------------------

-- TODO: familia

-- TODO: participante (relaciona-se com familia)

-- TODO: frequencia (relaciona participante e oficina em uma data)
--       Atencao: qual e a chave primaria natural desta tabela?

-- TODO: doacao

-- TODO: encaminhamento

-- Indices sugeridos (crie somente depois de medir a consulta sem eles) ---------
-- CREATE INDEX ix_frequencia_participante ON frequencia (id_participante);
