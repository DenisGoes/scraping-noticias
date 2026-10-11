from sqlalchemy.orm import Mapped, mapped_column
from backend.database.session import Base
from sqlalchemy import Boolean, DateTime, String, Text
from datetime import datetime, UTC

class Noticias(Base):
    __tablename__ = "noticias"

    id: Mapped[int] = mapped_column(primary_key=True)
    titulo: Mapped[str] = mapped_column(String(255), nullable=False)
    fonte: Mapped[str] = mapped_column(String(100), nullable=False)
    data_publicacao: Mapped[str | None] = mapped_column(String(100), nullable=True)
    resumo: Mapped[str | None] = mapped_column(Text, nullable=True)
    link: Mapped[str] = mapped_column(Text, nullable=False, unique=True)

    status: Mapped[str] = mapped_column(
        String(20),
        default="NOVA",
        nullable=False
    )

    coletado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False
    )

    remover_em: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    enviado_telegram: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    telegram_message_id: Mapped[int | None] = mapped_column(nullable=True)
    mensagem: Mapped[str] = mapped_column(Text, nullable=False)
    roteiro_gerado_em: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
