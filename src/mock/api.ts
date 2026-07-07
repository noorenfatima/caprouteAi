// Mock Data for GlobalAssetFlow

export interface RouteNode {
  country: string;
  code: string;
}

export interface CostBreakdown {
  tax: number;
  fx_loss: number;
  compliance_cost: number;
}

export interface RouteResponse {
  id: string;
  route: RouteNode[];
  total_cost: number;
  risk_score: "Low" | "Medium" | "High";
  estimated_time: string;
  breakdown: CostBreakdown;
  asset_type: string;
}

export interface Asset {
  id: string;
  name: string;
  type: "currency" | "gold" | "crypto";
  symbol: string;
}

export const MOCK_ASSETS: Asset[] = [
  { id: "usd", name: "US Dollar", type: "currency", symbol: "USD" },
  { id: "eur", name: "Euro", type: "currency", symbol: "EUR" },
  { id: "inr", name: "Indian Rupee", type: "currency", symbol: "INR" },
  { id: "sgd", name: "Singapore Dollar", type: "currency", symbol: "SGD" },
  { id: "aed", name: "UAE Dirham", type: "currency", symbol: "AED" },
  { id: "gold", name: "Physical Gold", type: "gold", symbol: "XAU" },
  { id: "btc", name: "Bitcoin", type: "crypto", symbol: "BTC" },
  { id: "eth", name: "Ethereum", type: "crypto", symbol: "ETH" },
  { id: "usdc", name: "USD Coin", type: "crypto", symbol: "USDC" },
];

export const MOCK_COUNTRIES = [
  { code: "US", name: "United States" },
  { code: "IN", name: "India" },
  { code: "SG", name: "Singapore" },
  { code: "AE", name: "United Arab Emirates" },
  { code: "GB", name: "United Kingdom" },
  { code: "CH", name: "Switzerland" },
  { code: "JP", name: "Japan" },
];

const generateMockRoute = (source: string, destination: string, assetType: string, optimizationGoal: string): RouteResponse => {
  const isCrypto = assetType === "crypto";
  const isGold = assetType === "gold";
  
  let routePath: RouteNode[] = [
    { country: MOCK_COUNTRIES.find(c => c.code === source)?.name || source, code: source }
  ];

  // Add intermediate nodes based on asset and goal
  if (isCrypto) {
    if (source !== "SG" && destination !== "SG") routePath.push({ country: "Singapore", code: "SG" });
  } else if (isGold) {
    if (source !== "CH" && destination !== "CH") routePath.push({ country: "Switzerland", code: "CH" });
    if (source !== "AE" && destination !== "AE") routePath.push({ country: "United Arab Emirates", code: "AE" });
  } else {
    if (optimizationGoal === "cheapest") {
      if (source !== "SG" && destination !== "SG") routePath.push({ country: "Singapore", code: "SG" });
      if (source !== "AE" && destination !== "AE") routePath.push({ country: "United Arab Emirates", code: "AE" });
    } else if (optimizationGoal === "safest") {
      if (source !== "GB" && destination !== "GB") routePath.push({ country: "United Kingdom", code: "GB" });
    }
  }

  routePath.push({ country: MOCK_COUNTRIES.find(c => c.code === destination)?.name || destination, code: destination });

  // Remove duplicates if source or destination was added as intermediate
  routePath = routePath.filter((node, index, self) => index === self.findIndex((t) => t.code === node.code));

  const baseCost = isCrypto ? 0.5 : isGold ? 2.5 : 1.2;
  const multiplier = optimizationGoal === "fastest" ? 1.5 : optimizationGoal === "safest" ? 1.2 : 1;
  const total_cost = parseFloat((baseCost * multiplier * (1 + Math.random() * 0.5)).toFixed(2));

  return {
    id: Math.random().toString(36).substr(2, 9),
    route: routePath,
    total_cost,
    risk_score: isCrypto ? "Medium" : optimizationGoal === "safest" ? "Low" : "Low",
    estimated_time: isCrypto ? "10 mins" : isGold ? "3-5 Days" : optimizationGoal === "fastest" ? "1 Day" : "2-3 Days",
    breakdown: {
      tax: parseFloat((total_cost * 0.4).toFixed(2)),
      fx_loss: parseFloat((total_cost * 0.35).toFixed(2)),
      compliance_cost: parseFloat((total_cost * 0.25).toFixed(2)),
    },
    asset_type: assetType
  };
};

export const mockOptimizeRoute = async (params: any): Promise<RouteResponse> => {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve(generateMockRoute(params.source, params.destination, params.assetType, params.optimizationGoal));
    }, 2000 + Math.random() * 1000);
  });
};

export const mockCompareRoutes = async (params: any): Promise<RouteResponse[]> => {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve([
        generateMockRoute(params.source, params.destination, params.assetType, "cheapest"),
        generateMockRoute(params.source, params.destination, params.assetType, "fastest"),
        generateMockRoute(params.source, params.destination, params.assetType, "safest"),
      ]);
    }, 1000 + Math.random() * 500);
  });
};

export const mockSimulateScenario = async (params: any): Promise<RouteResponse> => {
  return new Promise((resolve) => {
    setTimeout(() => {
      const route = generateMockRoute(params.source, params.destination, params.assetType, "cheapest");
      // Adjust based on simulation params
      if (params.adjustTax) {
        route.breakdown.tax *= (1 + params.adjustTax / 100);
      }
      if (params.adjustFx) {
        route.breakdown.fx_loss *= (1 + params.adjustFx / 100);
      }
      route.total_cost = parseFloat((route.breakdown.tax + route.breakdown.fx_loss + route.breakdown.compliance_cost).toFixed(2));
      resolve(route);
    }, 900 + Math.random() * 300);
  });
};

export const mockGetInsights = async (): Promise<any> => {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        costDistribution: [
          { name: "Tax", value: 40 },
          { name: "FX Loss", value: 35 },
          { name: "Compliance", value: 25 },
        ],
        topRoutes: [
          { path: "US → SG → IN", volume: "1.2B", avgCost: "1.1%" },
          { path: "GB → AE → IN", volume: "850M", avgCost: "1.4%" },
          { path: "CH → SG → JP", volume: "620M", avgCost: "0.9%" },
        ],
        riskHeatmap: [
          { region: "North America", risk: "Low", score: 15 },
          { region: "Europe", risk: "Low", score: 20 },
          { region: "Asia Pacific", risk: "Medium", score: 45 },
          { region: "Middle East", risk: "Medium", score: 35 },
          { region: "Latin America", risk: "High", score: 75 },
        ]
      });
    }, 700 + Math.random() * 300);
  });
};

export const mockGetAssets = async (): Promise<Asset[]> => {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve(MOCK_ASSETS);
    }, 300);
  });
};
