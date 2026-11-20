# Data-Backed Python App

A simple command line application that connects to a virtual store database that lets a user make and see changes.

## Features

- **Add a product:** User inputs a name, category, price and stock, then saves the new product into the database.
- **Place an order:** Takes the customer's email, product name and quantity, then creates an order of the product, reducing from the database.
- **Store report:** Shows user the number of users, total inventory and orders made, with the stock and prices, with the top 3 customers by items ordered.
- **Low-stock report:** Shows user for any products that have less than 10 items in stock.

## Tech Used

- **Python 3**: language app was written in.
- **PostgreSQL**: database that stores users, products and orders.
- **Docker**: runs the PostgreSQL database in a container (`pg`).
- **SQLAlchemy**: connects Python to the DB. The app uses ORM, thus tables are Python classes.
- **psycopg2-binary:** the driver SQLAlchemy uses to talk to PostgreSQL.
- **python-dotenv:** loads the database URL from the `.env` file, so no passwords are written in the code.

## Project Structure

- `dashboard.py`: The main script. Connects to the DB, models are maintained and runs the menu. Takes in user input.
- `models.py`: SQLAlchemy models mapping `users`, `products` and `orders` to Python classes `User`, `Product` and `Order`.
- `requirements.txt`: required Python Packages. Install with `pip install -r requirements.txt`
- `.env.example`: template for the `.env` file. Copy to `.env` and fill in your own `DATABASE_URL`.

## Setup

1. **Create a virtual environment**

   ```bash
   python -m venv .venv
   ```

2. **Activate it**

   - Windows (PowerShell): `.venv\Scripts\Activate.ps1`
   - macOS / Linux: `source .venv/bin/activate`

   Your prompt should now start with `(.venv)`.

3. **Install the packages**

   ```bash
   pip install -r requirements.txt
   ```

4. **Create your `.env` file**

   Copy `.env.example` to `.env` and fill in your database URL:

   ```
   DATABASE_URL=postgresql+psycopg2://postgres:<password>@localhost:5432/postgres
   ```

5. **Start the database**

   Open Docker Desktop, then start the PostgreSQL container:

   ```bash
   docker start pg
   ```

6. **Run the app**

   ```bash
   python dashboard.py
   ```

   ## Usage

Run the app and pick an option from the menu:

```
Choose options below:
  1) Add a product
  2) Place an order
  3) Show the store report again
  4) Low-stock alert
  q) Quit
>
```

### 1. Add a product

```
Product name: Nimbus Wireless Charger
Category: Electronics
Price: 34.99
Stock: 25
Added product 'Nimbus Wireless Charger' with id 208
```

### 2. Place an order

```
Customer email: user168@example.com
Product name: Nimbus Wireless Charger
Quantity: 3
Order 30003 placed: 3 x Nimbus Wireless Charger for user168@example.com (22 left in stock)
```

If there isn't enough stock, the order is refused and nothing is saved:

```
Customer email: user168@example.com
Product name: Unreleased Prototype
Quantity: 1
Order refused: Not enough stock for 'Unreleased Prototype': 0 left, 1 requested.
```

### 3. Store report

Prints the counts, the full catalog, and the top 3 customers:

```
=== Store Dashboard ===
Users: 1001 | Products: 202 | Orders: 30001

Catalog:
  Aero Backpack 126           $55.79   (stock 378)
  ...

Top customers:
  user168@example.com  - 144 items
  user183@example.com  - 142 items
  user826@example.com  - 140 items
```

### 4. Low-stock alert

```
Low stock (under 10):
  Unreleased Prototype - 0 left
  Nova Desk Lamp 21 - 1 left
```