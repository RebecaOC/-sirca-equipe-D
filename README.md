# Projeto Integrador Semestral 2026/2 — Núcleo de Informação e Especificação da Solução

Curso de Engenharia de Software — Modalidade Semipresencial — UniEVANGÉLICA, campus Ceres.
Organização do caso: **Instituto Semear — Centro de Convivência e Fortalecimento de Vínculos**.

Este repositório é o ponto de partida de todas as equipes. Ele já vem com o ambiente descrito, a base de
dados bruta, os esqueletos de código e os scripts de banco comentados. **Nenhuma equipe começa do zero e
nenhuma equipe começa em vantagem.**

## O que você precisa fazer na primeira semana

1. Leia o `Edital do Projeto Integrador` (pasta `01_edital` do material inicial).
2. Instale o ambiente seguindo `ambiente/INSTALACAO.md`.
3. Rode `python ambiente/verificar_ambiente.py`. Só siga adiante quando todas as verificações passarem.
4. Preencha o `Termo de Constituição de Equipe` e coloque-o em `documentos/ciclo-1/`.
5. Abra as planilhas de `dados/brutos/` e leia `dados/LEIA-ME.md`. **Não modifique os arquivos brutos.**

## Estrutura das pastas

```
projeto-integrador-2026-2/
├── ambiente/       instalação, verificação e serviço de banco de dados
├── dados/
│   ├── brutos/     planilhas originais anonimizadas — SOMENTE LEITURA
│   └── tratados/   saídas da limpeza feita pela equipe
├── banco/          scripts SQL: criação, carga e consultas de negócio
├── componente/
│   ├── src/        código do componente de organização e recuperação
│   ├── testes/     testes automatizados (começam falhando, por design)
│   └── medicao/    instrumentação para medir desempenho
├── documentos/     entregáveis por ciclo
├── extensao/       produtos entregues à organização do caso
└── entregas/       pacotes enviados no AVA (PDF de cada ciclo)
```

## Regras do repositório

- Um commit por tarefa concluída, com mensagem descritiva em português. `ajustes` e `wip` não contam.
- Cada integrante commita com o próprio usuário. A contribuição individual é conferida pelos docentes.
- Nada de dado pessoal identificável neste repositório. A base fornecida já está anonimizada; qualquer dado
  novo coletado na sessão deve ser anonimizado antes do commit.
- Arquivos gerados (ambiente virtual, cache, dumps grandes) não entram no repositório — veja `.gitignore`.

## Calendário das entregas

| Ciclo | Semanas | Entrega |
|---|---|---|
| 1 — Definição | 1 a 5 | 20/09/2026 até 23h59 |
| 2 — Produção | 6 a 10 | 25/10/2026 até 23h59 |
| 3 — Produção e fechamento | 11 a 15 | 29/11/2026 até 23h59 (apresentação na semana 15) |
