# Melhorias V8 — Login, PIX e Comanda

## Implementado

- Checkout com PIX QR Code dinâmico.
- Campo PIX Copia e Cola gerado automaticamente pelo valor total do pedido.
- Botão para copiar chave PIX e copiar o código PIX completo.
- Configuração da cidade do PIX no painel administrativo.
- Rota interna para gerar QR Code: `/pix/qrcode`.
- Rota interna para gerar código copia e cola: `/pix/copia-cola`.
- Comanda de cozinha em página própria para impressão térmica.
- Botão “Imprimir comanda” dentro do detalhe do pedido.
- CSS de impressão para esconder menu, rodapé, botão de WhatsApp e deixar a comanda limpa.

## Observação importante

O PIX desta versão gera QR Code e código Copia e Cola, mas não confirma pagamento automaticamente. Para confirmar pagamento sozinho, será necessário integrar Mercado Pago, PagSeguro, Efi/Gerencianet ou banco com webhook.

## Instalação

Depois de extrair o ZIP, rode:

```bash
pip install -r requirements.txt
python scripts/init_db.py
python run.py
```

Se o projeto já estiver instalado, atualize as dependências:

```bash
pip install -r requirements.txt
```

Depois acesse Admin > Configurações e cadastre a chave PIX.
