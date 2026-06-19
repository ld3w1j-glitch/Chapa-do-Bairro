# Melhorias V7 - Operação Segura

Nesta versão foram adicionadas melhorias operacionais reais:

## Login administrativo
- Painel administrativo já protegido por login.
- Senha salva com hash seguro pelo Werkzeug.
- Logout disponível no dashboard.

## Estoque automático mais seguro
- Antes de adicionar ao carrinho, o sistema verifica se existe estoque suficiente na ficha técnica.
- Antes de finalizar o pedido, o sistema valida estoque e baixa os insumos automaticamente.
- Se o pedido for cancelado no painel, o estoque é devolvido antes da exclusão.
- Produtos sem ficha técnica continuam vendendo normalmente, para não travar itens ainda não configurados.

## Frete por bairro
- Novo painel: Admin > Fretes por Bairro.
- Cadastro de bairro, taxa, prazo estimado e status ativo/inativo.
- Checkout calcula a taxa automaticamente com base nos bairros ativos.
- Mantém taxa padrão caso o banco ainda não tenha bairros cadastrados.

## Arquivos principais alterados
- app/models/delivery_zone.py
- app/models/__init__.py
- app/services/order_service.py
- app/site/routes.py
- app/admin/routes.py
- app/templates/admin/delivery_zones.html
- app/templates/admin/dashboard.html
- scripts/init_db.py
