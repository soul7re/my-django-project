# LaundryFlow

LaundryFlow is a Django-based laundry pickup, processing and delivery scheduling system designed to help small laundry collection businesses manage customers, clothing orders, laundrymen, payments, commissions and delivery schedules. The system uses PostgreSQL as its relational database and implements priority-based scheduling and workload balancing to organize laundry operations efficiently.

## Features

- Secure login and logout using Django authentication.
- Dashboard for today's pickups, deliveries, active orders, and financial totals.
- Customer management with order history, total spend, and outstanding balance.
- Laundryman management with active workload, completed orders, and item totals.
- Order creation with multiple clothing items.
- Automatic total item, customer bill, commission, laundryman earnings, and balance calculations.
- Multiple payments per order.
- Pickup and delivery schedule pages with date filtering.
- Processing schedule for orders sent to laundrymen.
- Priority scheduling for overdue and urgent orders.
- Laundryman workload balancing recommendation.
- Reports with date range filtering.
- Django Admin configuration for all core models.
- Sample data command for project demonstration.
- Django tests for core business rules and protected pages.

## Technologies

- Python
- Django
- PostgreSQL
- Django Templates
- HTML
- CSS
- Vanilla JavaScript

No React, Vue, Angular, Flask, Node.js, or other backend/frontend frameworks are used.

## Project Structure

```text
LaundryFlow/
  manage.py
  laundryflow/
  laundry/
  templates/
  static/
  requirements.txt
  .env.example
  README.md
```

## PostgreSQL Setup

Install PostgreSQL from the official PostgreSQL installer or your operating system package manager.

Start PostgreSQL, then create the database with `psql`:

```bash
psql -U postgres
CREATE DATABASE laundryflow;
\q
```

The same database can also be created in pgAdmin:

1. Open pgAdmin.
2. Connect to your PostgreSQL server.
3. Right-click Databases.
4. Choose Create > Database.
5. Use the name `laundryflow`.

## Environment Variables

Copy `.env.example` to `.env` and update values for your local PostgreSQL setup:

```text
SECRET_KEY=change-this-development-secret
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

DB_NAME=laundryflow
DB_USER=postgres
DB_PASSWORD=
DB_HOST=localhost
DB_PORT=5432
```

Do not commit `.env`. It is ignored by `.gitignore`.

## Installation

Create and activate a virtual environment:

```bash
python -m venv .venv
.venv\Scripts\activate
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

## Migrations

Create and apply database migrations:

```bash
python manage.py makemigrations
python manage.py migrate
```

This creates the Django and LaundryFlow tables in PostgreSQL.

## Superuser

Create an administrator account:

```bash
python manage.py createsuperuser
```

## Sample Data

Load demonstration records:

```bash
python manage.py seed_sample_data
```

The sample data includes Nigerian customer names, laundrymen, orders with different statuses, multiple clothing item types, payment statuses, pickup dates, and delivery dates.

## Running the Project

Start the development server:

```bash
python manage.py runserver
```

Open:

```text
http://127.0.0.1:8000/
```

Login with your superuser account.

## Testing

Run the test suite:

```bash
python manage.py test
```

The tests cover customer creation, laundryman creation, order creation, clothing item totals, payment balances, payment status, order status, priority scheduling, workload balancing, inactive laundryman validation, date validation, and authentication protection.

## Financial Calculations

The system uses the values in Business Settings instead of hard-coding prices throughout the app.

```text
Customer bill = Number of items x Price per item
Commission = Number of items x Commission per item
Laundryman earnings = Customer bill - Commission
Balance = Customer bill - Amount paid
```

Default values:

```text
Price per item = NGN 500
Commission per item = NGN 100
Default processing period = 2 days
```

Example:

```text
5 clothes x NGN 500 = NGN 2,500 customer bill
5 clothes x NGN 100 = NGN 500 commission
NGN 2,500 - NGN 500 = NGN 2,000 laundryman earnings
```

## Scheduling Algorithm

LaundryFlow uses Priority-Based Scheduling and Laundryman Workload Balancing.

Priority scheduling is simple:

```text
If an order is overdue, priority is Critical.
If the delivery date is today or tomorrow, priority is High.
If the delivery date is within the next week, priority is Normal.
Otherwise, priority is Low or Normal depending on whether a delivery date exists.
```

Workload balancing is also simple:

```text
Find all active laundrymen.
Count active orders assigned to each laundryman.
Recommend the active laundryman with the lowest active order count.
```

The administrator can still choose a different laundryman manually.

## Project Defense Notes

Why Django?

Django provides the backend framework, ORM, authentication, URL routing, forms, templates, admin panel, sessions, messages, CSRF protection, and testing tools needed to build the application.

Why PostgreSQL?

PostgreSQL is a robust relational database suitable for related records such as customers, laundrymen, orders, clothing items, and payments while maintaining data integrity.

Why a scheduling algorithm?

The business has multiple laundry orders with different deadlines. The scheduling algorithm helps prioritize urgent and overdue orders and helps balance work among laundrymen.

How is commission calculated?

Commission is calculated as the number of clothing items multiplied by the fixed commission per item.

## Security

- CSRF protection is enabled.
- Administrative pages require login.
- Passwords are handled by Django authentication.
- Database credentials are loaded from environment variables.
- `.env` is excluded from version control.
- Forms validate dates, inactive laundrymen, negative amounts, and invalid inputs.
