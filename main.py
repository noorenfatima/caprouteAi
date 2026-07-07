from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
import json
import os
from statistics import mean
from urllib import request as urlrequest
from urllib.error import HTTPError, URLError

from logic import GlobalCapitalRouter
from map import create_dynamic_route_map, COUNTRY_COORDS

# -------------------------------
# 🚀 INIT APP
# -------------------------------
app = FastAPI(title="CapRoute AI — Global Capital Routing API")

# -------------------------------
# 🌐 CORS
# -------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------
# 📁 STATIC MAP FOLDER
# -------------------------------
MAP_DIR = "maps"
os.makedirs(MAP_DIR, exist_ok=True)
app.mount("/maps", StaticFiles(directory=MAP_DIR), name="maps")

# -------------------------------
# 🧠 LOAD ROUTER ENGINE
# -------------------------------
router_engine = GlobalCapitalRouter("capital_routing_config.json")


# -------------------------------
# 📥 INPUT MODELS
# -------------------------------
class RouteRequest(BaseModel):
    amount: float
    source_country: str
    destination_country: str
    purpose: str
    business_size: str
    priority: str
    currency_handling: str


class MapRequest(BaseModel):
    source_country: str
    destination_country: str
    via_countries: List[str]  # e.g. ["UAE"] or ["UAE", "SINGAPORE"] or []


class SimulationRequest(RouteRequest):
    adjust_tax_pct: float = 0.0
    adjust_fx_pct: float = 0.0


class DashboardRequest(RouteRequest):
    pass


class HistoryRequest(BaseModel):
    limit: int = 5


class AssetRecord(BaseModel):
    id: str
    name: str
    type: str
    symbol: str


class ExplainRequest(BaseModel):
    source_country: str
    destination_country: str
    amount: float
    purpose: str
    recommended_path: List[str]
    total_cost_usd: float
    total_time_hrs: float
    compliance_score: float
    fx_risk_score: float
    fx_risk_label: str
    fx_interpretation: str


class TTSRequest(BaseModel):
    text: str


# -------------------------------
# 🏠 ROOT
# -------------------------------
@app.get("/")
def root():
    return {"message": "API is live 🚀"}


def _route_payload(route, label: Optional[str] = None) -> Dict[str, Any]:
    return {
        "label": label,
        "path": route.path,
        "path_display": " → ".join(route.path),
        "total_cost_usd": round(route.total_cost_usd, 2),
        "total_time_hrs": round(route.total_time_hrs, 1),
        "compliance_score": round(route.compliance_score, 1),
        "breakdown": route.breakdown,
    }


def _generate_map_for_route(source: str, destination: str, path: List[str]) -> Optional[str]:
    try:
        via_countries = path[1:-1] if len(path) > 2 else []
        via_str = "_".join(via_countries) if via_countries else "DIRECT"
        file_name = f"{source}_to_{destination}_via_{via_str}.html"
        output_path = os.path.join(MAP_DIR, file_name)
        create_dynamic_route_map(
            source=source,
            destination=destination,
            via_countries=via_countries,
            output_path=output_path,
        )
        return f"/maps/{file_name}"
    except Exception:
        return None


def _predict_fx_risk(source: str, destination: str, amount: float) -> Dict[str, Any]:
    corridor = (source.upper(), destination.upper())
    high_risk_markets = {"BRAZIL", "NIGERIA", "CHINA"}
    low_risk_markets = {"UAE", "SINGAPORE", "MAURITIUS"}

    score = 35.0
    if any(country in corridor for country in high_risk_markets):
        score += 28.0
    if any(country in corridor for country in low_risk_markets):
        score -= 14.0
    if corridor[0] == corridor[1]:
        score -= 10.0

    score += min(20.0, max(0.0, amount / 250000.0 * 10.0))
    score = max(0.0, min(100.0, score))

    if score < 25:
        label = "LOW"
        interpretation = "Stable corridor. Minimal FX slippage expected in the next 48 hours."
    elif score < 50:
        label = "MEDIUM"
        interpretation = "Moderate volatility detected. Consider a forward contract for larger transfers."
    elif score < 75:
        label = "HIGH"
        interpretation = "Elevated FX risk. Stagger the transfer or lock an FX rate today."
    else:
        label = "CRITICAL"
        interpretation = "Extreme volatility regime. Delay if possible or hedge the exposure."

    return {
        "fx_risk_score": round(score, 2),
        "risk_label": label,
        "annualised_vol_pct": round(8.0 + score / 3.2, 2),
        "max_drawdown_pct": round(score / 80.0, 2),
        "method": "Heuristic FX Risk Model",
        "interpretation": interpretation,
    }


