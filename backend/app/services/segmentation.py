"""Rule-based and AI-assisted segmentation engine."""

from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models import Customer, Order


ALLOWED_OPERATORS = {"eq", "gt", "gte", "lt", "lte", "contains", "in"}


def _apply_rule_customers(db: Session, rules: list[dict]) -> list[Customer]:
    """Evaluate simple rule-based filters on customer attributes."""
    if not rules:
        return []

    query = db.query(Customer)
    for rule in rules:
        field = rule.get("field")
        op = rule.get("operator", "eq")
        value = rule.get("value")
        applied = False

        if field == "name" and op == "contains":
            query = query.filter(Customer.name.ilike(f"%{value}%"))
            applied = True
        elif field == "email" and op == "contains":
            query = query.filter(Customer.email.ilike(f"%{value}%"))
            applied = True
        elif field == "created_days_ago_lte" and op == "lte":
            cutoff = datetime.utcnow() - timedelta(days=int(value))
            query = query.filter(Customer.created_at >= cutoff)
            applied = True

        if not applied:
            raise ValueError(f"Unsupported segment rule: field={field}, operator={op}")

    return query.all()


def _apply_sql_segment(db: Session, sql: str) -> list[Customer]:
    """Execute AI-generated read-only SQL against customers/orders."""
    normalized = sql.strip().lower()
    if not normalized.startswith("select"):
        raise ValueError("Only SELECT queries are allowed")

    forbidden = ["insert", "update", "delete", "drop", "alter", "truncate", "grant", "revoke"]
    for word in forbidden:
        if word in normalized:
            raise ValueError(f"Forbidden SQL keyword: {word}")

    result = db.execute(text(sql))
    rows = result.fetchall()
    if not rows:
        return []

    customer_ids = []
    for row in rows:
        row_dict = row._mapping
        if "id" in row_dict:
            customer_ids.append(row_dict["id"])
        elif "customer_id" in row_dict:
            customer_ids.append(row_dict["customer_id"])
        else:
            customer_ids.append(row[0])

    return db.query(Customer).filter(Customer.id.in_(customer_ids)).all()


def _apply_order_aggregate(db: Session, definition: dict) -> list[Customer]:
    """Filter customers by order aggregates (e.g. total spend, order count)."""
    min_total = definition.get("min_total_spend")
    min_orders = definition.get("min_order_count")
    days = definition.get("days", 30)
    cutoff = datetime.utcnow() - timedelta(days=days)

    customers = db.query(Customer).all()
    matched = []

    for customer in customers:
        orders = (
            db.query(Order)
            .filter(Order.customer_id == customer.id, Order.created_at >= cutoff)
            .all()
        )
        total = sum(o.amount for o in orders)
        count = len(orders)

        if min_total is not None and total < min_total:
            continue
        if min_orders is not None and count < min_orders:
            continue
        matched.append(customer)

    return matched


def evaluate_segment(db: Session, definition: dict) -> list[Customer]:
    """Evaluate a segment definition and return matching customers."""
    segment_type = definition.get("type", "rules")

    if segment_type == "rules":
        return _apply_rule_customers(db, definition.get("rules", []))
    if segment_type == "order_aggregate":
        return _apply_order_aggregate(db, definition)
    if segment_type == "sql":
        return _apply_sql_segment(db, definition["sql"])
    if segment_type == "customer_ids":
        ids = [UUID(str(cid)) for cid in definition.get("customer_ids", [])]
        return db.query(Customer).filter(Customer.id.in_(ids)).all()

    raise ValueError(f"Unknown segment type: {segment_type}")


def evaluate_segment_by_id(db: Session, segment_id: UUID) -> list[Customer]:
    from app.models import Segment

    segment = db.query(Segment).filter(Segment.id == segment_id).first()
    if not segment:
        raise ValueError("Segment not found")
    return evaluate_segment(db, segment.definition_json)
