### Setup DB Path

For local development, you need to set the DEPLOYMENT_FILESYSTEM_PATH.  When deployed in emp cloud, this will be set automatically.

```bash
export DEPLOYMENT_FILESYSTEM_PATH=/tmp
```

### Initialize the migrations
```bash
alembic init _alembic
```

### Create a new migration
```bash
alembic revision --autogenerate -m "message"
```

### Apply the migrations
```bash
alembic upgrade head
```

### Run the example
```bash
# include the DEPLOYMENT_FILESYSTEM_PATH to avoid using the default
DEPLOYMENT_FILESYSTEM_PATH=/tmp python -m simple_db.main
```


# NOTE: to run locally, you need to set the DEPLOYMENT_FILESYSTEM_PATH to a temporary directory.
#       this is where you will store the database files.
```bash
export DEPLOYMENT_FILESYSTEM_PATH=/tmp
```