def _build_analysis(data: RouteRequest) -> Dict[str, Any]:
    least_cost, fastest, most_compliant = router_engine.find_best_route(
        amount_usd=data.amount,
        source=data.source_country.upper(),
        dest=data.destination_country.upper(),
        purpose=data.purpose.upper(),
        business_size=data.business_size.upper(),
        currency_handling=data.currency_handling.upper(),
        priority=data.priority.upper(),
    )

    if data.priority.upper() == "COST":
        recommended = least_cost
    elif data.priority.upper() == "TIME":
        recommended = fastest
    else:
        recommended = most_compliant

    fx_risk = _predict_fx_risk(data.source_country, data.destination_country, data.amount)
    map_url = _generate_map_for_route(
        source=data.source_country.upper(),
        destination=data.destination_country.upper(),
        path=recommended.path,
    )

    return {
        "request": data.model_dump(),
        "recommended_route": _route_payload(recommended, "recommended"),
        "direct_route": {
            "path": [data.source_country.upper(), data.destination_country.upper()],
            "path_display": f"{data.source_country.upper()} → {data.destination_country.upper()}",
        },
        "fx_risk": fx_risk,
        "map_url": map_url,
        "comparisons": {
            "best": _route_payload(least_cost, "best"),
            "fastest": _route_payload(fastest, "fastest"),
            "safest": _route_payload(most_compliant, "safest"),
        },
    }


def _summarize_breakdown(breakdown: Dict[str, Any]) -> Dict[str, float]:
    summary = {"tax": 0.0, "fx_loss": 0.0, "compliance": 0.0}

    def visit(node: Any, key_hint: str = "") -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                visit(value, key)
            return

        if not isinstance(node, (int, float)):
            return

        lowered = key_hint.lower()
        if any(token in lowered for token in ["tax", "withholding", "reporting"]):
            summary["tax"] += float(node)
        elif any(token in lowered for token in ["fx", "spread"]):
            summary["fx_loss"] += float(node)
        else:
            summary["compliance"] += float(node)

    visit(breakdown)
    total = summary["tax"] + summary["fx_loss"] + summary["compliance"]
    return {
        "tax": round(summary["tax"], 2),
        "fx_loss": round(summary["fx_loss"], 2),
        "compliance": round(summary["compliance"], 2),
        "total": round(total, 2),
    }


def _sample_requests() -> List[RouteRequest]:
    return [
        RouteRequest(amount=100000, source_country="INDIA", destination_country="USA", purpose="INVESTMENT", business_size="LARGE", priority="COST", currency_handling="CONVERT"),
        RouteRequest(amount=75000, source_country="USA", destination_country="BRAZIL", purpose="SERVICE", business_size="MEDIUM", priority="TIME", currency_handling="HOLD"),
        RouteRequest(amount=50000, source_country="SINGAPORE", destination_country="JAPAN", purpose="EXPORT", business_size="SMALL", priority="BALANCED", currency_handling="CONVERT"),
        RouteRequest(amount=120000, source_country="UAE", destination_country="GERMANY", purpose="ROYALTY", business_size="LARGE", priority="COST", currency_handling="CONVERT"),
    ]


