from flask import Flask
import json
import os
from config import Config
from app.extensions import db

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)

    db.init_app(app)

    # Garante que novas tabelas do sistema (cupons, clientes/fidelidade)
    # sejam criadas automaticamente em instalações simples com SQLite.
    with app.app_context():
        try:
            from app import models  # noqa: F401
            db.create_all()
            # Atualização simples para bancos SQLite já existentes.
            # O create_all cria tabelas novas, mas não adiciona colunas em tabelas antigas.
            from sqlalchemy import text
            try:
                customer_cols = [row[1] for row in db.session.execute(text("PRAGMA table_info(customers)")).fetchall()]
                if "blocked" not in customer_cols:
                    db.session.execute(text("ALTER TABLE customers ADD COLUMN blocked BOOLEAN NOT NULL DEFAULT 0"))
                if "tags" not in customer_cols:
                    db.session.execute(text("ALTER TABLE customers ADD COLUMN tags VARCHAR(255) DEFAULT ''"))
                if "notes" not in customer_cols:
                    db.session.execute(text("ALTER TABLE customers ADD COLUMN notes TEXT"))
                db.session.commit()
            except Exception:
                db.session.rollback()

            # Garante que o login padrão sempre funcione em instalações locais.
            # Usuário padrão: admin / 123456, ou valores definidos no .env.
            try:
                from app.models.user import User
                default_user = User.query.filter_by(username=Config.ADMIN_USERNAME).first()
                if not default_user:
                    default_user = User(username=Config.ADMIN_USERNAME, role="admin", active=True)
                    default_user.set_password(Config.ADMIN_PASSWORD)
                    db.session.add(default_user)
                else:
                    default_user.active = True
                    default_user.role = default_user.role or "admin"
                    # Corrige banco antigo onde o hash foi gerado errado ou a senha padrão não entra.
                    if not default_user.check_password(Config.ADMIN_PASSWORD):
                        default_user.set_password(Config.ADMIN_PASSWORD)
                db.session.commit()
            except Exception:
                db.session.rollback()
        except Exception:
            pass

    from app.site.routes import site_bp
    from app.auth.routes import auth_bp
    from app.admin.routes import admin_bp
    from app.orders.routes import orders_bp
    from app.inventory.routes import inventory_bp

    app.register_blueprint(site_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(orders_bp, url_prefix="/pedidos")
    app.register_blueprint(inventory_bp, url_prefix="/admin/estoque")

    @app.context_processor
    def inject_store_data():
        settings = {
            "store_name": app.config["STORE_NAME"],
            "slogan": app.config["STORE_SLOGAN"],
            "primary_color": "#D96A1B",
            "delivery_time": "25 a 40 min",
            "open_message": "Estamos abertos para pedidos!",
            "pix_key": "",
            "pix_owner": "Chapa do Bairro",
            "pix_city": "MONTES CLAROS",
            "floating_ticket_enabled": "on",
            "floating_ticket_style": "horizontal",
            "floating_ticket_coupon": "CHAPA10",
            "floating_ticket_reward_product_id": "",
            "floating_ticket_text": "Ganhe desconto especial no seu primeiro pedido!"
        }
        settings_path = os.path.join(app.static_folder, "site_settings.json")
        try:
            with open(settings_path, "r", encoding="utf-8") as f:
                settings.update(json.load(f))
        except Exception:
            pass
        try:
            from app.models.product import Product
            reward_id = settings.get("floating_ticket_reward_product_id")
            if reward_id:
                produto = Product.query.get(int(reward_id))
                settings["floating_ticket_reward_product_name"] = produto.name if produto else ""
            else:
                settings["floating_ticket_reward_product_name"] = ""
        except Exception:
            settings["floating_ticket_reward_product_name"] = ""

        return {
            "store_name": settings.get("store_name", app.config["STORE_NAME"]),
            "store_slogan": settings.get("slogan", app.config["STORE_SLOGAN"]),
            "site_settings": settings,
            "whatsapp_number": app.config["WHATSAPP_NUMBER"],
        }

    return app
