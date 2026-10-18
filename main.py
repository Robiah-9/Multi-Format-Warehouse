import sys
import pandas as pd

from extract import extract_products_and_reviews, extract_orders
from clean import clean_products, clean_reviews, clean_orders
from load import load_all

PRODUCTS_JSON = r"data/product_reviews.json"
ORDERS_CSV = r"data/orders__1_.csv"
ERRORS_CSV = "errors.csv"


def build_errors(*rejected_tables):
    errors = pd.concat(rejected_tables, ignore_index=True)
    first = ["source", "reason"]
    return errors[first + [c for c in errors.columns if c not in first]]


def main():
    products_raw, reviews_raw = extract_products_and_reviews(PRODUCTS_JSON)
    orders_raw = extract_orders(ORDERS_CSV)
    products = clean_products(products_raw)
    reviews, reviews_rejected, review_dupes = clean_reviews(reviews_raw, products["product_id"])
    orders, orders_rejected, order_dupes = clean_orders(orders_raw, products["product_id"])
    errors = build_errors(orders_rejected, reviews_rejected)
    errors.to_csv(ERRORS_CSV, index=False)
    rows_in = len(reviews_raw) + len(orders_raw)
    dupes = review_dupes + order_dupes
    rejected = len(errors)
    loaded = len(reviews) + len(orders)
    if rows_in != loaded + rejected + dupes:
        raise ValueError(
            f"Row counts don't balance: in={rows_in}, loaded={loaded}, "
            f"rejected={rejected}, duplicates={dupes}"
        )

    counts = load_all(products, reviews, orders)

    print(f"rows in:            {rows_in}")
    print(f"duplicates removed: {dupes}")
    print(f"rejected:           {rejected}  (see {ERRORS_CSV})")
    print(f"loaded:             {loaded}")
    print(f"sent to Postgres:   {counts}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Pipeline failed: {e}", file=sys.stderr)
        sys.exit(1)