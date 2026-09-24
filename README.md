# Pesquisa de Contatos para Conferências

## Forma recomendada: Skill do Claude (sem custo extra)

A pasta `skill/` tem a Skill **pesquisa-contatos-conferencia**. Ela roda dentro do claude.ai (no
navegador ou no app do celular) e usa o seu plano do Claude, sem cobrança por pesquisa. O que ela
faz:
- pesquisa pessoas e fundos/empresas: nome digitado, agenda em PDF/Excel ou foto de crachá/cartão;
- monta o briefing: resumo, estratégia, AUM com data e fonte, outros dados financeiros e o que não
  foi encontrado;
- gera o PDF do briefing;
- atualiza a base `base_contatos.xlsx` com a data da conversa e a conferência.

**Instalação (cada pessoa, uma vez):**
1. Baixe `skill/pesquisa-contatos-conferencia.zip`.
2. No claude.ai, abra **Configurações → Capacidades**. Ative **Criação e edição de arquivos /
   execução de código** e **Busca na web**.
3. Na mesma tela, em **Skills**, clique em **Enviar skill** e selecione o `.zip`.

**Uso:** abra uma conversa nova e escreva, por exemplo:
- `Pesquisa Maria Silva - XYZ Capital`
- `Pesquisa e adiciona na base: João Souza - ABC Asset, conversei hoje na Conferência X` (anexe a
  `base_contatos.xlsx` mais recente, se já tiver uma)
- anexe a agenda ou a foto de um crachá e peça `pesquisa essas pessoas`

A pasta `exemplo/` tem um PDF gerado por uma pesquisa real.

As pesquisas consomem o limite de uso do plano, como qualquer conversa com o Claude. Numa agenda
grande, pesquise em lotes.

---

## Alternativa: app web local (usa a API da Anthropic, cobrada à parte)

Aplicação web que roda no seu computador e prepara briefings sobre as pessoas que você vai
encontrar em conferências, e sobre os fundos/empresas delas. Também mantém uma base em Excel
com as pessoas com quem você já conversou.

## O que ela faz

- **Pesquisa individual:** digite o nome da pessoa e o fundo/empresa.
- **Agenda da conferência:** envie o arquivo da agenda (PDF, Excel, CSV, Word ou texto). O app
  lista as pessoas e os fundos/empresas encontrados; você escolhe quem pesquisar.
- Para cada pessoa, o Claude pesquisa na internet, começando pelo perfil público do LinkedIn e
  seguindo pelo site da empresa, reguladores (SEC/Form ADV, CVM), notícias etc. O briefing traz:
  - resumo de 2-3 linhas sobre a pessoa e outro sobre o fundo/empresa;
  - a **estratégia** (Long-only, Long-short, Macro, Crédito…), quando a pessoa é PM ou investidora
    ou quando a estratégia faz sentido para a empresa;
  - o **AUM mais recente**, com a data de referência e a fonte;
  - outras informações financeiras relevantes (performance, funcionários, receita, captações…);
  - uma lista do que **não foi encontrado**, alertas (por exemplo, homônimos) e as fontes.
- Botões **Salvar em PDF** e **Nova pesquisa** em cada briefing. Na agenda, há também
  **Salvar todos em PDF**, que junta todos os briefings num único arquivo.
- **Pesquisar e adicionar pessoa na base:** faz a pesquisa normal e pede a data da conversa, a
  conferência e observações opcionais. A linha é gravada em `dados/base_contatos.xlsx`.
  Você também pode adicionar alguém mais tarde pelo botão **Adicionar à base** no briefing.
- Aba **Base de contatos:** mostra o histórico, tem filtro de busca e o botão **Baixar Excel**.

## Instalação (uma vez)

1. Instale o **Python 3.10 ou superior**: https://www.python.org/downloads/
   (no Windows, marque "Add Python to PATH" durante a instalação).
2. Crie uma chave da API da Anthropic em https://platform.claude.com/ (menu *API Keys*).
3. Nesta pasta, copie `.env.example` para `.env` e cole a chave:
   ```
   ANTHROPIC_API_KEY=sk-ant-...
   ```

## Como usar

- **Windows:** clique duas vezes em `iniciar.bat`.
- **Mac/Linux:** rode `./iniciar.sh` no terminal.

Na primeira vez, o script instala as dependências. Depois ele abre o navegador em
http://127.0.0.1:5000. Para encerrar, feche a janela do terminal.

Cada pesquisa leva de 1 a 3 minutos. Na agenda, o app pesquisa duas pessoas por vez.

## Observações

- **LinkedIn:** o LinkedIn não permite acesso automatizado a perfis quando você está logado. Por
  isso, a pesquisa usa o que está público na web: o perfil público indexado pelos buscadores,
  o site da empresa, notícias, filings etc. Quando algo não é encontrado, o briefing diz isso
  em vez de inventar.
- **Confira os números importantes:** AUM e dados financeiros vêm de fontes públicas e podem
  estar desatualizados. Por isso, o briefing mostra a data de referência e a fonte de cada número.
- **Custo:** cada pesquisa é cobrada na sua conta da API da Anthropic. Para usar outro modelo,
  defina `CLAUDE_MODEL` no `.env`.
- **Base em Excel:** o arquivo fica em `dados/base_contatos.xlsx`. Ele não vai para o Git porque
  contém dados pessoais. Para guardá-lo em outra pasta (por exemplo, no OneDrive), defina `DATA_DIR`
  no `.env`. Feche o arquivo no Excel antes de adicionar pessoas; se ele estiver aberto, o app
  avisa que não conseguiu salvar.

## Estrutura

| Arquivo | Função |
|---|---|
| `app.py` | Servidor web (Flask) e rotas da API |
| `research.py` | Pesquisa com Claude + busca na web, e estruturação do briefing |
| `agenda.py` | Leitura da agenda e extração das pessoas |
| `database.py` | Base de contatos em Excel |
| `pdf_export.py` | Geração do PDF |
| `templates/`, `static/` | Interface web |
