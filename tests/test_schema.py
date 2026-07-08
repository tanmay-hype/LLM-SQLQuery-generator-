from app.core.database import engine
from app.schema.schema_loader import SchemaLoader

loader = SchemaLoader(engine)

schema = loader.load_schema()

print(schema)