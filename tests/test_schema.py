from app.core.database import Engine
from app.schema.schema_loader import SchemaLoader
from app.schema.schema_formatter import SchemaFormatter

loadr = SchemaLoader(Engine)
schema = loadr.load_schema()
text = SchemaFormatter.format(schema)
print(text)