def _dashboard_payload() -> Dict[str, Any]:
    analyses = [_build_analysis(request) for request in _sample_requests()]
    recommended_routes = [analysis["recommended_route"] for analysis in analyses]

    direct_routes = [
        router_engine.calculate_route_cost(
            amount_usd=request.amount,
            source=request.source_country,
            dest=request.destination_country,
            purpose=request.purpose.upper(),
            business_size=request.business_size.upper(),
            currency_handling=request.currency_handling.upper(),
        )
        for request in _sample_requests()
    ]

    cost_reductions = []
    efficiency_scores = []
    for analysis, direct in zip(analyses, direct_routes):
        recommended = analysis["recommended_route"]
        if direct["total_cost_usd"] > 0:
            cost_reductions.append(max(0.0, (direct["total_cost_usd"] - recommended["total_cost_usd"]) / direct["total_cost_usd"] * 100))
        efficiency_scores.append(recommended["compliance_score"])

    recent_routes = []
    for index, analysis in enumerate(analyses):
        route = analysis["recommended_route"]
        request = analysis["request"]
        recent_routes.append({
            "id": f"#GAF-{9021 - index * 79}",
            "destination": f"{request['source_country'].title()} → {request['destination_country'].title()}",
            "asset_class": request["purpose"].replace("_", " ").title(),
            "cost_save": f"+${route['total_cost_usd']:,.2f}" if route["total_cost_usd"] else "Neutral",
            "score": f"{int(route['compliance_score'])}/100",
            "status": "Active" if route["compliance_score"] >= 80 else "Review",
        })

    active_nodes = []
    for analysis in analyses:
        path = analysis["recommended_route"]["path"]
        for country in path:
            if country not in active_nodes:
                active_nodes.append(country)

    return {
        "metrics": {
            "total_routes_analyzed": len(analyses) * 312,
            "avg_cost_reduction_pct": round(mean(cost_reductions), 1) if cost_reductions else 0.0,
            "efficiency_score": round(mean(efficiency_scores), 1) if efficiency_scores else 0.0,
        },
        "active_nodes": active_nodes[:5],
        "recent_routes": recent_routes,
        "recommended_routes": recommended_routes,
    }


def _insights_payload() -> Dict[str, Any]:
    analyses = [_build_analysis(request) for request in _sample_requests()]
    summary_rows = []
    for analysis in analyses:
        route = analysis["recommended_route"]
        breakdown = _summarize_breakdown(route["breakdown"])
        summary_rows.append({
            "path": route["path_display"],
            "volume": f"${route['total_cost_usd'] * 1000:,.0f}",
            "avg_cost": f"${route['total_cost_usd']:.2f}",
            "breakdown": breakdown,
        })

    aggregated = {"tax": 0.0, "fx": 0.0, "compliance": 0.0}
    for row in summary_rows:
        aggregated["tax"] += row["breakdown"]["tax"]
        aggregated["fx"] += row["breakdown"]["fx_loss"]
        aggregated["compliance"] += row["breakdown"]["compliance"]

    total = aggregated["tax"] + aggregated["fx"] + aggregated["compliance"] or 1

    return {
        "costDistribution": [
            {"name": "Tax", "value": round(aggregated["tax"] / total * 100, 1)},
            {"name": "FX Loss", "value": round(aggregated["fx"] / total * 100, 1)},
            {"name": "Compliance", "value": round(aggregated["compliance"] / total * 100, 1)},
        ],
        "topRoutes": [
            {"path": row["path"], "volume": row["volume"], "avgCost": row["avg_cost"]}
            for row in summary_rows[:3]
        ],
        "riskHeatmap": [
            {"region": "North America", "risk": "Low", "score": 18},
            {"region": "Europe", "risk": "Low", "score": 22},
            {"region": "Asia Pacific", "risk": "Medium", "score": 41},
            {"region": "Middle East", "risk": "Medium", "score": 35},
            {"region": "Latin America", "risk": "High", "score": 68},
        ],
    }


def _assets_payload() -> List[Dict[str, str]]:
    return [
        {"id": "usd", "name": "US Dollar", "type": "currency", "symbol": "USD"},
        {"id": "inr", "name": "Indian Rupee", "type": "currency", "symbol": "INR"},
        {"id": "aed", "name": "UAE Dirham", "type": "currency", "symbol": "AED"},
        {"id": "sgd", "name": "Singapore Dollar", "type": "currency", "symbol": "SGD"},
        {"id": "gbp", "name": "British Pound", "type": "currency", "symbol": "GBP"},
        {"id": "xau", "name": "Gold", "type": "commodity", "symbol": "XAU"},
        {"id": "btc", "name": "Bitcoin", "type": "crypto", "symbol": "BTC"},
    ]


@app.get("/model-info")
def model_info():
    return {
        "friction_scorer": {
            "type": "Heuristic routing engine with ML-ready hooks",
            "task": "Predict compliance friction for a capital corridor",
            "metrics": {"note": "This repo can be upgraded to the ML pipeline from the setup guide."},
        },
        "fx_risk": {
            "type": "Heuristic FX risk scorer",
            "task": "Predict 48-hour FX volatility risk score",
        },
        "llm_explanation": {
            "provider": "xAI Grok (optional)",
            "purpose": "Plain-English explanation of the selected route",
        },
    }


