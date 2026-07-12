import json
import math
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
from enum import Enum

from backend.ml_decision_engine import MLDecisionEngine
from backend.route_generator import ConfigRouteGenerator

# ============================================
# DATA MODELS
# ============================================

class Purpose(Enum):
    EXPORT = "EXPORT"
    SERVICE = "SERVICE"
    INVESTMENT = "INVESTMENT"
    SALARY = "SALARY"
    ROYALTY = "ROYALTY"

class BusinessSize(Enum):
    SMALL = "SMALL"
    LARGE = "LARGE"

class Priority(Enum):
    COST = "COST"
    TIME = "TIME"
    BALANCED = "BALANCED"

class CurrencyHandling(Enum):
    CONVERT = "CONVERT"
    HOLD = "HOLD"

@dataclass
class Route:
    path: List[str]
    total_cost_usd: float
    total_time_hrs: float
    compliance_score: float  # 0-100, higher = more compliant
    breakdown: Dict[str, Any]
    
    def __repr__(self):
        return f"Route(path={' → '.join(self.path)}, cost=${self.total_cost_usd:.2f}, time={self.total_time_hrs:.1f}h, compliance={self.compliance_score:.1f}/100)"


# ============================================
# CORE ROUTING ENGINE
# ============================================

class GlobalCapitalRouter:
    def __init__(self, json_config_path: str):
        with open(json_config_path, 'r') as f:
            self.config = json.load(f)

        if 'base_origins' not in self.config:
            raise KeyError("Missing 'base_origins' in configuration")

        self.base_origins = {k.upper(): v for k, v in self.config['base_origins'].items()}
        self.global_constants = self.config.get('global_constants', {})

        # Load ML Friction Scorer through the Phase 1 decision-engine wrapper.
        self.ml_scorer = MLDecisionEngine("friction_model.pkl")

        # Build source-specific destination lookup for fast routing
        self.source_to_destination_zone = {}
        for origin_name, origin_data in self.base_origins.items():
            destination_zones = origin_data.get('destination_zones', {})
            for zone_name, zone_data in destination_zones.items():
                for country in zone_data.get('countries', []):
                    self.source_to_destination_zone.setdefault(origin_name, {})[country.upper()] = {
                        'zone': zone_name,
                        'logic': zone_data.get('logic', {})
                    }

        # Add self zone defaults for same-country, including India origin
        for origin in self.base_origins.keys():
            self.source_to_destination_zone.setdefault(origin, {})[origin] = {
                'zone': 'ORIGIN',
                'logic': {
                    'withholding_tax_dividends': 0.0,
                    'withholding_tax_interest': 0.0,
                    'compliance_latency_hrs': 0,
                    'landing_fee_range_usd': [0, 0],
                    'avg_correspondent_hops': 0
                }
            }

        self.route_generator = ConfigRouteGenerator(self.source_to_destination_zone)
    
    def get_zone_config(self, source: str, dest: str) -> Dict:
        """Get zone logic for a given destination based on source origin"""
        source_upper = source.upper()
        dest_upper = dest.upper()

        if source_upper not in self.source_to_destination_zone:
            raise ValueError(f"Source country '{source}' has no configured destination zones")

        zone_entry = self.source_to_destination_zone[source_upper].get(dest_upper)
        if not zone_entry:
            raise ValueError(f"Destination country '{dest}' not found under source '{source}' zones")

        return zone_entry['logic']
    
    def calculate_route_cost(self, amount_usd: float, source: str, dest: str, 
                             purpose: str, business_size: str, currency_handling: str) -> Dict:
        """Calculate total cost, time, compliance for a direct route"""
        
        src = source.upper()
        source_zone = self.get_zone_config(source, dest)
        dest_zone = source_zone

        origin_info = self.base_origins.get(src, {})
        asset_config = origin_info.get('asset_specific_coefficients', {}).get('NORMAL_TRANSFER', {})

        # 1. Withholding Tax (based on purpose)
        if purpose in ["INVESTMENT", "FDI_INVESTMENT", "STOCK_MARKET"]:
            tax_rate = dest_zone.get('withholding_tax_dividends', 0.10)
        elif purpose in ["ROYALTY", "SERVICE"]:
            tax_rate = dest_zone.get('withholding_tax_interest', 0.10)
        else:
            tax_rate = 0.05  # default for export/salary
        
        withholding_tax = amount_usd * tax_rate
        
        # 2. Additional local tax (for high-compliance zones)
        additional_tax = amount_usd * dest_zone.get('additional_local_tax_pct', 0.0)
        
        # 3. FX Spread (depends on business size)
        if business_size == "LARGE":
            fx_spread_rate = asset_config.get('fx_spread_fintech', 0.006)
        else:
            fx_spread_rate = asset_config.get('fx_spread_retail_bank', 0.035)
        
        fx_cost = amount_usd * fx_spread_rate
        
        # 4. Landing fees
        landing_fee_range = dest_zone.get('landing_fee_range_usd', [10, 30])
        landing_fee = (landing_fee_range[0] + landing_fee_range[1]) / 2  # average
        
        # 5. Compliance/Reporting fees
        reporting_fee = 0
        if purpose == "INVESTMENT":
            reporting_fee = asset_config.get('reporting_fee_inr', 2500) / 83  # approx INR to USD
        elif dest_zone.get('mandatory_purpose_code_validation', False):
            reporting_fee = 50  # extra compliance fee
        
        # 6. ISO 20022 + SWIFT GPI (if currency handling = CONVERT)
        iso_fee = self.config['global_constants']['iso_20022_compliance_fee']
        swift_fee = self.config['global_constants']['swift_gpi_tracking_premium'] if currency_handling == "CONVERT" else 0
        
        # 7. Intermediary bank fees (based on correspondent hops)
        correspondent_fee = dest_zone.get('avg_correspondent_hops', 1) * 25
        
        # Total cost
        total_cost = (withholding_tax + additional_tax + fx_cost + landing_fee + 
                      reporting_fee + iso_fee + swift_fee + correspondent_fee)
        
        # Time calculation
        compliance_latency = dest_zone.get('compliance_latency_hrs', 24)
        settlement_time = 2 if currency_handling == "CONVERT" else 5  # days to hours
        total_time_hrs = compliance_latency + (settlement_time * 24)
        
        # Compliance score (0-100, higher = better)
        src_upper = source.upper()
        dest_upper = dest.upper()
        zone_name = self.source_to_destination_zone[src_upper][dest_upper]['zone']
        ml_decision = self.ml_scorer.predict_compliance(
            withholding_tax_rate=tax_rate,
            additional_local_tax=dest_zone.get('additional_local_tax_pct', 0.0),
            correspondent_hops=dest_zone.get('avg_correspondent_hops', 1),
            compliance_latency_hrs=dest_zone.get('compliance_latency_hrs', 24),
            landing_fee_avg=landing_fee,
            fx_spread=fx_spread_rate,
            purpose=purpose,
            amount_usd=amount_usd,
            zone_name=zone_name,
            is_mandatory_validation=dest_zone.get('mandatory_purpose_code_validation', False),
            business_size=business_size,
            zone_logic=dest_zone,
        )
        compliance_score = ml_decision.compliance_score
        
        return {
            'total_cost_usd': total_cost,
            'total_time_hrs': total_time_hrs,
            'compliance_score': compliance_score,
            'breakdown': {
                'withholding_tax_usd': withholding_tax,
                'additional_local_tax_usd': additional_tax,
                'fx_cost_usd': fx_cost,
                'landing_fee_usd': landing_fee,
                'reporting_fee_usd': reporting_fee,
                'iso_swift_fees_usd': iso_fee + swift_fee,
                'correspondent_fees_usd': correspondent_fee
            }
        }
    
    def find_best_route(self, amount_usd: float, source: str, dest: str,
                        purpose: str, business_size: str, currency_handling: str,
                        priority: str) -> Tuple[Route, Route, Route]:
        """
        Returns: (least_cost_route, fastest_route, most_compliant_route)
        
        Candidate corridors are generated from capital_routing_config.json.
        Ranking behavior remains the same: least cost, fastest, most compliant.
        """
        
        candidate_routes = []

        for candidate in self.route_generator.generate(source, dest):
            hop_costs = [
                self.calculate_route_cost(
                    amount_usd,
                    hop.source,
                    hop.destination,
                    purpose,
                    business_size,
                    currency_handling,
                )
                for hop in candidate.hops
            ]

            if len(hop_costs) == 1:
                breakdown = hop_costs[0]['breakdown']
            else:
                breakdown = {
                    f"hop{index + 1}": hop_cost['breakdown']
                    for index, hop_cost in enumerate(hop_costs)
                }

            candidate_routes.append(Route(
                path=candidate.path,
                total_cost_usd=sum(hop_cost['total_cost_usd'] for hop_cost in hop_costs),
                total_time_hrs=sum(hop_cost['total_time_hrs'] for hop_cost in hop_costs),
                compliance_score=sum(hop_cost['compliance_score'] for hop_cost in hop_costs) / len(hop_costs),
                breakdown=breakdown
            ))
        
        # Find best by each metric
        least_cost = min(candidate_routes, key=lambda r: r.total_cost_usd)
        fastest = min(candidate_routes, key=lambda r: r.total_time_hrs)
        most_compliant = max(candidate_routes, key=lambda r: r.compliance_score)
        
        return least_cost, fastest, most_compliant
    
    def generate_insights(self, amount_usd: float, source: str, dest: str,
                          purpose: str, business_size: str, priority: str,
                          currency_handling: str):
        """Generate detailed comparison insights"""
        
        least_cost, fastest, most_compliant = self.find_best_route(
            amount_usd, source, dest, purpose, business_size, currency_handling, priority
        )
        
        print("\n" + "="*80)
        print("🌍 GLOBAL CAPITAL ROUTING ANALYSIS")
        print("="*80)
        print(f"📊 Input Summary:")
        print(f"   • Amount: ${amount_usd:,.2f}")
        print(f"   • Source: {source}")
        print(f"   • Destination: {dest}")
        print(f"   • Purpose: {purpose}")
        print(f"   • Business Size: {business_size}")
        print(f"   • Priority: {priority}")
        print(f"   • Currency Handling: {currency_handling}")
        
        print("\n" + "-"*80)
        print("🚀 THREE OPTIMAL ROUTES")
        print("-"*80)
        
        print(f"\n💰 LEAST COST ROUTE: {' → '.join(least_cost.path)}")
        print(f"   • Total Cost: ${least_cost.total_cost_usd:,.2f}")
        print(f"   • Total Time: {least_cost.total_time_hrs:.1f} hours ({least_cost.total_time_hrs/24:.1f} days)")
        print(f"   • Compliance Score: {least_cost.compliance_score:.1f}/100")
        
        print(f"\n⚡ FASTEST ROUTE: {' → '.join(fastest.path)}")
        print(f"   • Total Cost: ${fastest.total_cost_usd:,.2f}")
        print(f"   • Total Time: {fastest.total_time_hrs:.1f} hours ({fastest.total_time_hrs/24:.1f} days)")
        print(f"   • Compliance Score: {fastest.compliance_score:.1f}/100")
        
        print(f"\n✅ MOST COMPLIANT ROUTE: {' → '.join(most_compliant.path)}")
        print(f"   • Total Cost: ${most_compliant.total_cost_usd:,.2f}")
        print(f"   • Total Time: {most_compliant.total_time_hrs:.1f} hours ({most_compliant.total_time_hrs/24:.1f} days)")
        print(f"   • Compliance Score: {most_compliant.compliance_score:.1f}/100")
        
        print("\n" + "-"*80)
        print("📈 DETAILED COMPARISON & INSIGHTS")
        print("-"*80)
        
        # 1. Cost difference analysis
        cost_savings = least_cost.total_cost_usd - fastest.total_cost_usd
        cost_savings_pct_vs_fastest = abs(cost_savings) / fastest.total_cost_usd * 100 if fastest.total_cost_usd else 0
        cost_savings_vs_compliant = least_cost.total_cost_usd - most_compliant.total_cost_usd
        cost_savings_pct_vs_compliant = abs(cost_savings_vs_compliant) / most_compliant.total_cost_usd * 100 if most_compliant.total_cost_usd else 0

        if cost_savings > 0:
            print(f"\n💡 Cost vs Speed Trade-off:")
            print(f"   → Fastest route costs ${cost_savings:,.2f} MORE than least-cost route")
            print(f"   → Least-cost route is {cost_savings_pct_vs_fastest:.1f}% cheaper than fastest")
            print(f"   → But fastest route saves {fastest.total_time_hrs - least_cost.total_time_hrs:.1f} hours")
            print(f"   → Hourly cost of speed: ${cost_savings / (fastest.total_time_hrs - least_cost.total_time_hrs):.2f}/hour")
        else:
            print(f"\n💡 Cost vs Speed Trade-off:")
            print(f"   → Fastest route is actually {abs(cost_savings_pct_vs_fastest):.1f}% cheaper than least-cost")

        # 2. Compliance vs Cost
        compliance_premium = most_compliant.total_cost_usd - least_cost.total_cost_usd
        if compliance_premium > 0:
            print(f"\n🛡️ Compliance vs Cost Trade-off:")
            print(f"   → Most compliant route costs ${compliance_premium:,.2f} MORE than least-cost")
            print(f"   → Least-cost route is {cost_savings_pct_vs_compliant:.1f}% cheaper than most compliant")
            print(f"   → But offers {most_compliant.compliance_score - least_cost.compliance_score:.1f} points higher compliance score")
        else:
            print(f"\n🛡️ Compliance vs Cost Trade-off:")
            print(f"   → Most compliant route is actually {abs(cost_savings_pct_vs_compliant):.1f}% cheaper than least-cost")
            print(f"   → Compliance score gain: {most_compliant.compliance_score - least_cost.compliance_score:.1f} points")
        
        # 3. Priority-based recommendation
        print(f"\n🎯 RECOMMENDATION BASED ON YOUR PRIORITY ('{priority}'):")
        if priority == "COST":
            savings_vs_fastest = fastest.total_cost_usd - least_cost.total_cost_usd
            savings_vs_compliant = most_compliant.total_cost_usd - least_cost.total_cost_usd
            pct_vs_fastest = savings_vs_fastest / fastest.total_cost_usd * 100 if fastest.total_cost_usd else 0
            pct_vs_compliant = savings_vs_compliant / most_compliant.total_cost_usd * 100 if most_compliant.total_cost_usd else 0

            print(f"   → Choose LEAST COST ROUTE: {' → '.join(least_cost.path)}")
            print(f"   → You save ${savings_vs_fastest:,.2f} ({pct_vs_fastest:.1f}%) vs fastest")
            print(f"   → You save ${savings_vs_compliant:,.2f} ({pct_vs_compliant:.1f}%) vs most compliant")
        elif priority == "TIME":
            print(f"   → Choose FASTEST ROUTE: {' → '.join(fastest.path)}")
            print(f"   → Saves {fastest.total_time_hrs - least_cost.total_time_hrs:.1f}h vs least cost")
        elif priority == "BALANCED":
            # Find middle ground
            balanced_route = least_cost if least_cost.compliance_score > 70 else fastest
            print(f"   → Consider {balanced_route.path} (balanced cost & compliance)")
        
        # 4. Hidden cost breakdown for best route
        best = least_cost if priority == "COST" else (fastest if priority == "TIME" else most_compliant)
        print(f"\n🔍 HIDDEN COST BREAKDOWN FOR YOUR RECOMMENDED ROUTE:")
        if 'hop1' in best.breakdown:
            print(f"   Hop 1 ({best.path[0]} → {best.path[1]}):")
            for k, v in best.breakdown['hop1'].items():
                if v > 0:
                    print(f"      - {k.replace('_', ' ').title()}: ${v:.2f}")
        else:
            for k, v in best.breakdown.items():
                if v > 0:
                    print(f"   - {k.replace('_', ' ').title()}: ${v:.2f}")
        
        # 5. Strategic insight
        print(f"\n💎 STRATEGIC INSIGHT:")
        if 'UAE' in best.path or 'SINGAPORE' in best.path:
            print(f"   → Routing through a low-friction hub (UAE/Singapore) reduces cost/time")
            print(f"   → This is legal under most tax treaties when structured properly")
        elif most_compliant.compliance_score > 85:
            print(f"   → Direct routing offers highest compliance but at premium cost")
            print(f"   → Consider if your priority is audit-readiness")
        
        print("\n" + "="*80)
        print("⚠️ DISCLAIMER: This is for informational purposes. Consult tax professionals.")
        print("="*80)


# ============================================
# MAIN EXECUTION
# ============================================

if __name__ == "__main__":
    # Example user inputs
    router = GlobalCapitalRouter("capital_routing_config.json")  # Your JSON file path
    
    # Simulate user inputs
    user_inputs = {
        "amount_usd": 100000,
        "source_country": "INDIA",
        "destination_country": "USA",
        "purpose_of_transfer": "INVESTMENT",
        "business_size": "LARGE",
        "priority": "COST",
        "currency_handling": "CONVERT"
    }

    router.generate_insights(
        amount_usd=user_inputs['amount_usd'],
        source=user_inputs['source_country'],
        dest=user_inputs['destination_country'],
        purpose=user_inputs['purpose_of_transfer'],
        business_size=user_inputs['business_size'],
        currency_handling=user_inputs['currency_handling'],
        priority=user_inputs['priority']
    )
