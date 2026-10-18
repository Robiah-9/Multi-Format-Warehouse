import os
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv


def get_connection():
    load_dotenv()
    required = ["DB_USER", "DB_PASSWORD", "DB_HOST", "DB_PORT", "DB_NAME"]

    missing = [name for name in required if not os.getenv(name)]
    if missing:
        raise RuntimeError(f"Missing environment variables: {', '.join(missing)}")

    try:
        return psycopg2.connect(
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
        )
    except psycopg2.OperationalError as e:
        raise RuntimeError(
            f"Could not connect to Postgres at "
            f"{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}: {e}"
        )


def _to_rows(df, cols):
    sub = df[cols].astype(object)
    return list(sub.where(df[cols].notna(), None).itertuples(index=False, name=None))


def load_all(products, reviews, orders):
    products_sql = """
        INSERT INTO products (product_id, product_name, category)
        VALUES %s
        ON CONFLICT (product_id) DO UPDATE SET
            product_name = EXCLUDED.product_name,
            category     = EXCLUDED.category
    """
    reviews_sql = """
        INSERT INTO reviews (review_id, customer_id, product_id, rating, comment, review_date)
        VALUES %s
        ON CONFLICT (review_id) DO UPDATE SET
            customer_id = EXCLUDED.customer_id,
            product_id  = EXCLUDED.product_id,
            rating      = EXCLUDED.rating,
            comment     = EXCLUDED.comment,
            review_date = EXCLUDED.review_date
    """
    orders_sql = """
        INSERT INTO orders (order_id, customer_id, product_id, quantity, unit_price, order_date, price_imputed)
        VALUES %s
        ON CONFLICT (order_id) DO UPDATE SET
            customer_id   = EXCLUDED.customer_id,
            product_id    = EXCLUDED.product_id,
            quantity      = EXCLUDED.quantity,
            unit_price    = EXCLUDED.unit_price,
            order_date    = EXCLUDED.order_date,
            price_imputed = EXCLUDED.price_imputed
    """

    conn = get_connection()
    try:
        with conn:                     
            with conn.cursor() as cur:
              
                execute_values(cur, products_sql,
                               _to_rows(products, ["product_id", "product_name", "category"]))
                execute_values(cur, reviews_sql,
                               _to_rows(reviews, ["review_id", "customer_id", "product_id",
                                                  "rating", "comment", "review_date"]))
                execute_values(cur, orders_sql,
                               _to_rows(orders, ["order_id", "customer_id", "product_id",
                                                 "quantity", "unit_price", "order_date",
                                                 "price_imputed"]))
    except psycopg2.Error as e:
        raise RuntimeError(f"Load failed and was rolled back: {e}")
    finally:
        conn.close()

    return {"products": len(products), "reviews": len(reviews), "orders": len(orders)}