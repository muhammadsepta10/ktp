from sqlalchemy import Integer, String, Text, SmallInteger, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class KtpOcr(Base):
    __tablename__ = "ktp_ocr"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ktp_img: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    raw_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    nik: Mapped[str] = mapped_column(String(20), nullable=False, default="")
    province: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    birthdate: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    virgin: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    status: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    birthplace: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    city: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    sub_district: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    village: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    address: Mapped[str] = mapped_column(Text, nullable=False, default="")
    rt: Mapped[str] = mapped_column(String(10), nullable=False, default="")
    rw: Mapped[str] = mapped_column(String(10), nullable=False, default="")
    religion: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    job: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    citizenship: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    valid_until: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    rating: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    is_valid: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_changed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[str] = mapped_column(DateTime, nullable=False, default=func.now())
