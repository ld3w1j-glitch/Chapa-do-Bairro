# Chapa do Bairro V2 - Corrigido

Sistema Flask modular para hamburgueria.

## Como rodar no Windows

Extraia o ZIP, entre na pasta do projeto e dê dois cliques em:

```txt
start_windows.bat
```

Ou rode manualmente:

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python scripts\init_db.py
python run.py
```

Acesse:

```txt
http://127.0.0.1:5000
```

Painel admin:

```txt
http://127.0.0.1:5000/admin
```

Login padrão:

```txt
Usuário: admin
Senha: 123456
```

## Correção aplicada

O banco SQLite agora usa caminho absoluto dentro da pasta:

```txt
instance/chapa_do_bairro.db
```

A pasta `instance` é criada automaticamente pelo `config.py`.

## Alterar WhatsApp

No arquivo `.env`, altere:

```txt
WHATSAPP_NUMBER=5535999999999
```

Use: 55 + DDD + número.


## Checkout antes do WhatsApp

Agora, ao clicar em "Fazer pedido", o cliente passa por uma tela de checkout onde informa:

- Nome
- Telefone
- Quantidade
- Retirada ou entrega
- Endereço, se for entrega
- Forma de pagamento
- Troco, se for dinheiro
- Observações

Depois disso, o sistema monta a mensagem completa e abre o WhatsApp.


## V4 visual

Esta versão inclui:

- Imagem da identidade visual como fundo fixo
- Cards transparentes com efeito vidro
- Header transparente com blur
- Painéis do admin transparentes
- Checkout antes do WhatsApp
- Campos de endereço, telefone, pagamento e troco


## V5 Mobile

Esta versão inclui:

- Imagem exclusiva para mobile: `background-mobile.png`
- Menu hambúrguer com três tracinhos em telas pequenas
- Menu abre e fecha ao clicar
- Fundo desktop preservado
- Fundo mobile otimizado para celular

## V7 - Estoque Inteligente

Novo módulo disponível em:

```txt
/admin/estoque
```

Inclui:

- Cadastro de fornecedores
- Cadastro de insumos e matéria-prima
- Unidade de medida: un, g, kg, ml, L, fatia e pacote
- Estoque atual
- Estoque mínimo
- Custo por unidade
- Percentual de desperdício/perda
- Ficha técnica por produto
- Cálculo de custo de produção
- Lucro estimado por produto
- Produção possível com estoque atual
- Sugestão de compras para evitar falta e desperdício


## V8 - Logo do footer acessa o admin

A logo do Washington no footer agora é clicável.

Ao clicar nela, o sistema abre:

```txt
/login
```

que é a tela de login do painel administrativo.


## V9 - Menu superior limpo

Os links `Admin` e `Estoque` foram removidos do menu superior.

O acesso ao painel administrativo continua disponível pela logo do Washington no footer.


## V10 - Footer profissional

Alterações feitas:

- Removido o bloco grande "Desenvolvido por Washington Oliveira" do centro.
- Footer agora fica simples e no final da página.
- A logo do Washington virou um botão flutuante discreto no canto inferior direito.
- Clicar na logo abre `/login`, mantendo o acesso admin oculto.


## V12 - Carrinho de múltiplos produtos

Agora o cliente consegue:

- Adicionar vários produtos ao carrinho
- Escolher quantidade por produto
- Atualizar carrinho
- Limpar carrinho
- Finalizar pedido com nome, telefone, endereço e pagamento
- Enviar todos os produtos juntos para o WhatsApp

## V13 - Previsão de Lucro

Nova aba no estoque inteligente:

```txt
/admin/estoque/previsao-lucro
```

Recursos:

- Simulação por quantidade vendida
- Faturamento previsto
- Custo previsto
- Lucro previsto
- Margem estimada
- Gráfico em CSS com as cores do site
- Tabela detalhada por produto


## V14 - Gráfico vertical de lucro

O gráfico da previsão de lucro agora usa:

- Barras verticais
- Crescimento de baixo para cima
- Gradiente laranja/abóbora com opacidade da base até o topo
- Visual adaptado para mobile


## V15 - Preparado para Railway

Arquivos adicionados:

```txt
Procfile
railway.json
runtime.txt
start_railway.sh
scripts/railway_init_db.py
```

Dependências adicionadas:

```txt
gunicorn
psycopg2-binary
```

### Como subir no Railway

1. Envie este projeto para um repositório no GitHub.
2. No Railway, crie um novo projeto usando **Deploy from GitHub repo**.
3. Adicione um banco **PostgreSQL** no Railway.
4. Confira se a variável `DATABASE_URL` ficou disponível no serviço Flask.
5. Configure estas variáveis no Railway:

```txt
SECRET_KEY=uma-chave-grande-e-segura
ADMIN_USERNAME=admin
ADMIN_PASSWORD=sua-senha-forte
WHATSAPP_NUMBER=55DDDNUMERO
STORE_NAME=Chapa do Bairro
STORE_SLOGAN=Sabor de bairro, qualidade de respeito.
```

O Railway iniciará com:

```txt
sh start_railway.sh
```

Esse script cria as tabelas, prepara o usuário admin e inicia o Gunicorn.

### Login admin

```txt
https://seu-projeto.up.railway.app/login
```


## Melhorias incluídas nesta versão

- Removida a dependência `psycopg2-binary` para facilitar a instalação local com SQLite no Windows.
- Checkout agora registra o pedido no banco antes de abrir o WhatsApp.
- Baixa automática do estoque com base na ficha técnica cadastrada do produto.
- Dashboard com pedidos em aberto e alertas de estoque baixo.
- Tela do pedido com botão para imprimir comanda e reenviar mensagem pelo WhatsApp.
- Campos de pagamento e troco salvos no pedido.
- CSS extra para melhorar visual mobile e impressão.

## Como rodar no Windows

```bat
python -m venv venv
venv\Scriptsctivate
python -m pip install --upgrade pip
pip install -r requirements.txt
python scripts\init_db.py
python run.py
```

Acesse: http://127.0.0.1:5000

Login padrão do admin, caso não altere o `.env`:

- Usuário: admin
- Senha: 123456

Para produção, altere `SECRET_KEY`, `ADMIN_USERNAME`, `ADMIN_PASSWORD` e `WHATSAPP_NUMBER` no arquivo `.env`.


## Telefone padronizado para WhatsApp

O checkout valida e salva o telefone do cliente no formato numérico: `55 + DDD + celular com 9 dígitos`. Exemplo: `5535999999999`. No painel do pedido, cada status possui um botão para enviar mensagem pronta ao cliente pelo WhatsApp.
