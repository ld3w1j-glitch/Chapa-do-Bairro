from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.category import Category
from app.models.product import Product
from app.models.supplier import Supplier
from app.models.ingredient import Ingredient
from app.models.recipe import RecipeItem
from app.models.coupon import Coupon
from app.models.delivery_zone import DeliveryZone
from config import Config

app = create_app()

with app.app_context():
    db.create_all()

    if not User.query.filter_by(username=Config.ADMIN_USERNAME).first():
        user = User(username=Config.ADMIN_USERNAME, role="admin", active=True)
        user.set_password(Config.ADMIN_PASSWORD)
        db.session.add(user)

    categorias_base = ["Hambúrguer", "Acompanhamento", "Bebida", "Combo"]
    for nome in categorias_base:
        if not Category.query.filter_by(name=nome).first():
            db.session.add(Category(name=nome, active=True))

    db.session.commit()

    hamburguer = Category.query.filter_by(name="Hambúrguer").first()
    acompanhamento = Category.query.filter_by(name="Acompanhamento").first()

    if Product.query.count() == 0:
        produtos = [
            Product(
                name="Smash Bairro",
                description="Pão brioche, burger smash, cheddar e molho da casa.",
                price=24.90,
                category_id=hamburguer.id,
                active=True,
                featured=True
            ),
            Product(
                name="Duplo Chapa",
                description="Dois burgers smash, cheddar duplo, bacon crocante e barbecue.",
                price=34.90,
                category_id=hamburguer.id,
                active=True,
                featured=True
            ),
            Product(
                name="Batata Cheddar Bacon",
                description="Batata crocante com cheddar cremoso e bacon.",
                price=19.90,
                category_id=acompanhamento.id,
                active=True,
                featured=True
            ),
        ]
        db.session.add_all(produtos)


    if not Supplier.query.filter_by(name="Fornecedor Padrão").first():
        db.session.add(Supplier(name="Fornecedor Padrão", phone="", notes="Fornecedor inicial do sistema.", active=True))
        db.session.commit()

    fornecedor = Supplier.query.filter_by(name="Fornecedor Padrão").first()

    insumos_base = [
        ("Pão brioche", "un", 40, 10, 1.20, 2),
        ("Carne smash", "g", 8000, 3000, 0.045, 5),
        ("Cheddar", "fatia", 100, 30, 0.80, 1),
        ("Bacon", "g", 2000, 700, 0.055, 8),
        ("Molho da casa", "g", 1500, 500, 0.030, 4),
        ("Embalagem", "un", 80, 30, 0.75, 0),
    ]

    for nome, unit, atual, minimo, custo, perda in insumos_base:
        if not Ingredient.query.filter_by(name=nome).first():
            db.session.add(Ingredient(
                name=nome,
                unit=unit,
                current_stock=atual,
                minimum_stock=minimo,
                cost_per_unit=custo,
                waste_percent=perda,
                supplier_id=fornecedor.id,
                active=True
            ))

    db.session.commit()


    # Ficha técnica inicial
    smash = Product.query.filter_by(name="Smash Bairro").first()
    duplo = Product.query.filter_by(name="Duplo Chapa").first()

    pao = Ingredient.query.filter_by(name="Pão brioche").first()
    carne = Ingredient.query.filter_by(name="Carne smash").first()
    cheddar = Ingredient.query.filter_by(name="Cheddar").first()
    bacon = Ingredient.query.filter_by(name="Bacon").first()
    molho = Ingredient.query.filter_by(name="Molho da casa").first()
    embalagem = Ingredient.query.filter_by(name="Embalagem").first()

    def add_recipe(product, ingredient, qty):
        if product and ingredient and not RecipeItem.query.filter_by(product_id=product.id, ingredient_id=ingredient.id).first():
            db.session.add(RecipeItem(product_id=product.id, ingredient_id=ingredient.id, quantity=qty))

    add_recipe(smash, pao, 1)
    add_recipe(smash, carne, 120)
    add_recipe(smash, cheddar, 2)
    add_recipe(smash, molho, 20)
    add_recipe(smash, embalagem, 1)

    add_recipe(duplo, pao, 1)
    add_recipe(duplo, carne, 240)
    add_recipe(duplo, cheddar, 4)
    add_recipe(duplo, bacon, 30)
    add_recipe(duplo, molho, 25)
    add_recipe(duplo, embalagem, 1)




    # Bairros e taxas de entrega iniciais
    zonas_base = [
        ("Centro", 5.00, "25 a 35 min"),
        ("Todos os Santos", 6.00, "30 a 40 min"),
        ("Major Prates", 8.00, "35 a 50 min"),
        ("Maristela", 10.00, "40 a 55 min"),
    ]
    for nome, taxa, tempo in zonas_base:
        if not DeliveryZone.query.filter_by(name=nome).first():
            db.session.add(DeliveryZone(name=nome, fee=taxa, estimated_time=tempo, active=True))
    db.session.commit()

    # Cupom inicial para campanhas de retorno
    if not Coupon.query.filter_by(code="VOLTE10").first():
        db.session.add(Coupon(
            code="VOLTE10",
            description="10% OFF para campanha de retorno",
            discount_type="percent",
            value=10,
            minimum_total=0,
            active=True
        ))
        db.session.commit()

    db.session.commit()
    print("Banco inicializado com sucesso.")
