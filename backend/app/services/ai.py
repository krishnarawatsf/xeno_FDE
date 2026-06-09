"""AI layer: NL→segment, message generation, campaign recommendations, insights."""

import json
import logging

from openai import OpenAI

from app.config import settings

logger = logging.getLogger(__name__)


def _get_client() -> OpenAI | None:
    if not settings.openai_api_key:
        return None
    return OpenAI(api_key=settings.openai_api_key)


def _fallback_segment(natural_language: str) -> dict:
    nl = natural_language.lower()
    if "high value" in nl or "high spend" in nl:
        return {
            "type": "order_aggregate",
            "min_total_spend": 500,
            "days": 30,
            "description": natural_language,
        }
    if "new" in nl or "recent" in nl:
        return {
            "type": "rules",
            "rules": [{"field": "created_days_ago_lte", "operator": "lte", "value": 30}],
            "description": natural_language,
        }
    return {
        "type": "order_aggregate",
        "min_order_count": 1,
        "days": 90,
        "description": natural_language,
    }


def suggest_segment_from_nl(natural_language: str) -> dict:
    client = _get_client()
    if not client:
        result = _fallback_segment(natural_language)
        result["is_ai_generated"] = False
        result["fallback"] = True
        return result

    prompt = f"""Convert this natural language segment description into a JSON segment definition.

Description: "{natural_language}"

Return ONLY valid JSON with one of these types:
1. "rules" - array of rules on customer fields (name, email, created_days_ago_lte)
2. "order_aggregate" - min_total_spend, min_order_count, days
3. "sql" - a safe SELECT query joining customers and orders tables

Schema:
- customers: id (uuid), name, email, phone, created_at
- orders: id (uuid), customer_id, amount, status, created_at
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        result = json.loads(response.choices[0].message.content)
        result["is_ai_generated"] = True
        return result
    except Exception as e:
        logger.warning("AI segment generation failed: %s", e)
        result = _fallback_segment(natural_language)
        result["is_ai_generated"] = False
        result["fallback"] = True
        return result


def _message_fallback(customer_name: str, goal: str, channel: str) -> dict:
    templates = {
        "email": f"Hi {customer_name}, we have something special for you! {goal}",
        "sms": f"Hey {customer_name}! {goal[:80]}",
        "whatsapp": f"Hi {customer_name} 👋 {goal}",
        "rcs": f"{customer_name}, check this out: {goal}",
    }
    return {
        "message": templates.get(channel, templates["email"]),
        "channel": channel,
        "personalization_notes": "Fallback template",
    }


def generate_message(
    customer_name: str, goal: str, brand_tone: str, channel: str
) -> dict:
    client = _get_client()
    if not client:
        return _message_fallback(customer_name, goal, channel)

    prompt = f"""Write a personalized marketing message.

Customer: {customer_name}
Campaign goal: {goal}
Brand tone: {brand_tone}
Channel: {channel}

Return JSON: {{"message": "...", "personalization_notes": "..."}}
Keep message length appropriate for {channel}.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            response_format={"type": "json_object"},
        )
        result = json.loads(response.choices[0].message.content)
        result["channel"] = channel
        return result
    except Exception as e:
        logger.warning("AI message generation failed: %s", e)
        return _message_fallback(customer_name, goal, channel)


def recommend_campaign(goal: str, audience_size: int = 0) -> dict:
    client = _get_client()
    if not client:
        channels = ["email", "whatsapp"] if audience_size < 1000 else ["email", "sms"]
        return {
            "channel_mix": channels,
            "timing": "Tuesday 10:00 AM local time",
            "rationale": "Email for reach, WhatsApp for engagement on smaller audiences",
            "fallback": True,
        }

    prompt = f"""Recommend a campaign strategy.

Goal: {goal}
Audience size: {audience_size}

Channels available: whatsapp, sms, email, rcs

Return JSON:
{{
  "channel_mix": ["email", "whatsapp"],
  "timing": "best send time recommendation",
  "rationale": "why these channels"
}}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            response_format={"type": "json_object"},
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        logger.warning("AI campaign recommendation failed: %s", e)
        channels = ["email", "whatsapp"] if audience_size < 1000 else ["email", "sms"]
        return {
            "channel_mix": channels,
            "timing": "Tuesday 10:00 AM local time",
            "rationale": "Fallback recommendation",
            "fallback": True,
        }


def generate_insights(funnel: dict, rates: dict) -> list[str]:
    insights = []

    sent = funnel.get("sent", 0)
    if sent == 0:
        return ["No messages sent yet. Launch the campaign to start collecting data."]

    delivery_rate = rates.get("delivery_rate", 0)
    open_rate = rates.get("open_rate", 0)
    click_rate = rates.get("click_rate", 0)
    converted = funnel.get("converted", 0)
    clicked = funnel.get("clicked", 0)

    if delivery_rate < 0.85:
        insights.append(
            f"Delivery rate is {delivery_rate:.0%} — check channel health and contact data quality."
        )
    else:
        insights.append(f"Strong delivery rate at {delivery_rate:.0%}.")

    if open_rate < 0.3:
        insights.append("Open rate is below benchmark. Consider A/B testing subject lines.")
    elif open_rate > 0.5:
        insights.append(f"Excellent open rate ({open_rate:.0%}) — messaging resonates well.")

    if click_rate > 0.2:
        insights.append(f"Click-through rate of {click_rate:.0%} indicates strong CTA performance.")

    if converted > 0 and clicked > 0:
        insights.append(f"Conversion rate from clicks: {converted / clicked:.0%}.")

    client = _get_client()
    if client and sent > 10:
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "user",
                        "content": (
                            f"Given campaign metrics {json.dumps({'funnel': funnel, 'rates': rates})}, "
                            'provide 2 actionable insights. Return JSON: {"insights": ["...", "..."]}'
                        ),
                    }
                ],
                temperature=0.5,
                response_format={"type": "json_object"},
            )
            ai_insights = json.loads(response.choices[0].message.content).get("insights", [])
            insights.extend(ai_insights[:2])
        except Exception:
            pass

    return insights[:5]
