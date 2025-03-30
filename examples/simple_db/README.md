# Initialize the migrations
```bash
alembic init alembic
```

# Create a new migration
```bash
alembic revision --autogenerate -m "message"
```

# Apply the migrations
```bash
alembic upgrade head
```

to run the example:
```bash
# include the DEPLOYMENT_FILESYSTEM_PATH to avoid using the default
DEPLOYMENT_FILESYSTEM_PATH=/tmp python -m simple_db.main
```


# NOTE: to run locally, you need to set the DEPLOYMENT_FILESYSTEM_PATH to a temporary directory.
#       this is where you will store the database files.
```bash
export DEPLOYMENT_FILESYSTEM_PATH=/tmp
```
