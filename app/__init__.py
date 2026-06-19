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
            "pix_city": "MONTES CLAROS"
        }
        settings_path = os.path.join(app.static_folder, "site_settings.json")
        try:
            with open(settings_path, "r", encoding="utf-8") as f:
                settings.update(json.load(f))
        except Exception:
            pass
        return {
            "store_name": settings.get("store_name", app.config["STORE_NAME"]),
            "store_slogan": settings.get("slogan", app.config["STORE_SLOGAN"]),
            "site_settings": settings,
            "whatsapp_number": app.config["WHATSAPP_NUMBER"],
        }

    return app
