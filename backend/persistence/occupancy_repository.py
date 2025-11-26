from datetime import datetime, timedelta, date
from typing import List, Optional, Dict, Any
from sqlalchemy import func
from database.models.occupancy import Occupancy


class OccupancyRepository:
    """
    Repository for recording and retrieving parking occupancy events.
    """

    def __init__(self, db):
        self.db = db

    def record_occupancy(
        self, lot_id: int, node_id: int, timestamp: Optional[datetime] = None
    ) -> Occupancy:
        """
        Insert a new occupancy event.

        Args:
            lot_id: ID of the parking lot.
            node_id: node ID in the parking lot.
            timestamp: Optional timestamp. Defaults to `datetime.utcnow()`.

        Returns:
            The persisted Occupancy ORM instance.
        """
        ts = timestamp or datetime.utcnow()
        occ = Occupancy(lot_id=lot_id, node_id=node_id, timestamp=ts)
        self.db.add(occ)
        self.db.commit()
        self.db.refresh(occ)
        return occ

    def _count_between(
        self, start_ts: datetime, end_ts: datetime, lot_id: Optional[int] = None
    ) -> int:
        """
        Returns the count of occupancy events between start_ts and end_ts.

        Args:
            start_ts: Start timestamp (inclusive).
            end_ts: End timestamp (exclusive).
            lot_id: Optional parking lot ID to filter by.

        Returns:
            Count of occupancy events in the specified range.
        """
        q = self.db.query(func.count(Occupancy.id)).filter(
            Occupancy.timestamp >= start_ts, Occupancy.timestamp < end_ts
        )
        if lot_id:
            q = q.filter(Occupancy.lot_id == lot_id)
        count = int(q.scalar() or 0)
        return count

    def get_hourly_for_date(
        self, date_str: str, lot_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Returns a list for hours 00..23 with keys { time: "HH:00", used: N }
        for the given date (YYYY-MM-DD).

        Args:
            date_str: Date string in "YYYY-MM-DD" format.
            lot_id: Optional parking lot ID to filter by.

        Returns:
            A list of dictionaries with hourly occupancy counts.
        """
        start = datetime.fromisoformat(date_str)
        result = []
        for h in range(0, 24):
            s = start + timedelta(hours=h)
            e = s + timedelta(hours=1)
            used = self._count_between(s, e, lot_id)
            result.append({"time": f"{h:02d}:00", "used": used})
        return result

    def get_daily_range(
        self, start_date: str, end_date: str, lot_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Returns a list of daily counts for an inclusive date range.

        Args:
            start_date: Start date string in "YYYY-MM-DD" format.
            end_date: End date string in "YYYY-MM-DD" format.
            lot_id: Optional parking lot ID to filter by.
        """
        s = datetime.fromisoformat(start_date).date()
        e = datetime.fromisoformat(end_date).date()
        if e < s:
            return []

        result = []
        cur = s
        while cur <= e:
            start_ts = datetime.combine(cur, datetime.min.time())
            end_ts = start_ts + timedelta(days=1)
            used = self._count_between(start_ts, end_ts, lot_id)
            result.append({"date": cur.isoformat(), "used": used})
            cur = cur + timedelta(days=1)
        return result

    def get_monthly_range(
        self, start_date: str, end_date: str, lot_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Returns a list of monthly counts for an inclusive date range.
        Each item: { month: "YYYY-MM", used: N }

        Args:
            start_date: Start date string in "YYYY-MM-DD" format.
            end_date: End date string in "YYYY-MM-DD" format.
            lot_id: Optional parking lot ID to filter by.

        Returns:
            A list of dictionaries with monthly occupancy counts.
        """
        start_dt = datetime.fromisoformat(start_date).date().replace(day=1)
        end_dt_raw = datetime.fromisoformat(end_date).date()
        # compute last month's first day
        end_dt = end_dt_raw.replace(day=1)

        def next_month(d: date) -> date:
            if d.month == 12:
                return date(d.year + 1, 1, 1)
            return date(d.year, d.month + 1, 1)

        result = []
        cur = start_dt
        while cur <= end_dt:
            start_ts = datetime.combine(cur, datetime.min.time())
            nm = next_month(cur)
            end_ts = datetime.combine(nm, datetime.min.time())
            used = self._count_between(start_ts, end_ts, lot_id)
            result.append({"month": f"{cur.year:04d}-{cur.month:02d}", "used": used})
            cur = nm
        return result
