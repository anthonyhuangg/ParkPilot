from database.setup import Base
from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    func,
)


class CarbonSaving(Base):
    __tablename__ = "carbon_savings"

    id = Column(Integer, primary_key=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    lot_id = Column(
        Integer,
        ForeignKey("parking_lots.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    route_length_saved_m = Column(Float, nullable=False)
    co2_saved_g = Column(Float, nullable=False)
    money_saved_usd = Column(Float, nullable=False)
    date_time = Column(DateTime(timezone=True), server_default=func.now())
