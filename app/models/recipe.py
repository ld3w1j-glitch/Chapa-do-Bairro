from app.extensions import db

class RecipeItem(db.Model):
    __tablename__ = "recipe_items"

    id = db.Column(db.Integer, primary_key=True)

    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    ingredient_id = db.Column(db.Integer, db.ForeignKey("ingredients.id"), nullable=False)

    quantity = db.Column(db.Float, nullable=False, default=0)

    product = db.relationship("Product", back_populates="recipe_items")
    ingredient = db.relationship("Ingredient", back_populates="recipes")

    def item_cost(self):
        waste_multiplier = 1 + ((self.ingredient.waste_percent or 0) / 100)
        return self.quantity * self.ingredient.cost_per_unit * waste_multiplier

    def quantity_label(self):
        return f"{self.quantity:g} {self.ingredient.unit}"
