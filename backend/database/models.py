from sqlalchemy.orm import Mapped, mapped_column
from backend.database.session import Base
from sqlalchemy import DateTime, String
from datetime import datetime, UTC

class Noticias(Base):
    __tablename__ = "noticias"

    id: Mapped[int] = mapped_column(primary_key=True)
    titulo: Mapped[str] = mapped_column(String(255), nullable=False)
    fonte: Mapped[str] = mapped_column(String(100), nullable=False)
    data_publicacao: Mapped[str] = mapped_column(nullable=False)
    link: Mapped[str] = mapped_column(nullable=False, unique=True)

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

    enviado_telegram: Mapped[bool] = mapped_column(default=False)
    telegram_message_id: Mapped[int] = mapped_column(nullable=True)
    mensagem: Mapped[str] = mapped_column(nullable=False)
    