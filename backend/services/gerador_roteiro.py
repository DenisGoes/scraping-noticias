import os
from datetime import UTC, datetime, timedelta
from dotenv import load_dotenv
from google import genai
from google.genai import types
from sqlalchemy import select

from backend.database.session import Session
from backend.database.models import Noticias

load_dotenv()

LIMITE_NOTICIAS_ROTEIRO = 30
JANELA_NOTICIAS_ROTEIRO = timedelta(days=2)


def buscar_noticias_para_roteiro():
    """Retorna notícias recentes ainda não usadas em um roteiro."""
    coletadas_desde = datetime.now(UTC) - JANELA_NOTICIAS_ROTEIRO
    with Session() as session:
        noticias = session.scalars(
            select(Noticias)
            .where(
                Noticias.roteiro_gerado_em.is_(None),
                Noticias.status.in_(("APLICADA", "SALVA")),
                Noticias.coletado_em >= coletadas_desde,
            )
            .order_by(Noticias.coletado_em.desc(), Noticias.id.desc())
            .limit(LIMITE_NOTICIAS_ROTEIRO)
        ).all()
        return list(reversed(noticias))


def marcar_noticias_como_roteirizadas(ids):
    if not ids:
        return
    with Session() as session:
        try:
            noticias = session.scalars(
                select(Noticias).where(Noticias.id.in_(ids))
            ).all()
            agora = datetime.now(UTC)
            for noticia in noticias:
                noticia.roteiro_gerado_em = agora
            session.commit()
        except Exception:
            session.rollback()
            raise


def gerar_roteiro(noticias=None):
    noticias = noticias if noticias is not None else buscar_noticias_para_roteiro()
    if not noticias:
        print("Nenhuma notícia pendente para gerar roteiro.")
        return None

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY não configurada.")

    client = genai.Client(api_key=api_key)

    print(f"{len(noticias)} notícia(s) encontrada(s).")

    dados_noticias = ""

    for noticia in noticias:
        resumo = (noticia.resumo or "não informado").strip()
        if len(resumo) > 1200:
            resumo = resumo[:1197].rstrip() + "..."

        dados_noticias += f"""Título: {noticia.titulo}
Fonte: {noticia.fonte}
Data de publicação: {noticia.data_publicacao or "não informada"}
Resumo: {resumo}
Link: {noticia.link}
---
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
        model=os.getenv("GEMINI_MODEL", "gemini-3.5-flash"),
        contents=[prompt],
        config=types.GenerateContentConfig(
            temperature=0.3,
        ),
    )


    if not response.text:
        print("O Gemini não retornou nenhum conteúdo.")
        return None

    return response.text
