import json
import pandas as pd


def extract_products_and_reviews(path):
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Could not find the JSON file: {path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"{path} is not valid JSON: {e}")

    product_rows = []
    review_rows = []

    for product in data["products"]:
        product_rows.append({
            "product_id": product["product_id"],
            "product_name": product["product_name"],
            "category": product["category"],
        })
        for review in product["reviews"]:
            review_rows.append({**review, "product_id": product["product_id"]})

    return pd.DataFrame(product_rows), pd.DataFrame(review_rows)


def extract_orders(path):
    try:
        return pd.read_csv(path)
    except FileNotFoundError:
        raise FileNotFoundError(f"Could not find the orders CSV: {path}")
