# Base de dados bruta — leia antes de abrir

## Proveniência

Os arquivos desta pasta reproduzem os controles operacionais reais do **Instituto Semear**, mantidos em
planilhas soltas e cadernos de papel entre 2024 e 2026. Os dados foram **anonimizados**: nomes foram
substituídos, o CPF aparece parcialmente mascarado, endereços foram generalizados e nenhum telefone
corresponde a linha existente. A organização é apresentada sob nome fictício.

Uso **exclusivamente acadêmico**, nos termos do Edital e da Lei nº 13.709/2018. É vedado publicar esta base
em repositório de acesso aberto ou utilizá-la fora deste projeto.

## Arquivos

| Arquivo | Conteúdo |
|---|---|
| `Instituto_Semear_planilhas_operacionais_2024-2026.xlsx` | Seis abas: CadastroFamilias, Participantes, Oficinas, Frequencia, Doacoes e Encaminhamentos. |
| `frequencia_export_sistema_antigo.csv` | Exportação do sistema anterior. Separador `;` e codificação **latin-1**. |
| `doacoes_2026.csv` | Recorte das doações de 2026, separador `,`, codificação UTF-8. |

## O que esperar

A base **não está limpa**, e isso é proposital. Ela reproduz o que existe de verdade em organizações que
controlam sua operação em planilhas. Você vai encontrar, entre outras coisas:

- datas em formatos diferentes na mesma coluna;
- marcações de presença sem padrão (`P`, `x`, `1`, `presente`, `falta`, vazio);
- nomes com grafias divergentes, abreviações, acentuação inconsistente e espaços sobrando;
- registros duplicados, alguns idênticos e outros quase idênticos;
- referências que não existem (participante ou oficina inexistente);
- campos vazios e preenchimentos como `NÃO INFORMADO`, `n/i`, `-`;
- valores monetários ora como número, ora como texto com `R$`;
- linhas de anotação no meio da planilha, escritas por quem operava o controle.

## Regras de trabalho

1. **Nunca edite os arquivos de `dados/brutos/`.** Eles são a fonte e precisam permanecer intactos para
   que qualquer resultado seja reproduzível.
2. Toda limpeza é feita por **script**, e a saída vai para `dados/tratados/`. Limpeza feita à mão na
   planilha não é aceita: não é reproduzível nem auditável.
3. Registre cada decisão de limpeza no `Relatório de Qualidade da Informação`: o que foi encontrado,
   quantas ocorrências, o que foi feito e por quê.
4. Quando uma decisão depender de conhecimento do negócio — por exemplo, se `presente` e `P` significam a
   mesma coisa —, **pergunte à organização**. Não decida sozinho.
