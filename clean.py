import pandas as pd

REVIEW_DATE_FORMATS = ("%Y-%m-%d", "%B %d, %Y", "%d/%m/%Y")
ORDER_DATE_FORMAT = "%m/%d/%Y"


def _parse_review_date(s):
    for fmt in REVIEW_DATE_FORMATS:
        result = pd.to_datetime(s, format=fmt, errors="coerce")
        if pd.notna(result):
            return result
    return pd.NaT


def clean_products(products):
    products = products.copy()
    products["category"] = products["category"].str.strip().str.lower()
    return products


def clean_reviews(reviews, valid_product_ids):
    reviews = reviews.copy()
    rows_in = len(reviews)

    # 1. duplicates
    reviews = reviews.drop_duplicates(subset=["review_id"], keep="first")
    dupes_removed = rows_in - len(reviews)

    # 2. orphans (product_id not in products)
    known = reviews["product_id"].isin(valid_product_ids)
    orphans = reviews[~known].copy()
    orphans["reason"] = "product_id not found in products"
    reviews = reviews[known]

    # 3. invalid ratings
    ok = reviews["rating"].between(1, 5)
    bad_rating = reviews[~ok].copy()
    bad_rating["reason"] = "rating must be between 1 and 5"
    reviews = reviews[ok]

    # 4. dates: parse, reject any that no format could read
    parsed = reviews["review_date"].apply(_parse_review_date)
    date_ok = parsed.notna()
    bad_date = reviews[~date_ok].copy()
    bad_date["reason"] = "unparseable review_date"
    valid = reviews[date_ok].copy()
    valid["review_date"] = parsed[date_ok]

    # 5. combine rejects
    rejected = pd.concat([orphans, bad_rating, bad_date], ignore_index=True)
    rejected["source"] = "reviews"

    assert rows_in == dupes_removed + len(valid) + len(rejected), "review row counts don't add up"
    return valid, rejected, dupes_removed


def clean_orders(orders, valid_product_ids):
    orders = orders.copy()
    rows_in = len(orders)

    # 1. duplicates (whole row)
    orders = orders.drop_duplicates()
    dupes_removed = rows_in - len(orders)

    # 2. orphans
    known = orders["product_id"].isin(valid_product_ids)
    orphans = orders[~known].copy()
    orphans["reason"] = "product_id not found in products"
    orders = orders[known]

    # 3. quantity
    allowed = orders["quantity"] >= 1
    bad_qty = orders[~allowed].copy()
    bad_qty["reason"] = "quantity must be at least 1"
    orders = orders[allowed].copy()

    # 4. prices: flag first, then fill, then round
    orders["price_imputed"] = orders["unit_price"].isna()
    means = orders.groupby("product_id")["unit_price"].transform("mean")
    orders["unit_price"] = orders["unit_price"].fillna(means).round(2)

    price_ok = orders["unit_price"].notna()
    no_price = orders[~price_ok].copy()
    no_price["reason"] = "unit_price missing and no product average"
    orders = orders[price_ok].copy()

    # 5. dates
    parsed = pd.to_datetime(orders["order_date"], format=ORDER_DATE_FORMAT, errors="coerce")
    date_ok = parsed.notna()
    bad_date = orders[~date_ok].copy()
    bad_date["reason"] = "unparseable order_date"
    valid = orders[date_ok].copy()
    valid["order_date"] = parsed[date_ok]

    # 6. combine rejects
    rejected = pd.concat([orphans, bad_qty, no_price, bad_date], ignore_index=True)
    rejected["source"] = "orders"

    assert rows_in == dupes_removed + len(valid) + len(rejected), "order row counts don't add up"
    return valid, rejected, dupes_removed