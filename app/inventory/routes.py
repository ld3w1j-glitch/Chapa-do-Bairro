import csv
import io
from flask import Blueprint, render_template, request, redirect, url_for, flash, Response
from app.core.security import login_required
from app.extensions import db
from app.models.supplier import Supplier
from app.models.ingredient import Ingredient
from app.models.product import Product
from app.models.recipe import RecipeItem

inventory_bp = Blueprint("inventory", __name__)

@inventory_bp.route("/")
@login_required
def dashboard():
    ingredients = Ingredient.query.filter_by(active=True).order_by(Ingredient.name).all()
    low_stock = [item for item in ingredients if item.is_low_stock()]
    products = Product.query.order_by(Product.name).all()

    total_stock_value = sum(i.current_stock * i.cost_per_unit for i in ingredients)

    return render_template(
        "inventory/dashboard.html",
        ingredients=ingredients,
        low_stock=low_stock,
        products=products,
        total_stock_value=total_stock_value,
    )

@inventory_bp.route("/fornecedores")
@login_required
def suppliers():
    fornecedores = Supplier.query.order_by(Supplier.name).all()
    return render_template("inventory/suppliers.html", fornecedores=fornecedores)

@inventory_bp.route("/fornecedores/novo", methods=["GET", "POST"])
@login_required
def create_supplier():
    if request.method == "POST":
        supplier = Supplier(
            name=request.form["name"],
            phone=request.form.get("phone"),
            notes=request.form.get("notes"),
            active=request.form.get("active") == "on",
        )
        db.session.add(supplier)
        db.session.commit()
        flash("Fornecedor cadastrado com sucesso.", "success")
        return redirect(url_for("inventory.suppliers"))

    return render_template("inventory/supplier_form.html", fornecedor=None)

@inventory_bp.route("/fornecedores/<int:supplier_id>/editar", methods=["GET", "POST"])
@login_required
def edit_supplier(supplier_id):
    supplier = Supplier.query.get_or_404(supplier_id)

    if request.method == "POST":
        supplier.name = request.form["name"]
        supplier.phone = request.form.get("phone")
        supplier.notes = request.form.get("notes")
        supplier.active = request.form.get("active") == "on"
        db.session.commit()
        flash("Fornecedor atualizado.", "success")
        return redirect(url_for("inventory.suppliers"))

    return render_template("inventory/supplier_form.html", fornecedor=supplier)

@inventory_bp.route("/insumos")
@login_required
def ingredients():
    insumos = Ingredient.query.order_by(Ingredient.name).all()
    return render_template("inventory/ingredients.html", insumos=insumos)

@inventory_bp.route("/insumos/novo", methods=["GET", "POST"])
@login_required
def create_ingredient():
    fornecedores = Supplier.query.filter_by(active=True).order_by(Supplier.name).all()

    if request.method == "POST":
        ingredient = Ingredient(
            name=request.form["name"],
            unit=request.form["unit"],
            current_stock=float(request.form.get("current_stock", "0").replace(",", ".")),
            minimum_stock=float(request.form.get("minimum_stock", "0").replace(",", ".")),
            cost_per_unit=float(request.form.get("cost_per_unit", "0").replace(",", ".")),
            waste_percent=float(request.form.get("waste_percent", "0").replace(",", ".")),
            supplier_id=int(request.form["supplier_id"]) if request.form.get("supplier_id") else None,
            active=request.form.get("active") == "on",
        )
        db.session.add(ingredient)
        db.session.commit()
        flash("Insumo cadastrado com sucesso.", "success")
        return redirect(url_for("inventory.ingredients"))

    return render_template("inventory/ingredient_form.html", insumo=None, fornecedores=fornecedores)

@inventory_bp.route("/insumos/<int:ingredient_id>/editar", methods=["GET", "POST"])
@login_required
def edit_ingredient(ingredient_id):
    ingredient = Ingredient.query.get_or_404(ingredient_id)
    fornecedores = Supplier.query.filter_by(active=True).order_by(Supplier.name).all()

    if request.method == "POST":
        ingredient.name = request.form["name"]
        ingredient.unit = request.form["unit"]
        ingredient.current_stock = float(request.form.get("current_stock", "0").replace(",", "."))
        ingredient.minimum_stock = float(request.form.get("minimum_stock", "0").replace(",", "."))
        ingredient.cost_per_unit = float(request.form.get("cost_per_unit", "0").replace(",", "."))
        ingredient.waste_percent = float(request.form.get("waste_percent", "0").replace(",", "."))
        ingredient.supplier_id = int(request.form["supplier_id"]) if request.form.get("supplier_id") else None
        ingredient.active = request.form.get("active") == "on"
        db.session.commit()
        flash("Insumo atualizado.", "success")
        return redirect(url_for("inventory.ingredients"))

    return render_template("inventory/ingredient_form.html", insumo=ingredient, fornecedores=fornecedores)

