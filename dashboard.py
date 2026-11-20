import os
import sys
from decimal import Decimal, InvalidOperation
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, select, func
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from models import User, Product, Order

load_dotenv()

LOW_STOCK_THRESHOLD = 10

def get_engine():
    """Create and return a SQLAlchemy engine from DATABASE_URL."""
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        print("Error: DATABASE_URL is not set. Add it to your .env file.")
        sys.exit(1)

    engine = create_engine(database_url)

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except OperationalError as e:
        print("Error: could not connect to the database.")
        print("Is the container running? Try: docker start pg")
        sys.exit(1)

    return engine

def store_report(engine):
    """Print counts, the catalog, and the top 3 customers."""
    with Session(engine) as session:   # read-only: nothing to commit
        # .scalar() returns the single value of a one-row, one-column result
        users = session.scalar(select(func.count()).select_from(User))
        products = session.scalar(select(func.count()).select_from(Product))
        orders = session.scalar(select(func.count()).select_from(Order))

        print("=== Store Dashboard ===")
        print(f"Users: {users} | Products: {products} | Orders: {orders}")

        # Select only the columns we print, not whole Product objects
        catalog = session.execute(
            select(Product.name, Product.price, Product.stock).order_by(Product.name)
        ).all()

        print("\nCatalog:")
        name_width = max((len(row.name) for row in catalog), default=0)
        for row in catalog:
            price = f"${row.price:.2f}"   # build "$49.99" first, then right-align it
            print(f"  {row.name:<{name_width}}  {price:>9}   (stock {row.stock})")

        # JOIN users->orders, one group per user, add up quantities, biggest first
        total_items = func.sum(Order.quantity).label("total_items")
        top_customers = session.execute(
            select(User.email, total_items)
            .join(Order, Order.user_id == User.id)
            .group_by(User.id, User.email)
            .order_by(total_items.desc(), User.email)
            .limit(3)
        ).all()

        print("\nTop customers:")
        email_width = max((len(row.email) for row in top_customers), default=0)
        for row in top_customers:
            unit = "item" if row.total_items == 1 else "items"
            print(f"  {row.email:<{email_width}}  - {row.total_items} {unit}")


def add_product(engine, name, category, price, stock):
    """INSERT a product and return its new id."""
    with Session(engine) as session:
        product = Product(name=name, category=category, price=price, stock=stock)
        session.add(product)
        session.commit()   # the INSERT runs here; the database assigns the id
        print(f"Added product '{name}' with id {product.id}")
        return product.id


def place_order(engine, email, product_name, quantity):
    """Create an order and decrement stock in one transaction."""
    if quantity <= 0:
        raise ValueError("Quantity must be at least 1.")

    with Session(engine) as session:   # nothing is saved until session.commit()
        user_id = session.scalar(select(User.id).where(User.email == email))
        if user_id is None:
            raise ValueError(f"No user with email '{email}'.")

        # with_for_update() locks this product row until we commit, so two
        # orders placed at the same moment can't both grab the last items
        product = session.scalars(
            select(Product)
            .where(Product.name == product_name)
            .order_by(Product.id)
            .with_for_update()
        ).first()
        if product is None:
            raise ValueError(f"No product named '{product_name}'.")

        # Raising here leaves the with-block without a commit, so the session
        # throws everything away -- that is the rollback
        if product.stock < quantity:
            raise ValueError(
                f"Not enough stock for '{product_name}': "
                f"{product.stock} left, {quantity} requested."
            )

        order = Order(user_id=user_id, product_id=product.id, quantity=quantity)
        session.add(order)
        product.stock -= quantity
        session.commit()   # INSERT + UPDATE are saved together, or not at all
        print(f"Order {order.id} placed: {quantity} x {product_name} for {email} "
              f"({product.stock} left in stock)")
        return order.id


# --- Stretch goals --------------------

def low_stock_report(engine, threshold=LOW_STOCK_THRESHOLD):
    """Print every product with stock below the threshold."""
    with Session(engine) as session:
        rows = session.execute(
            select(Product.name, Product.stock)
            .where(Product.stock < threshold)
            .order_by(Product.stock, Product.name)
        ).all()

    print(f"\nLow stock (under {threshold}):")
    if not rows:
        print("  (none)")
    for row in rows:
        print(f"  {row.name} - {row.stock} left")


# --- Menu: all input() lives here, so the functions above stay testable ----

def prompt_add_product(engine):
    name = input("Product name: ").strip()
    category = input("Category: ").strip()
    if not name or not category:
        print("Name and category are both required.")
        return
    try:
        price = Decimal(input("Price: ").strip())
        stock = int(input("Stock: ").strip())
    except (InvalidOperation, ValueError):
        print("Price must be a number and stock a whole number.")
        return
    if price < 0 or stock < 0:
        print("Price and stock can't be negative.")
        return

    try:
        add_product(engine, name, category, price, stock)
    except SQLAlchemyError as e:
        print(f"Could not add product: {e.orig if hasattr(e, 'orig') else e}")


def prompt_place_order(engine):
    email = input("Customer email: ").strip()
    product_name = input("Product name: ").strip()
    try:
        quantity = int(input("Quantity: ").strip())
    except ValueError:
        print("Quantity must be a whole number.")
        return

    try:
        place_order(engine, email, product_name, quantity)
    except ValueError as e:
        print(f"Order refused: {e}")
    except SQLAlchemyError as e:
        # e.g. a database CHECK constraint rejected the values
        print(f"Order refused by the database: {e.orig if hasattr(e, 'orig') else e}")


def main():
    engine = get_engine()
    #store_report(engine)

    while True:
        print("Choose options below: ")
        print("  1) Add a product")
        print("  2) Place an order")
        print("  3) Show the store report again")
        print("  4) Low-stock alert")
        print("  q) Quit")
        choice = input("> ").strip().lower()

        if choice == "1":
            prompt_add_product(engine)
        elif choice == "2":
            prompt_place_order(engine)
        elif choice == "3":
            store_report(engine)
        elif choice == "4":
            low_stock_report(engine)
        elif choice in ("q", "quit", "exit"):
            print("Bye!")
            break
        else:
            print("Please input 1-4 or q.")


if __name__ == "__main__":
    main()
