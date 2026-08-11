from backend.services.clean_db import clean_dados

if __name__ == "__main___":
    quantidade = clean_dados()

    print(
        f"Limpeza concluída. "
        f"{quantidade} notícia(s) removida(s)"
    )