@inventory_bp.route("/ficha-tecnica/<int:product_id>", methods=["GET", "POST"])
@login_required
def recipe(product_id):
    product = Product.query.get_or_404(product_id)
    ingredients = Ingredient.query.filter_by(active=True).order_by(Ingredient.name).all()

    if request.method == "POST":
        ingredient_id = int(request.form["ingredient_id"])
        quantity = float(request.form["quantity"].replace(",", "."))

        if quantity <= 0:
            flash("Informe uma quantidade válida.", "error")
            return redirect(url_for("inventory.recipe", product_id=product.id))

        item = RecipeItem(
            product_id=product.id,
            ingredient_id=ingredient_id,
            quantity=quantity
        )
        db.session.add(item)
        db.session.commit()
        flash("Ingrediente adicionado à ficha técnica.", "success")
        return redirect(url_for("inventory.recipe", product_id=product.id))

    return render_template("inventory/recipe.html", produto=product, ingredients=ingredients)

@inventory_bp.route("/ficha-tecnica/item/<int:item_id>/excluir", methods=["POST"])
@login_required
def delete_recipe_item(item_id):
    item = RecipeItem.query.get_or_404(item_id)
    product_id = item.product_id
    db.session.delete(item)
    db.session.commit()
    flash("Item removido da ficha técnica.", "success")
    return redirect(url_for("inventory.recipe", product_id=product_id))

@inventory_bp.route("/compras-sugeridas")
@login_required
def purchase_suggestions():
    ingredients = Ingredient.query.filter_by(active=True).order_by(Ingredient.name).all()
    suggestions = [i for i in ingredients if i.suggested_purchase() > 0]
    return render_template("inventory/purchase_suggestions.html", suggestions=suggestions)



@inventory_bp.route("/compras-sugeridas/exportar")
@login_required
def export_purchase_suggestions():
    ingredients = Ingredient.query.filter_by(active=True).order_by(Ingredient.name).all()
    suggestions = [i for i in ingredients if i.suggested_purchase() > 0]
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    writer.writerow(["Insumo", "Estoque atual", "Estoque minimo", "Comprar", "Unidade", "Fornecedor", "Custo estimado"])
    for item in suggestions:
        writer.writerow([
            item.name,
            f"{item.current_stock:g}",
            f"{item.minimum_stock:g}",
            f"{item.suggested_purchase():.2f}",
            item.unit,
            item.supplier.name if item.supplier else "",
            f"{item.suggested_purchase() * item.cost_per_unit:.2f}",
        ])
    return Response(output.getvalue(), mimetype="text/csv; charset=utf-8", headers={"Content-Disposition": "attachment; filename=lista_compras_chapa_do_bairro.csv"})

@inventory_bp.route("/previsao-lucro", methods=["GET", "POST"])
@login_required
def profit_forecast():
    products = Product.query.order_by(Product.name).all()

    if request.method == "POST":
        quantities = {}
        for product in products:
            raw_value = request.form.get(f"quantity_{product.id}", "0")
            try:
                quantities[str(product.id)] = max(int(raw_value or 0), 0)
            except ValueError:
                quantities[str(product.id)] = 0
    else:
        quantities = {str(product.id): 10 for product in products}

    rows = []
    total_revenue = 0
    total_cost = 0
    total_profit = 0
    max_profit = 0

    for product in products:
        quantity = quantities.get(str(product.id), 0)
        unit_cost = product.production_cost()
        unit_profit = product.price - unit_cost
        revenue = product.price * quantity
        cost = unit_cost * quantity
        profit = unit_profit * quantity
        margin = (profit / revenue * 100) if revenue > 0 else 0

        total_revenue += revenue
        total_cost += cost
        total_profit += profit
        max_profit = max(max_profit, profit)

        rows.append({
            "product": product,
            "quantity": quantity,
            "unit_cost": unit_cost,
            "unit_profit": unit_profit,
            "revenue": revenue,
            "cost": cost,
            "profit": profit,
            "margin": margin,
        })

    for row in rows:
        row["bar_width"] = int((row["profit"] / max_profit) * 100) if max_profit > 0 else 0

    total_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0

    return render_template(
        "inventory/profit_forecast.html",
        products=products,
        rows=rows,
        total_revenue=total_revenue,
        total_cost=total_cost,
        total_profit=total_profit,
        total_margin=total_margin,
    )
