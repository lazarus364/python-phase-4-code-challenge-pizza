#!/usr/bin/env python3
from flask import Flask, request, make_response, jsonify
from flask_migrate import Migrate
from flask_restful import Api, Resource
from models import db, Restaurant, Pizza, RestaurantPizza
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get("DB_URI", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.json.compact = False

migrate = Migrate(app, db)

db.init_app(app)

api = Api(app)

@app.route("/")
def index():
    return "<h1>Code challenge</h1>"

class Restaurants(Resource):
    def get(self):
        restaurants = Restaurant.query.all()
        # Use the default serialization rules (exclude restaurant_pizzas)
        return make_response([restaurant.to_dict() for restaurant in restaurants], 200)

class RestaurantById(Resource):
    def get(self, id):
        restaurant = Restaurant.query.get(id)
        if restaurant:
            # Manually include restaurant_pizzas and associated pizza data
            restaurant_data = restaurant.to_dict()
            restaurant_data['restaurant_pizzas'] = [
                {
                    "id": rp.id,
                    "pizza": rp.pizza.to_dict(),
                    "pizza_id": rp.pizza_id,
                    "price": rp.price,
                    "restaurant_id": rp.restaurant_id
                }
                for rp in restaurant.restaurant_pizzas
            ]
            return make_response(restaurant_data, 200)
        else:
            return make_response({"error": "Restaurant not found"}, 404)

    def delete(self, id):
        restaurant = Restaurant.query.get(id)
        if restaurant:
            db.session.delete(restaurant)
            db.session.commit()
            return make_response('', 204)
        else:
            return make_response({"error": "Restaurant not found"}, 404)

class Pizzas(Resource):
    def get(self):
        pizzas = Pizza.query.all()
        return make_response([pizza.to_dict() for pizza in pizzas], 200)

class RestaurantPizzas(Resource):
    def post(self):
        data = request.get_json()

        # Validate required fields
        if not all(key in data for key in ['price', 'pizza_id', 'restaurant_id']):
            return make_response({"errors": ["validation errors"]}, 400)

        # Check if the referenced Restaurant and Pizza exist
        restaurant = Restaurant.query.get(data['restaurant_id'])
        pizza = Pizza.query.get(data['pizza_id'])

        if not restaurant or not pizza:
            return make_response({"errors": ["validation errors"]}, 404)

        # Validate the price
        try:
            restaurant_pizza = RestaurantPizza(
                price=data['price'],
                pizza_id=data['pizza_id'],
                restaurant_id=data['restaurant_id']
            )
            db.session.add(restaurant_pizza)
            db.session.commit()

            # Return the created RestaurantPizza with nested pizza and restaurant data
            response = {
                "id": restaurant_pizza.id,
                "pizza": pizza.to_dict(),
                "pizza_id": restaurant_pizza.pizza_id,
                "price": restaurant_pizza.price,
                "restaurant": restaurant.to_dict(),
                "restaurant_id": restaurant_pizza.restaurant_id
            }
            return make_response(response, 201)

        except ValueError as e:
            # Handle validation errors (e.g., price out of range)
            db.session.rollback()
            return make_response({"errors": ["validation errors"]}, 400)  # Match the expected error messageclear
            

api.add_resource(Restaurants, '/restaurants')
api.add_resource(RestaurantById, '/restaurants/<int:id>')
api.add_resource(Pizzas, '/pizzas')
api.add_resource(RestaurantPizzas, '/restaurant_pizzas')

if __name__ == "__main__":
    app.run(port=5555, debug=True)