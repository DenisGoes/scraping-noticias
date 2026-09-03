from backend.gemini.gemini import gerar_roteiro
from backend.bot.telegram import enviar_roteiro

def main():

    print("=" * 70)
    print("GERAÇÃO DO ROTEIRO")
    print("=" * 70)

    roteiro = gerar_roteiro()

    if not roteiro:
        print("❌ Não foi possível gerar o roteiro.")
        return

    print("\nRoteiro gerado com sucesso!\n")

    enviar_roteiro(roteiro)


if __name__ == "__main__":
    main()