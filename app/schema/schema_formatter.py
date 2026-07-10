class SchemaFormatter:

    @staticmethod
    def format(schema):

        output = []

        for table_name, table in schema.items():

            output.append(f"Table: {table_name}")

            output.append("Columns:")

            for column in table["columns"]:

                output.append(
                    f"- {column['name']} ({column['type']})"
                )

            pk = table["primary_keys"].get("constrained_columns", [])

            if pk:

                output.append(
                    f"Primary Key: {', '.join(pk)}"
                )

            foreign_keys = table["foreign_keys"]

            if foreign_keys:

                output.append("Foreign Keys:")

                for fk in foreign_keys:

                    local = ", ".join(
                        fk["constrained_columns"]
                    )

                    remote = (
                        f"{fk['referred_table']}."
                        f"{', '.join(fk['referred_columns'])}"
                    )

                    output.append(
                        f"- {local} → {remote}"
                    )

            output.append("")

        return "\n".join(output)