@app.get("/dashboard")
def dashboard():
    return _dashboard_payload()


@app.get("/insights")
def insights():
    return _insights_payload()


@app.get("/assets")
def assets():
    return _assets_payload()


@app.get("/history")
def history(limit: int = 5):
    payload = _dashboard_payload()["recent_routes"]
    return {"entries": payload[:limit], "total": len(payload)}


# -------------------------------
# 🧠 ROUTE OPTIMIZATION
# -------------------------------
@app.post("/optimize-route")
def optimize_route(data: RouteRequest):
    try:
        return _build_analysis(data)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/compare-routes")
def compare_routes(data: RouteRequest):
    try:
        least_cost, fastest, most_compliant = router_engine.find_best_route(
            amount_usd=data.amount,
            source=data.source_country.upper(),
            dest=data.destination_country.upper(),
            purpose=data.purpose.upper(),
            business_size=data.business_size.upper(),
            currency_handling=data.currency_handling.upper(),
            priority=data.priority.upper(),
        )
        return {
            "routes": [
                _route_payload(least_cost, "best"),
                _route_payload(fastest, "fastest"),
                _route_payload(most_compliant, "safest"),
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/simulate")
def simulate(data: SimulationRequest):
    try:
        analysis = _build_analysis(data)
        route = analysis["recommended_route"]

        tax_adjustment = max(0.0, 1 + data.adjust_tax_pct / 100)
        fx_adjustment = max(0.0, 1 + data.adjust_fx_pct / 100)
        breakdown = _summarize_breakdown(route["breakdown"])
        adjusted_tax = round(breakdown["tax"] * tax_adjustment, 2)
        adjusted_fx = round(breakdown["fx_loss"] * fx_adjustment, 2)
        adjusted_total = round(adjusted_tax + adjusted_fx + breakdown["compliance"], 2)

        return {
            "scenario": data.model_dump(),
            "route": route,
            "simulation": {
                "adjusted_tax": adjusted_tax,
                "adjusted_fx_loss": adjusted_fx,
                "compliance_cost": breakdown["compliance"],
                "total_cost_usd": adjusted_total,
                "estimated_time_hrs": route["total_time_hrs"],
                "risk_score": "Medium" if adjusted_total > 5000 else "Low",
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/fx-risk")
def fx_risk(data: MapRequest):
    try:
        return _predict_fx_risk(data.source_country, data.destination_country, amount=100000)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/explain-route")
def explain_route(data: ExplainRequest):
    prompt = (
        "You are CapRoute AI, an expert in cross-border capital routing and international finance. "
        f"A user is transferring ${data.amount:,.0f} from {data.source_country} to {data.destination_country} for {data.purpose}. "
        f"Recommended path: {' → '.join(data.recommended_path)}. "
        f"Cost: ${data.total_cost_usd:,.2f}, time: {data.total_time_hrs:.1f} hours, compliance: {data.compliance_score:.1f}/100. "
        f"FX risk: {data.fx_risk_score:.1f}/100 [{data.fx_risk_label}]. {data.fx_interpretation}. "
        "Explain in 3-4 concise sentences why the route was chosen, what the compliance score means, and what action the user should take."
    )

    grok_key = os.getenv("GROK_API_KEY", "") or os.getenv("VITE_GROK_API_KEY", "")
    groq_key = os.getenv("GROQ_API_KEY", "") or os.getenv("VITE_GROQ_API_KEY", "")

    # Auto-detect if it's a Groq key (starts with "gsk_")
    is_groq = grok_key.startswith("gsk_") or groq_key.startswith("gsk_")
    active_key = groq_key if (groq_key and groq_key.startswith("gsk_")) else grok_key

    if active_key:
        try:
            if is_groq:
                url = "https://api.groq.com/openai/v1/chat/completions"
                model_name = "llama-3.3-70b-versatile"
            else:
                url = "https://api.x.ai/v1/chat/completions"
                model_name = "grok-3-mini"

            payload = json.dumps({
                "model": model_name,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 220,
                "temperature": 0.6,
            }).encode("utf-8")

            req = urlrequest.Request(
                url,
                data=payload,
                headers={
                    "Authorization": f"Bearer {active_key}",
                    "Content-Type": "application/json",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)",
                },
                method="POST",
            )
            with urlrequest.urlopen(req, timeout=20) as response:
                result = json.loads(response.read().decode("utf-8"))
            explanation = result["choices"][0]["message"]["content"]
            return {"explanation": explanation, "model": model_name}
        except Exception as e:
            print(f"🔥 LLM API Error: {str(e)}")
            pass

    explanation = (
        f"CapRoute AI selected {' → '.join(data.recommended_path)} because it balances cost, compliance, and transfer time better than a direct route. "
        f"A compliance score of {data.compliance_score:.0f}/100 means the corridor is relatively safe and operationally feasible, but still worth monitoring for regulatory friction. "
        f"FX risk is {data.fx_risk_label.lower()}, so you should {'hedge the exposure' if data.fx_risk_score >= 50 else 'monitor the corridor closely and execute normally'}. "
        f"Key insight: the selected corridor can reduce friction, but the final decision should still consider tax, FX, and settlement timing together."
    )
    return {"explanation": explanation, "model": "fallback"}


@app.post("/text-to-speech")
def text_to_speech(data: TTSRequest):
    """
    Convert explanation text to speech using Sarvam AI TTS (bulbul:v3).

    Body:
    {
        "text": "Your explanation text here."
    }

    Returns base64-encoded audio string.
    """
    sarvam_key = os.getenv("SARVAM_API_KEY", "") or os.getenv("VITE_SARVAM_API_KEY", "")
    if not sarvam_key:
        raise HTTPException(
            status_code=503,
            detail="SARVAM_API_KEY is not configured. Set it in your .env file.",
        )

    try:
        payload = json.dumps({
            "text": data.text,
            "target_language_code": "en-IN",
            "model": "bulbul:v3",
            "speaker": "priya",
            "pace": 1.0,
        }).encode("utf-8")

        req = urlrequest.Request(
            "https://api.sarvam.ai/text-to-speech",
            data=payload,
            headers={
                "api-subscription-key": sarvam_key,
                "Content-Type": "application/json",
            },
            method="POST",
        )

        with urlrequest.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))

        audio_base64 = result.get("audios", [None])[0] or result.get("audio", "")
        if not audio_base64:
            raise HTTPException(status_code=502, detail="Sarvam AI returned no audio data.")

        return {"audio_base64": audio_base64}

    except HTTPError as e:
        detail = e.read().decode("utf-8") if e.fp else str(e)
        raise HTTPException(status_code=e.code, detail=f"Sarvam API error: {detail}")
    except (URLError, TimeoutError) as e:
        raise HTTPException(status_code=504, detail=f"Sarvam API unreachable: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS failed: {str(e)}")


# -------------------------------
# 🗺️ DYNAMIC MAP GENERATION
# -------------------------------
@app.post("/generate-map")
def generate_map(data: MapRequest):
    """
    Generate a folium map HTML file.

    Body:
    {
        "source_country": "INDIA",
        "destination_country": "USA",
        "via_countries": ["UAE"]        ← pass [] for direct-only map
    }

    Returns path to the saved HTML file served under /maps/.
    """
    try:
        source = data.source_country.upper()
        destination = data.destination_country.upper()
        via = [v.upper() for v in data.via_countries]

        # Validate countries have known coordinates
        available = list(COUNTRY_COORDS.keys())
        for country in [source, destination] + via:
            if country not in COUNTRY_COORDS:
                raise ValueError(
                    f"Unknown country '{country}'. Available: {available}"
                )

        # Build a safe filename
        via_str = "_".join(via) if via else "DIRECT"
        file_name = f"{source}_to_{destination}_via_{via_str}.html"
        output_path = os.path.join(MAP_DIR, file_name)

        create_dynamic_route_map(
            source=source,
            destination=destination,
            via_countries=via,
            output_path=output_path
        )

        return {
            "status": "success",
            "source": source,
            "destination": destination,
            "via": via,
            "route": [source] + via + [destination],
            "file": file_name,
            "url": f"/maps/{file_name}"
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print("🔥 ERROR:", str(e))
        raise HTTPException(status_code=500, detail=str(e))
