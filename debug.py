import sys
import os
from dotenv import load_dotenv

# Add app directory to path to allow for relative imports
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

print("Loading .env file...")
load_dotenv()
print("Starting debug script...")
try:
    # We need to make sure all modules are imported to catch any errors
    from app import models, security
    from app.routers import dashboard, webhook
    from app.database import Base, create_db_and_tables, engine

    print("Imports successful.")

    # Check if tables are registered in metadata
    registered_tables = list(Base.metadata.tables.keys())
    print(f"Tables known to SQLAlchemy Base: {registered_tables}")

    if not registered_tables:
        print("Error: Models are not being registered with SQLAlchemy's Base. Check imports.")
    else:
        print("Calling create_db_and_tables()...")
        create_db_and_tables()
        print("create_db_and_tables() finished.")

        # Verify connection
        print("Attempting to connect to the database engine...")
        with engine.connect() as connection:
            print("Successfully connected to the database engine.")

    print("Debug script finished successfully.")

except Exception as e:
    import traceback
    print("\n--- AN ERROR OCCURRED ---")
    print(e)
    print("-------------------------")
    traceback.print_exc()
    print("-------------------------")
