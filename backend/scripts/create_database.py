from backend.database.session import Base, engine
from backend.database.models import Noticias

Base.metadata.create_all(engine)
print("Banco e tabelas criados com sucesso!")