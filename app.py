from flask import Flask, render_template, request, redirect, url_for, session, flash, g, Response, jsonify
from database import Session as DBSession, User, Product, Purchase
from recommendation import get_recommendations, get_user_purchase_history, get_hybrid_recommendations, get_similar_item_recommendations
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import create_engine
import os
import json

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Session setup
@app.before_request
def before_request():
    session.modified = True
    session.setdefault('cart_count', len(session.get("cart", [])))
    g.db_session = DBSession()

@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session = getattr(g, 'db_session', None)
    if db_session is not None:
        db_session.close()

# Landing page
@app.route("/")
def landing():
    return render_template("landing.html")

# Homepage
@app.route("/home")
def home():
    db = g.db_session
    user = db.query(User).get(session.get('user_id')) if 'user_id' in session else None
    products = db.query(Product).all()
    show_popup = request.args.get('show_popup')
    return render_template("home.html", products=products, user=user, show_popup=show_popup)

# All products page
@app.route("/products")
def products():
    db = g.db_session
    all_products = db.query(Product).all()
    return render_template("products.html", products=all_products)

# Product detail page
@app.route("/product/<int:product_id>")
def product_detail(product_id):
    db = g.db_session
    product = db.get(Product, product_id)
    if not product:
        return render_template("404.html"), 404
    return render_template("product_details.html", product=product)

# Add to cart
@app.route("/add_to_cart/<int:product_id>", methods=["POST"])
def add_to_cart(product_id):
    cart = session.get("cart", [])
    if product_id not in cart:
        cart.append(product_id)
        session["cart"] = cart
    flash("✅ Product added to cart successfully!", "success")  
    return redirect(url_for('product_detail', product_id=product_id))

# View cart
@app.route("/cart")
def cart():
    db = g.db_session
    cart_ids = session.get("cart", [])
    products = db.query(Product).filter(Product.id.in_(cart_ids)).all()
    total = sum(p.price for p in products)
    return render_template("cart.html", cart_items=products, total=total)

# Remove from cart
@app.route('/remove_from_cart/<int:product_id>', methods=['POST'])
def remove_from_cart(product_id):
    cart = session.get('cart', [])
    if product_id in cart:
        cart.remove(product_id)
        session['cart'] = cart  
    return redirect(url_for('cart'))

# Register user
@app.route("/register", methods=['GET', 'POST'])
def register():
    db = g.db_session
    if request.method == 'POST':
        full_name = request.form['full_name']
        email = request.form['email']
        address = request.form['address']
        password = request.form['password']

        if db.query(User).filter_by(email=email).first():
            flash("Email already registered.")
            return redirect(url_for('register'))

        user = User(
            full_name=full_name,
            email=email,
            address=address,
            password_hash=generate_password_hash(password)
        )
        db.add(user)
        db.commit()
        flash("Registration successful.")
        return redirect(url_for('login'))

    return render_template("register.html")

# Login user
@app.route("/login", methods=['GET', 'POST'])
def login():
    db = g.db_session
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = db.query(User).filter_by(email=email).first()

        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['user_name'] = user.full_name
            session['cart_count'] = len(session.get('cart', []))
            return redirect(url_for('home'))

        flash("Invalid credentials.")
    return render_template("login.html")

# Logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('landing'))

# User account page
@app.route("/account")
def account():
    db = g.db_session
    user = db.query(User).get(session.get('user_id'))
    if not user:
        return redirect(url_for('login'))
    purchases = db.query(Purchase).filter_by(user_id=user.id).all()
    return render_template("account.html", user=user, purchases=purchases)

# Recommendation route
@app.route("/recommendations")
def recommendations_json():
    if 'user_id' not in session:
        return jsonify({"error": "User not logged in"}), 401

    current_product_id = request.args.get('product_id')
    if not current_product_id:
        return jsonify({"error": "Product ID is missing"}), 400

    db = g.db_session
    current_product = db.query(Product).get(current_product_id)
    if not current_product:
        return jsonify({"error": "Product not found"}), 404

    user_id = session['user_id']
    user_purchases = get_user_purchase_history(db, user_id)

    if not user_purchases:
        print(f"No purchase history for user {user_id}, recommending similar items to product {current_product.name}.")
        recommended_products = get_similar_item_recommendations(db, current_product, top_n=5)
    else:
        recommended_products = get_hybrid_recommendations(db, user_id, top_n=5)

    products_data = []
    for product in recommended_products:
        products_data.append({
            'id': product.id,
            'name': product.name,
            'image_path': product.image_path,
            'price': float(product.price)
        })
    return jsonify(products_data)

# Search route
@app.route("/search")
def search():
    db = g.db_session
    query = request.args.get('q', '')
    products = db.query(Product).filter(Product.name.ilike(f"%{query}%")).all()
    return render_template("search_results.html", products=products)

if __name__ == '__main__':
    app.run(debug=True)
