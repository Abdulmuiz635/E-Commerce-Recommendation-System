# E-Commerce Recommendation System

A product recommendation engine that combines purchase history with content similarity and falls back to popular items when there is not enough data, shown inside a working demo store.

## Overview
New users and new products have no history, which is the cold-start problem for recommenders. This project handles it by combining several signals. It uses what a user has bought, what is popular across all users, and how similar products are to each other, so there is always a sensible recommendation to show.

## How it works
The system reads purchase history from the database and looks for patterns. For similar-item suggestions it builds TF-IDF vectors from product names and descriptions and ranks products by cosine similarity. When a user or product is too new to have history, it falls back to the most frequently purchased items. A Flask storefront ties it together with accounts, a catalogue, a cart, and product pages.

## Tech stack
- Python, Flask, SQLAlchemy, SQLite
- Scikit-Learn for TF-IDF and cosine similarity
- pandas for data handling

## Getting started
    pip install -r requirements.txt
    python app.py

## Notes
The store ships with sample data so the recommendations can be demonstrated without an existing customer base.
