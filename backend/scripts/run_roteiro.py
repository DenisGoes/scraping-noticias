from backend.services.gerador_roteiro import (
    buscar_noticias_para_roteiro,
    gerar_roteiro,
    marcar_noticias_como_roteirizadas,
)
from backend.bot.telegram import enviar_roteiro

def main():

    print("=" * 70)
    print("GERAÇÃO DO ROTEIRO")
    print("=" * 70)

    noticias = buscar_noticias_para_roteiro()
    roteiro = gerar_roteiro(noticias)

    if not roteiro:
        print("❌ Não foi possível gerar o roteiro.")
        return

    print("\nRoteiro gerado com sucesso!\n")

    if enviar_roteiro(roteiro):
        marcar_noticias_como_roteirizadas([noticia.id for noticia in noticias])
        print("Notícias marcadas como utilizadas no roteiro.")
    else:
        print("O roteiro não foi marcado; ele poderá ser reenviado na próxima execução.")


if __name__ == "__main__":
    main()
