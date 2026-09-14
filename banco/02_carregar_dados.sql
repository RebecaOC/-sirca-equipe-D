-- =============================================================================
-- 02 - CARGA DOS DADOS TRATADOS
-- =============================================================================
-- A carga e feita a partir dos arquivos gerados pela equipe em dados/tratados/,
-- NUNCA diretamente dos arquivos brutos.
--
-- Fluxo esperado:
--   1. script Python le dados/brutos/  ->  limpa  ->  grava dados/tratados/*.csv
--   2. este script carrega os csv tratados para as tabelas
--   3. as verificacoes ao final devem retornar zero linhas
-- =============================================================================

-- Exemplo de carga (ajuste o caminho absoluto no seu ambiente) ----------------
-- \copy oficina FROM 'dados/tratados/oficina.csv' WITH (FORMAT csv, HEADER true);

-- TODO: carga de familia
-- TODO: carga de participante
-- TODO: carga de frequencia
-- TODO: carga de doacao
-- TODO: carga de encaminhamento

-- =============================================================================
-- VERIFICACOES OBRIGATORIAS APOS A CARGA
-- Todas devem retornar ZERO linhas. Se retornarem algo, a limpeza falhou.
-- =============================================================================

-- 1. Participante apontando para familia inexistente
-- SELECT p.* FROM participante p
--  LEFT JOIN familia f ON f.id_familia = p.id_familia
--  WHERE f.id_familia IS NULL;

-- 2. Frequencia apontando para oficina inexistente
-- SELECT fr.* FROM frequencia fr
--  LEFT JOIN oficina o ON o.id_oficina = fr.id_oficina
--  WHERE o.id_oficina IS NULL;

-- 3. Presenca fora do dominio definido
-- SELECT DISTINCT presenca FROM frequencia
--  WHERE presenca NOT IN ('presente','falta','justificada');

-- 4. Datas fora do intervalo plausivel do projeto
-- SELECT * FROM frequencia WHERE data_encontro < DATE '2024-01-01'
--     OR data_encontro > CURRENT_DATE;

-- 5. Duplicidade de participante na mesma oficina e data
-- SELECT id_participante, id_oficina, data_encontro, COUNT(*)
--   FROM frequencia GROUP BY 1,2,3 HAVING COUNT(*) > 1;
