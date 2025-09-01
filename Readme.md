# API
This API uses FastAPI. Start the development server with: 

```bash
fastapi dev app.py
```

The APIs documentation can be found on the `/docs` or `/redoc` route.

## Cronjobs
You can run the cronjobs from the project-root like this:
```bash
python -m app.src.cron.init_db
python -m app.src.cron.fetcher.fetcher 
python -m app.src.cron.db_updater.db_updater
```

## Alembic
This project uses Alembic for database migrations.

1. You can verify the database connection in your `alembic.ini` and `env.py` files by running:

    ```bash
    alembic current
    ```

2. After making a change to the DB schema, commit it:

    ```bash
    alembic revision --autogenerate -m "Add phone_number to Customer"
    ```
    This creates a new migration script in the `migrations/versions/` directory. Each migration script includes `upgrade()` and `downgrade()` functions:

   - `upgrade()`: Defines how to apply the migration (e.g., add a column).
   - `downgrade()`: Defines how to undo the migration (e.g., remove the column).

3. Run the migration to apply the changes to the database:

    ```bash
    alembic upgrade head
    ```

4. To view all applied and pending migrations:

    ```bash
    alembic history
    ```

> [!NOTE]
> The migration scripts generated will probably not run due to a missing import. Just add `import sqlmodel` to the file.

> [!TIP]
> To undo the last migration:
> 
> ```bash
> alembic downgrade -1
> ```
> To revert to a specific migration (using its revision ID):
> 
> ```bash
> alembic downgrade <revision_id>
> ```

## Docker
To build the image:
```bash
docker buildx build --platform linux/amd64 -t mensabuddies-public-api . --output type=docker
docker save -o mensabuddies-public-api.tar mensabuddies-public-api
```