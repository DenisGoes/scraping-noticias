import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from sqlalchemy import select

from backend.database.session import Session
from backend.database.models import Noticias

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY não encontrada.")

client = genai.Client(api_key=api_key)

# print("Modelos disponíveis:")

# for model in client.models.list():
#     print(model.name)

def buscar_todas_noticias():

     with Session() as session:
        try:
            noticias = session.scalars(select(Noticias)).all()

            return noticias

        except Exception as e:
            print(f"Erro ao buscar notícias: {e}")
            return []

def gerar_roteiro():
    noticias = buscar_todas_noticias()

    if not noticias:
        print("Nenhuma notícia encontrada.")
        exit()

    print(f"{len(noticias)} notícia(s) encontrada(s).")

    dados_noticias = ""

    for noticia in noticias:
        dados_noticias += f"""
            Título: {noticia.titulo}

            Fonte: {noticia.fonte}

            Data de publicação: {noticia.data_publicacao}

            Resumo:
            {noticia.resumo}

            Link:
            {noticia.link}

            --------------------------------------------------
        """


    prompt = f"""
        Você é um jornalista especializado em tecnologia e também roteirista
        de podcasts.

        A seguir estão várias notícias de tecnologia coletadas de diferentes
        fontes.

        Sua tarefa é analisar todas as notícias e criar um roteiro para um
        podcast diário de tecnologia, apresentado por duas pessoas.

        OBJETIVOS:

        1. Identificar os assuntos mais relevantes do conjunto de notícias.
        2. Agrupar notícias que tratam do mesmo assunto.
        3. Eliminar informações repetidas.
        4. Criar um resumo geral dos acontecimentos mais importantes.
        5. Criar uma conversa natural entre duas pessoas sobre esses assuntos.
        6. Fazer com que a conversa seja informativa, mas fácil de entender.
        7. Priorizar notícias relevantes para desenvolvedores, profissionais
        de tecnologia e pessoas interessadas em tecnologia.

        REGRAS:

        - Escreva tudo em português do Brasil.
        - Não invente informações.
        - Utilize somente as informações presentes nas notícias fornecidas.
        - Não crie fatos, números, empresas ou declarações que não estejam
        presentes nas informações fornecidas.
        - Caso uma informação não esteja disponível, não tente adivinhar.
        - Não dê opiniões políticas ou pessoais.
        - Evite linguagem excessivamente técnica.
        - Explique brevemente termos técnicos quando forem importantes
        para entender a notícia.
        - Não mencione todas as notícias obrigatoriamente.
        - Priorize os assuntos mais relevantes.
        - Notícias semelhantes devem ser agrupadas.
        - O roteiro deve parecer uma conversa natural entre duas pessoas.
        - Evite transformar o roteiro em uma simples leitura de notícias.
        - As duas pessoas devem interagir, comentar e fazer perguntas entre si.
        - Evite conversas artificiais ou repetitivas.
        - O roteiro deve ser adequado para posteriormente ser enviado ao
        NotebookLM para geração de áudio.

        LIMITES DE TAMANHO:

        - O RESUMO GERAL deve ter no máximo 800 caracteres.
        - O ROTEIRO deve ter no máximo 8.000 caracteres.
        - As FONTES devem ser listadas de forma curta e objetiva.
        - Evite repetir informações entre o resumo e o roteiro.
        - Priorize qualidade e relevância em vez de quantidade.
        - Se houver muitas notícias, selecione apenas os assuntos mais
        importantes para permanecer dentro dos limites.
        - Nunca ultrapasse os limites de caracteres definidos acima.

        ESTRUTURA DA RESPOSTA:

        1. TÍTULO DO EPISÓDIO

        Crie um título curto e interessante para o episódio.

        2. RESUMO GERAL

        Faça um resumo dos principais acontecimentos tecnológicos
        presentes nas notícias.

        Limite máximo: 800 caracteres.

        3. ROTEIRO

        Crie uma conversa entre:

        APRESENTADOR 1
        APRESENTADOR 2

        A conversa deve possuir:

        - Introdução
        - Apresentação dos principais assuntos
        - Explicações
        - Interações entre os apresentadores
        - Transições naturais entre os assuntos
        - Encerramento

        Limite máximo: 8.000 caracteres.

        4. FONTES

        Ao final, liste as fontes utilizadas no roteiro.

        Para cada fonte informe:

        - Título
        - Fonte
        - Link

        Mantenha essa seção curta e objetiva.

        NOTÍCIAS:

        {dados_noticias}
    """


    print("Enviando notícias para o Gemini...")

    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=[prompt],
        config=types.GenerateContentConfig(
            temperature=0.3,
        ),
    )


    if not response.text:
        print("O Gemini não retornou nenhum conteúdo.")
        return None

    return response.text