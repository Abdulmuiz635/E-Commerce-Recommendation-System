from sqlalchemy import create_engine, Column, Integer, String, Float, Date, DateTime, ForeignKey, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
from database import engine
from database import User, Product, Purchase
from collections import Counter
from sqlalchemy import desc, or_
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

Session = sessionmaker(bind=engine)


def get_user_purchase_history(session, user_id):
    """Fetches the products the user has purchased"""
    purchases = session.query(Purchase).filter_by(user_id=user_id).all()
    return [purchase.product_id for purchase in purchases]


def get_top_purchased_products(session, limit=5):
    """Returns the top most frequently purchased products as a fallback"""
    product_counts = session.query(
        Purchase.product_id, func.count(Purchase.product_id).label('count')
    ).group_by(Purchase.product_id).order_by(desc('count')).limit(limit).all()
    return [row.product_id for row in product_counts]


def get_similar_item_recommendations(session, product, top_n=5):
    """Recommends items with similar name or description"""
    all_products = session.query(Product).all()
    if not all_products or product not in all_products:
        return []

    tfidf_vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf_vectorizer.fit_transform([p.name + ' ' + (p.description or '') for p in all_products])

    product_index = -1
    for i, p in enumerate(all_products):
        if p.id == product.id:
            product_index = i
            break

    if product_index == -1:
        return []

    cosine_similarities = cosine_similarity(tfidf_matrix[product_index], tfidf_matrix)[0]
    similar_indices = cosine_similarities.argsort()[::-1][1:top_n + 1]  

    similar_products = [all_products[i] for i in similar_indices]
    return similar_products


def get_item_based_recommendations(session, user_id, top_n=5):
    """Item-based collaborative filtering recommendations"""
    purchases = session.query(Purchase).all()
    df = pd.DataFrame([{"user_id": p.user_id, "product_id": p.product_id} for p in purchases])

    if df.empty or user_id not in df['user_id'].unique():
        print("Item-based: Using similar item recommendations (no user data)")
        # Get a random product to find similar items for
        random_product = session.query(Product).order_by(func.random()).first()
        if random_product:
            return get_similar_item_recommendations(session, random_product, top_n)
        else:
            return get_top_purchased_products(session, top_n)

    purchase_matrix = df.pivot_table(index='user_id', columns='product_id', aggfunc=len, fill_value=0)
    sim_matrix = cosine_similarity(purchase_matrix.T)
    sim_df = pd.DataFrame(sim_matrix, index=purchase_matrix.columns, columns=purchase_matrix.columns)

    user_purchases = purchase_matrix.loc[user_id]
    scores = sim_df.dot(user_purchases).sort_values(ascending=False)

    already_bought = set(df[df['user_id'] == user_id]['product_id'])
    recommended_ids = [pid for pid in scores.index if pid not in already_bought][:top_n]

    recommended_products = session.query(Product).filter(Product.id.in_(recommended_ids)).all()
    print(f"Item-based: Found {len(recommended_products)} recommendations")
    return recommended_products


def get_user_based_recommendations(session, user_id, top_n=5):
    """User-based collaborative filtering recommendations"""
    user_products = get_user_purchase_history(session, user_id)
    if not user_products:
        print("User-based: Using similar item recommendations (no user history)")
        # Get a random product to find similar items for
        random_product = session.query(Product).order_by(func.random()).first()
        if random_product:
            return get_similar_item_recommendations(session, random_product, top_n)
        else:
            return get_top_purchased_products(session, top_n)

    similar_users = session.query(Purchase).filter(Purchase.product_id.in_(user_products)).all()
    user_freq = Counter([s.user_id for s in similar_users if s.user_id != user_id])

    top_user_ids = [uid for uid, _ in user_freq.most_common(3)]
    recommended = session.query(Purchase).filter(Purchase.user_id.in_(top_user_ids)).all()

    product_ids = [r.product_id for r in recommended if r.product_id not in user_products]
    product_counts = Counter(product_ids)
    top_product_ids = [pid for pid, _ in product_counts.most_common(top_n)]

    recommended_products = session.query(Product).filter(Product.id.in_(top_product_ids)).all()
    print(f"User-based: Found {len(recommended_products)} recommendations")
    return recommended_products


def get_hybrid_recommendations(session, user_id, top_n=5, item_weight=0.8, user_weight=0.2):
    """Combines item-based and user-based recommendations"""
    item_recs = get_item_based_recommendations(session, user_id, top_n)
    user_recs = get_user_based_recommendations(session, user_id, top_n)

    item_rec_ids = {rec.id: item_weight for rec in item_recs}
    user_rec_ids = {rec.id: user_weight for rec in user_recs if rec.id not in item_rec_ids}
    item_rec_ids.update(user_rec_ids)

    # Sort and get top N
    final_rec_ids_sorted = sorted(item_rec_ids.items(), key=lambda item: item[1], reverse=True)[:top_n]
    final_rec_ids = [rec_id for rec_id, _ in final_rec_ids_sorted]
    final_recs = session.query(Product).filter(Product.id.in_(final_rec_ids)).all()

    print(f"Hybrid: Found {len(final_recs)} recommendations")
    return final_recs


def get_recommendations(user_id, top_n=5):
    """Main function to get recommendations, using a hybrid approach with fallback"""
    session = Session()
    try:
        user_purchases = get_user_purchase_history(session, user_id)
        if not user_purchases:
            print("No user purchase history, using similar item recommendations as fallback.")
            # Get a random product to find similar items for
            random_product = session.query(Product).order_by(func.random()).first()
            if random_product:
                return get_similar_item_recommendations(session, random_product, top_n)
            else:
                print("No products available to find similar items.")
                return get_top_purchased_products(session, top_n)
        else:
            return get_hybrid_recommendations(session, user_id, top_n)
    finally:
        session.close()


if __name__ == '__main__':
    from database import load_data

    load_data()

    session = Session()
    try:
        user_id = 1
        recommendations = get_recommendations(user_id)
        if recommendations:
            print("\nRecommendation System Output:\n")
            print(f"Recommendations for User {user_id}:")
            for product in recommendations:
                print(f"- {product.name} (ID: {product.id})")
        else:
            print("No recommendations found.")
    finally:
        session.close()