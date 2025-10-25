# API
> [!NOTE]  
> Would like to add your own city? Feel free to create a Pull Request :)

## How it works
The backend consists of three main parts:
0. A [script](https://github.com/mensabuddies/facility-api/blob/main/app/src/cron/init_db.py) initializing the database with some static data from [`facilities.json`](https://github.com/mensabuddies/facility-api/blob/main/assets/facilities.json)
1. A cronjob getting the raw HTML from the site of the Studierendenwerk, stripping the unnecessary parts away and storing it as files (see [`app/src/cron/fetcher`](https://github.com/mensabuddies/facility-api/tree/main/app/src/cron/fetcher)).
2. A second cronjob parsing the downloaded files and populating the Postgres database (see [`app/src/cron/db_updater`](https://github.com/mensabuddies/facility-api/tree/main/app/src/cron/db_updater)).
3. The actual API reading the data from the database and returning the JSON (see [`app/src/routes`](https://github.com/mensabuddies/facility-api/tree/main/app/src/routes)). You can find API-Documententation on the [`/docs` route](https://facility-api.mensabuddies.de/docs).

## How would I add a new city?
> Tbh, the project needs some refactoring to make it easier to extend. By now, its only in version 1.0 :'D

1. Add the static data to the [`facilities.json`](https://github.com/mensabuddies/facility-api/blob/main/assets/facilities.json)
2. Run the database initialization script like this: `python -m app.src.cron.init_db`
3. Adjust [`app/src/cron/fetcher`](https://github.com/mensabuddies/facility-api/tree/main/app/src/cron/fetcher) to strip away the unnecessary parts. You can skip this step if you do not perform webscraping and access an API directly.
4. Extend [`app/src/cron/db_updater`](https://github.com/mensabuddies/facility-api/tree/main/app/src/cron/db_updater) to write the data to the database (either by parsing the HTML or by calling an API provided by a Studierendenwerk)

Now your cities canteens should be available via the API :)

## Getting started
This API uses [FastAPI](https://fastapi.tiangolo.com/) and [SQLModel](https://sqlmodel.tiangolo.com/). Start the development server with: 

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
