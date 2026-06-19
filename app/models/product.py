from app.extensions import db

class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    image = db.Column(db.String(255), nullable=True)
    active = db.Column(db.Boolean, default=True)
    featured = db.Column(db.Boolean, default=False)

    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)
    category = db.relationship("Category", back_populates="products")
    recipe_items = db.relationship("RecipeItem", back_populates="product", cascade="all, delete-orphan")

    def price_br(self):
        return f"R$ {self.price:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


    def production_cost(self):
        return sum(item.item_cost() for item in self.recipe_items)

    def production_cost_br(self):
        return f"R$ {self.production_cost():,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def estimated_profit(self):
        return self.price - self.production_cost()

    def estimated_profit_br(self):
        return f"R$ {self.estimated_profit():,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def max_possible_production(self):
        if not self.recipe_items:
            return 0

        possible = []
        for item in self.recipe_items:
            if item.quantity <= 0:
                continue
            possible.append(int(item.ingredient.current_stock // item.quantity))

        return min(possible) if possible else 0
