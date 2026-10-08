import json
from pathlib import Path
from urllib.parse import quote_plus
from PIL import Image
from ..config import settings

PLATFORM_BASES = {
    "Amazon": "https://www.amazon.in/s?k=",
    "Flipkart": "https://www.flipkart.com/search?q=",
    "IKEA": "https://www.ikea.com/in/en/search/?q=",
    "Swiggy": "https://www.swiggy.com/search?query=",
    "Zomato": "https://www.zomato.com/search?query=",
    "OYO": "https://www.oyorooms.com/search?location=",
}

def search_url(platform: str, query: str) -> str:
    base = PLATFORM_BASES.get(platform, "https://www.google.com/search?q=")
    return base + quote_plus(query)

def fallback(kind, data):
    budget = float(data["budget"])
    if kind == "home":
        raw = [("LED lighting set", "Amazon", .10), ("Ceiling fan", "Amazon", .15), ("Storage/side table", "IKEA", .20), ("Wall decor", "Flipkart", .10), ("Rug or soft furnishing", "IKEA", .15)]
        title = f"Budget-friendly {data['room_type']} plan"
        summary = f"Prioritizes {data['style']} style while keeping a safety buffer."
        allocation = {"furniture": round(budget*.45), "lighting": round(budget*.20), "decor": round(budget*.20), "buffer": round(budget*.15)}
    elif kind == "party":
        raw = [("Catering package", "Zomato", .40), ("Decoration package", "Amazon", .15), ("Venue/accommodation search", "OYO", .25), ("Dessert/snacks", "Swiggy", .10)]
        title = f"{data['event_type']} plan for {data['guests']} guests"
        summary = "Food and venue are prioritized before optional spending."
        allocation = {"food": round(budget*.40), "venue": round(budget*.25), "decoration": round(budget*.15), "entertainment": round(budget*.10), "buffer": round(budget*.10)}
    else:
        raw = [("Statement necklace", "Amazon", .25), ("Matching earrings", "Flipkart", .20), ("Bracelet/bangle", "Amazon", .15), ("Minimal ring", "Flipkart", .10)]
        title = f"{data['occasion']} jewelry shortlist"
        summary = f"Balances {data['style']} styling with a generous budget buffer."
        allocation = {"necklace": round(budget*.25), "earrings": round(budget*.20), "bracelet": round(budget*.15), "ring": round(budget*.10), "buffer": round(budget*.40)}

    items = [{"name": n, "platform": p, "estimated_price": round(budget*x), "why": "Good starting point for a budget-conscious search.", "search_url": search_url(p, n)} for n, p, x in raw]
    return {
        "title": title, "summary": summary, "budget": budget,
        "estimated_total": sum(x["estimated_price"] for x in items),
        "allocation": allocation, "recommendations": items,
        "tips": ["Compare at least two listings before buying.", "Check delivery, reviews, return policy and taxes.", "Keep the buffer for unexpected costs."],
        "source": "demo",
    }

def _clean_result(result, kind, data):
    if not isinstance(result, dict):
        raise ValueError("AI response is not an object")
    budget = float(data["budget"])
    recommendations = result.get("recommendations") or []
    cleaned = []
    for item in recommendations:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", "Recommendation")).strip()[:120]
        platform = str(item.get("platform", "Amazon")).strip()
        if platform not in PLATFORM_BASES:
            platform = "Amazon"
        try:
            price = max(0, float(item.get("estimated_price", 0)))
        except (TypeError, ValueError):
            price = 0
        cleaned.append({
            "name": name,
            "platform": platform,
            "estimated_price": price,
            "why": str(item.get("why", "Budget-aware option."))[:500],
            "search_url": search_url(platform, name),
        })
    if not cleaned:
        raise ValueError("AI response contains no recommendations")

    total = sum(x["estimated_price"] for x in cleaned)
    if total > budget and total > 0:
        scale = budget / total * 0.90
        for x in cleaned:
            x["estimated_price"] = round(x["estimated_price"] * scale)
        total = sum(x["estimated_price"] for x in cleaned)

    allocation = result.get("allocation")
    if not isinstance(allocation, dict):
        allocation = {"planned spending": round(total), "buffer": max(0, round(budget-total))}
    else:
        allocation = {str(k): max(0, round(float(v))) for k, v in allocation.items() if isinstance(v, (int, float))}

    return {
        "title": str(result.get("title", f"{kind.title()} recommendations"))[:160],
        "summary": str(result.get("summary", "Budget-aware recommendations generated for your request."))[:1000],
        "budget": budget,
        "estimated_total": round(total),
        "allocation": allocation,
        "recommendations": cleaned,
        "tips": [str(x) for x in (result.get("tips") or [])][:6] or ["Compare listings before buying.", "Check reviews, delivery and return policies."],
        "source": "gemini",
    }

def generate(kind, data, image_path=None):
    if settings.DEMO_MODE or not settings.GEMINI_API_KEY:
        return fallback(kind, data)
    try:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        prompt = (
            "You are PocketSmart AI. Create a practical INR budget recommendation. "
            "Never claim live inventory or exact current prices. Return ONLY JSON with "
            "title, summary, budget, estimated_total, allocation, recommendations, tips. "
            "Each recommendation must contain name, platform, estimated_price and why. "
            "Use only these platforms where relevant: Amazon, Flipkart, IKEA, Swiggy, Zomato, OYO. "
            "Keep estimated_total <= budget. User input: " + json.dumps(data)
        )
        contents = [prompt]
        if image_path:
            contents.append(Image.open(Path(image_path)))
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.4,
                max_output_tokens=1800,
            ),
        )
        return _clean_result(json.loads(response.text), kind, data)
    except Exception:
        # The application must remain usable even when the API key, model,
        # quota, network, or AI response is unavailable.
        return fallback(kind, data)
