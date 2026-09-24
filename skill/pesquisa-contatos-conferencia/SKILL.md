---
name: pesquisa-contatos-conferencia
description: Pesquisa pessoas que o usuário vai encontrar (ou encontrou) em conferências e eventos do mercado financeiro e monta um briefing curto sobre a pessoa e o fundo/empresa dela, com estratégia (long-only, long-short etc.), AUM mais recente e outras informações financeiras. Também gera o briefing em PDF e mantém a base histórica em Excel de pessoas com quem o usuário conversou (data da conversa + conferência). Use esta skill sempre que o usuário mandar um nome de pessoa acompanhado de fundo, gestora ou empresa pedindo para pesquisar, "quem é", "me prepara para a reunião com", ou mandar uma agenda de conferência, lista de participantes, foto de crachá ou cartão de visita, ou pedir para adicionar alguém na base de contatos, mesmo que não mencione a palavra "skill" ou "briefing".
---

# Pesquisa de contatos para conferências

O usuário trabalha no mercado financeiro e usa esta skill para se preparar para conversas em
conferências. O objetivo é um briefing **curto, confiável e fácil de ler no celular**: quem é a
pessoa, o que o fundo/empresa faz, como investe e qual o tamanho (AUM). Números inventados são
piores do que "não encontrado". O usuário vai usar isso numa conversa real, e um AUM errado
constrange. Por isso cada número vem com data de referência e fonte, e o que não for achado é dito
explicitamente.

Responda no idioma do usuário (normalmente português).

## 1. Entender o pedido

As entradas possíveis são:
- **Nome + fundo/empresa** digitados. Pode ser uma pessoa ou várias, uma por linha.
- **Arquivo da agenda** (PDF, Excel, CSV, Word) ou **foto** de crachá, cartão de visita ou lista
  de participantes. Extraia nome, fundo/empresa, cargo e painel/horário, quando houver. Se houver
  mais de ~8 pessoas, mostre a lista numerada e pergunte quem pesquisar ("todas", "1, 4, 7" ou
  "só os PMs"). Cada pesquisa consome o limite de uso do plano do usuário; pesquisar 40 pessoas
  de uma vez pode esgotá-lo.
