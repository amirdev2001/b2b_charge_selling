# B2B Charge Shop

A Django-based B2B (Business-to-Business) e-commerce platform with robust seller accounting and transaction management. The system features real-time credit management, concurrent transaction handling, and comprehensive financial logging.

## Setup

#### Notice
- In the Nginx config, I have set `b2b.local` as the url of serving.
if you want to serve it on localhost or your own domain,
change the nginx/nginx.conf file line 10, to your own domain address or local host.

- You must have Docker compose installed.

```bash
docker-compose up --build -d
```

- Create the admin panel super user

```bash
docker-compose exec app python manage.py createsuperuser
```

## Features

- **Seller Management**
  - Individual seller accounts with credit balance tracking
  - Secure user authentication
  - Real-time credit updates

- **Transaction Processing**
  - Atomic transaction handling
  - Concurrent sale processing
  - Comprehensive transaction logging
  - UUID-based transaction tracking

- **Financial Integrity**
  - Transaction atomicity guaranteed through Django's transaction management
  - Double-entry accounting system
  - Automatic balance verification
  - Complete audit trail through TransactionLog

## Technical Stack

- **Backend Framework**: Django
- **Database**: PostgreSQL (recommended)
- **Asynchronous Support**: Django ASGI with asyncio
- **Authentication**: Django's built-in authentication system

## Project Structure

```
src/
├── b2b_project/          # Django project settings
├── B2B_shop/            # Main application
│   ├── models.py        # Data models
│   ├── views.py         # View controllers
│   ├── urls.py          # URL routing
│   ├── tests.py         # Test suite
│   └── migrations/      # Database migrations
├── nginx/               # Nginx configuration
└── staticfiles/         # Static assets
```

## Testing

The project includes comprehensive tests for financial integrity and concurrent operations:

```bash
docker-compose exec app python manage.py test
```

Key test scenarios include:
- Concurrent transaction processing
- Credit balance integrity
- Transaction log consistency
- Race condition handling

## API Documentation

The system provides Swagger (`{base url}/swagger/`) RESTful APIs for:
- Seller management
- Transaction processing
- Credit operations
- Balance inquiries

## Security Considerations

- All financial transactions are atomic
- Concurrent access is handled safely
- All monetary values use Decimal for precision
- Transaction logs are immutable and uniquely identified

## Performance

The system is designed to handle:
- High concurrency with async operations
- Large numbers of simultaneous transactions
- Real-time credit updates
- Efficient database operations through select_for_update

