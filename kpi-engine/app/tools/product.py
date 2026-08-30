from langchain_core.tools import tool
from sqlalchemy import text

from app.tools.database import engine


@tool
def get_product_metrics(start: str, end: str, kpi_key: str = "monthly_revenue"):
    """Get metrics grouped by product for a time window."""

    query = text("""
        SELECT
            COALESCE(dimensions->>'product', 'unknown') AS product,
            SUM(value) AS total_value
        FROM canonical_measurements
        WHERE observed_at >= :start
          AND observed_at <= :end
          AND (
              kpi_id IN (
                  SELECT id FROM kpi_definitions 
                  WHERE kpi_key = :kpi_key OR kpi_key = 'revenue'
              )
              OR :kpi_key IS NULL
          )
        GROUP BY dimensions->>'product'
        ORDER BY total_value DESC
    """)

    try:
        with engine.connect() as conn:
            rows = conn.execute(
                query,
                {
                    "start": start,
                    "end": end,
                    "kpi_key": kpi_key
                }
            ).mappings().all()

        return [dict(row) for row in rows]
    except Exception as e:
        return [{"error": str(e)}]


get_product_revenue = get_product_metrics