- **Pedido para adicionar à base** ("pesquisa e adiciona na base", "conversei com ele hoje na
  conferência X"). Veja a seção 4.

Se só vier o nome, sem empresa, pesquise assim mesmo. Se houver homônimos relevantes, pergunte
qual é a pessoa ou use o contexto (conferência, cargo) para desambiguar.

## 2. Pesquisar

Use a busca na web. Uma boa ordem:

1. **LinkedIn** (`"Nome" "Empresa" site:linkedin.com/in`): cargo atual, trajetória e formação.
   O LinkedIn costuma bloquear a leitura direta da página; o trecho que aparece no resultado de
   busca normalmente basta. Não insista em abrir o perfil. Se aparecerem vários perfis, use o que
   bate com a empresa e o cargo (prefira a URL "personalizada", ex. `/in/nome-sobrenome`).
2. **Site oficial** do fundo/empresa: o que faz, estratégias, produtos, equipe, AUM divulgado.
3. **AUM e dados financeiros**, conforme o tipo de instituição:
   - Gestoras nos EUA: SEC Form ADV (adviserinfo.sec.gov), com "Regulatory AUM" e data do filing.
   - Gestoras no Brasil: CVM, ANBIMA (ranking de gestores), lâminas de fundos, Mais Retorno etc.
   - Hedge funds e PE/VC: notícias (Bloomberg, Reuters, FT, Valor, Institutional Investor,
     PitchBook, Preqin, Crunchbase).
   - Empresas operacionais: receita, valor de mercado, número de funcionários, rodadas de captação.
   - Fundos de pensão, endowments e family offices: ativos sob gestão, política de alocação.
4. **Notícias recentes** (últimos 12-18 meses): mudanças de cargo, captações, lançamentos,
   performance.

Confirme que a pessoa encontrada é de fato a do fundo/empresa informado. Se ela mudou de empresa
recentemente, diga isso num alerta.

**Estratégia:** inclua quando a pessoa for PM, CIO, analista, trader, alocador, ou quando a
estratégia fizer sentido para a empresa (qualquer gestora ou fundo). Classifique de forma clara:
Long-only, Long-short, Long-biased, Market neutral, Multi-strategy, Global macro, Crédito,
Quant/sistemático, Event-driven, Private equity, Venture capital, Real estate, Multi-asset/FoF
etc. Complete com classes de ativos, regiões e setores de foco. Para um CFO de empresa operacional,
por exemplo, a estratégia de investimento não se aplica: omita a seção.

**AUM:** traga o dado mais recente, com mês/ano de referência e fonte. Se só achar um número
antigo (mais de ~2 anos), mostre e sinalize que pode estar desatualizado. Quando existir, traga
também o AUM da estratégia ou fundo específico da pessoa.

**Fontes conflitantes:** é comum sites antigos repetirem um AUM desatualizado. Use o número mais
recente de fonte confiável e, se a diferença for grande, registre num alerta (ex.: "vários sites
ainda citam R$ 49 bi, número de 2021").

**Páginas bloqueadas:** se não conseguir abrir um site, use os trechos dos resultados de busca e
tente outras fontes. Só coloque em "Não encontrado" o que realmente não achou em lugar nenhum.

Para cada pessoa, 5 a 10 buscas costumam bastar. Priorize qualidade e pare quando tiver o essencial.

## 3. Apresentar o briefing

Use este formato, pensado para leitura rápida no celular:

```
## [Nome] — [Cargo], [Fundo/Empresa]

**Pessoa:** [2-3 linhas: cargo e responsabilidade, trajetória relevante, formação]
[LinkedIn](url)

**Fundo/empresa:** [2-3 linhas: o que faz, tipo, sede, fundação, principais produtos]

**Estratégia:** [Tipo] — [classes de ativos, regiões, setores, estilo]     ← só se fizer sentido

**AUM:** [valor] ([mês/ano] — fonte: [fonte])

**Outras informações financeiras:**
- [item]: [valor] ([data/fonte])

**Não encontrado:** [lista curta do que foi procurado e não achado]
⚠️ [alertas: homônimo, mudou de empresa, dado possivelmente desatualizado]

Fontes: [2-5 links principais]
```

Mantenha cada resumo em 2-3 linhas. Tudo que foi procurado e não encontrado vai para "Não
encontrado", para o usuário saber que você procurou.

Ao final da resposta (uma vez só, mesmo com várias pessoas), ofereça numa linha curta as próximas
ações que ainda não foram feitas: **📄 Salvar em PDF · ➕ Adicionar à base · 🔎 Nova pesquisa**. Se o
PDF ou a base já foram entregues nesta resposta, diga isso em vez de oferecer de novo.

Os caminhos `scripts/...` abaixo são relativos à pasta desta skill (onde está este SKILL.md).

## 4. Adicionar à base de contatos (Excel)

A base é uma planilha `base_contatos.xlsx` com as pessoas com quem o usuário já conversou. Os
arquivos não ficam salvos entre conversas no claude.ai. Por isso o usuário anexa a versão mais
recente da base quando quer adicionar pessoas, e você devolve a versão atualizada para ele baixar
e guardar.

1. Para cada pessoa, você precisa de **data da conversa** e **conferência**. Pergunte o que faltar
   numa única mensagem curta. Se o usuário disser "hoje", use a data de hoje. Observações
   (assuntos, próximos passos) são opcionais; aceite se o usuário mandar.
2. Se o usuário não anexou a base, pergunte se ele tem uma para anexar. Se não tiver (ou disser
   para criar), crie uma nova. Nunca invente o conteúdo de uma base que você não viu.
3. Salve os briefings em JSON (formato abaixo) e rode:
   ```bash
   python scripts/base_excel.py --briefings briefings.json \
       --data-conversa 2026-09-24 --conferencia "Nome da conferência" \
       [--observacoes "texto"] [--base /caminho/base_contatos.xlsx] \
       --saida /mnt/user-data/outputs/base_contatos.xlsx
   ```
   `--base` é a planilha anexada. Sem esse argumento, o script cria uma base nova. Para pessoas
   com observações diferentes, rode uma vez por pessoa, usando a saída de uma execução como
   `--base` da seguinte. O script avisa se a mesma pessoa já estiver na base com a mesma data e
   conferência e não a duplica.
4. Entregue o arquivo atualizado e diga quantos contatos a base tem agora. Lembre o usuário, em
   meia linha, de guardar esta versão no lugar da anterior (por exemplo, no OneDrive ou Google
   Drive, se a equipe compartilha a base por lá).

"Pesquisar e adicionar" na mesma mensagem: faça a pesquisa, mostre o briefing e já adicione à
base, se tiver os dados; senão, pergunte só o que falta.

## 5. Salvar em PDF

Salve os briefings em JSON e rode:
```bash
python scripts/briefing_pdf.py --briefings briefings.json --saida /mnt/user-data/outputs/briefing_Nome.pdf
```
Com várias pessoas, gere um PDF único com uma página por pessoa (nome do arquivo sugerido:
`briefings_<conferencia>_<data>.pdf`), a menos que o usuário peça arquivos separados.

Se o diretório `/mnt/user-data/outputs/` não existir no ambiente, salve em outro lugar de onde o
arquivo possa ser entregue ao usuário.

## Formato do JSON dos briefings

Os dois scripts usam o mesmo arquivo: uma lista com um objeto por pessoa. Use a string
`"Não encontrado"` nos campos sem informação.

```json
[
  {
    "pessoa": {"nome": "", "cargo": "", "linkedin_url": "", "resumo": ""},
    "empresa": {"nome": "", "tipo": "", "sede": "", "site": "", "resumo": ""},
    "estrategia": {"aplicavel": true, "tipo": "Long-short", "descricao": ""},
    "aum": {"valor": "US$ 12,5 bi", "data_referencia": "mar/2026", "fonte": "Form ADV", "observacao": ""},
    "outras_informacoes_financeiras": [{"item": "", "valor": "", "fonte": ""}],
    "nao_encontrado": [""],
    "alertas": [""],
    "fontes": [{"titulo": "", "url": ""}]
  }
]
```
