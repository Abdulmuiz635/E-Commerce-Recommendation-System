from sqlalchemy import create_engine, Column, Integer, String, Float, Date, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import pandas as pd
from datetime import datetime, timedelta
import numpy as np

# Create SQLite engine & session
engine = create_engine("sqlite:///ecommerce.db", echo=False)
Session = sessionmaker(bind=engine)
Base = declarative_base()

# Define tables
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    full_name = Column(String(120), nullable=False)
    email = Column(String, unique=True, nullable=False)
    address = Column(String(120), nullable=False)
    password_hash = Column(String(128), nullable=False)
    registered_on = Column(DateTime, default=datetime.utcnow)

    cart_items = relationship('CartItem', back_populates='user')
    purchases = relationship('Purchase', back_populates='user')

class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(String)
    category = Column(String(100))
    price = Column(Float, nullable=False)
    image_path = Column(String(500))

    cart_items = relationship('CartItem', back_populates='product')
    purchases = relationship('Purchase', back_populates='product')

class Purchase(Base):
    __tablename__ = 'purchases'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship('User', back_populates='purchases')
    product = relationship('Product', back_populates='purchases')

class CartItem(Base):
    __tablename__ = 'cart_items'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    quantity = Column(Integer, default=1)
    added_on = Column(DateTime, default=datetime.utcnow)

    user = relationship('User', back_populates='cart_items')
    product = relationship('Product', back_populates='cart_items')

def clean_price(price_str):
    if isinstance(price_str, str):
        price_str = price_str.replace("₦", "").replace(",", "").strip()
        if "-" in price_str:
            price_str = price_str.split("-")[0].strip()
        try:
            return float(price_str)
        except ValueError:
            return 0.0
    elif isinstance(price_str, (int, float)):
        return float(price_str)
    else:
        return 0.0

def load_data():
    Base.metadata.create_all(engine)
    session = Session()

    try:
        df = pd.read_excel("Ecommerce dataset.xlsx")
        # Insert products into the db
        products_map = {}  
        for _, row in df.iterrows():
            product = Product(
                id=row['product_id'],
                name=row['name'],
                description=row['description'],
                category=row['category'],
                price=clean_price(row['price']),
                image_path=row['image path']
            )
            session.merge(product)
            products_map[product.id] = product  

        # Create dummy users
        users_map = {}  # To store user_id to User object
        for i in range(1, 10):
            user = User(
                id=i,
                full_name=f"User {i}",
                email=f"user{i}@example.com",
                address="123 Main St",
                password_hash="hashed_password",
                registered_on=datetime.utcnow()
            )
            session.merge(user)
            users_map[user.id] = user  

        # Create dummy purchases
        user_ids = list(users_map.keys())
        product_ids = list(products_map.keys())
        for _ in range(50):
            user_id = np.random.choice(user_ids)
            product_id = np.random.choice(product_ids)
            date = datetime.now() - timedelta(days=np.random.randint(0, 180))

            print(f"About to create Purchase: user_id={user_id} (type: {type(user_id)}), product_id={product_id} (type: {type(product_id)})")

            purchase = Purchase(
                user_id=int(user_id),  # Ensure integer
                product_id=int(product_id),  # Ensure integer
                timestamp=datetime.utcnow()
            )

            print(f"Purchase object created: user_id={purchase.user_id} (type: {type(purchase.user_id)}), product_id={purchase.product_id} (type: {type(purchase.product_id)})")

            session.add(purchase)

            print("Purchase added to session.")

        session.commit()
        print("Session committed.")
        print("Database loaded successfully.")

        # DEBUG:  Query and print a purchase
        first_purchase = session.query(Purchase).first()
        if first_purchase:
            print("--- DEBUG: First Purchase ---")
            print(f"  Purchase ID: {first_purchase.id} (type: {type(first_purchase.id)})")
            print(f"  User ID: {first_purchase.user_id} (type: {type(first_purchase.user_id)})")
            print(f"  Product ID: {first_purchase.product_id} (type: {type(first_purchase.product_id)})")
            print(f"  Timestamp: {first_purchase.timestamp} (type: {type(first_purchase.timestamp)})")
        else:
            print("--- DEBUG: No Purchase found in the database! ---")

    except Exception as e:
        session.rollback()
        print(f"Error loading database: {e}")

    finally:
        session.close()

if __name__ == '__main__':
    load_data()
    pass