from sqlalchemy import inspect, text

from backend.database.session import Base, engine
from backend.database.models import Noticias

Base.metadata.create_all(engine)

# create_all não altera tabelas existentes. Esta migração idempotente adiciona
# o campo usado para impedir que notícias entrem em mais de um roteiro.
if "noticias" in inspect(engine).get_table_names():
    columns = {column["name"] for column in inspect(engine).get_columns("noticias")}
    with engine.begin() as connection:
        if "roteiro_gerado_em" not in columns:
            column_type = (
                "TIMESTAMP WITH TIME ZONE"
                if engine.dialect.name == "postgresql"
                else "DATETIME"
            )
            connection.execute(
                text(f"ALTER TABLE noticias ADD COLUMN roteiro_gerado_em {column_type}")
            )
        connection.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_noticias_roteiro_gerado_em "
                "ON noticias (roteiro_gerado_em)"
            )
        )

print("Banco e tabelas criados com sucesso!")
