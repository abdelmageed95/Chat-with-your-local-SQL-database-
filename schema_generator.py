from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import Inspector
from dotenv import load_dotenv
import os

load_dotenv()


USER = os.getenv("POSTGRES_USER")
PASSWORD = os.getenv("POSTGRES_PASSWORD")
HOST = os.getenv("POSTGRES_HOST")
PORT = os.getenv("POSTGRES_PORT")
DB_NAME = os.getenv("POSTGRES_DB")

def get_full_schema(database_url: str, schema_name: str = "public") -> str:
    """
    Retrieve the full schema of a PostgreSQL database as a formatted string.

    Args:
        database_url (str): Database connection URL (e.g., "postgresql+psycopg2://user:password@host:port/dbname").
        schema_name (str, optional): Schema to inspect. Defaults to "public".

    Returns:
        str: Formatted string containing schema details for all tables.

    Raises:
        Exception: If database connection or schema retrieval fails.
    """
    try:
        # Create SQLAlchemy engine
        engine = create_engine(database_url)
        inspector: Inspector = inspect(engine)

        schema_text = ""
        tables = inspector.get_table_names(schema=schema_name)

        for table_name in tables:
            schema_text += f"Table: {table_name}\n"

            # Columns
            columns = inspector.get_columns(table_name, schema=schema_name)
            schema_text += "Columns:\n"
            for col in columns:
                schema_text += f"  - {col['name']}: {col['type']} (Nullable: {col['nullable']})\n"

            # Primary Keys
            pk = inspector.get_pk_constraint(table_name, schema=schema_name)["constrained_columns"]
            schema_text += f"Primary Keys: {pk}\n"

            # Foreign Keys
            fks = inspector.get_foreign_keys(table_name, schema=schema_name)
            schema_text += "Foreign Keys:\n"
            for fk in fks:
                schema_text += f"  - {fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}\n"

            # Indexes
            indexes = inspector.get_indexes(table_name, schema=schema_name)
            schema_text += "Indexes:\n"
            for idx in indexes:
                schema_text += f"  - {idx['name']}: {idx['column_names']} (Unique: {idx['unique']})\n"

            schema_text += "\n"

        return schema_text.strip()

    except Exception as e:
        raise Exception(f"Failed to retrieve schema: {str(e)}")



if __name__ == "__main__":
    DATABASE_URL = f"postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}:{PORT}/{DB_NAME}"
    SCHEMA_NAME = "public"

    try:
        schema = get_full_schema(DATABASE_URL, SCHEMA_NAME)
        with open("schema.txt", "w") as f:
            f.write(schema)
        print("Schema Generated")
    except Exception as e:
        print(f"Error: {str(e)}")