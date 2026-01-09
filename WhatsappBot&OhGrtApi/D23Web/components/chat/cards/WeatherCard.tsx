"use client";

import { Cloud, Sun, CloudRain, CloudSnow, Wind, Droplets, Thermometer, MapPin } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";

// Backend ToolResult format
interface ToolResult {
  success: boolean;
  data: {
    location?: string;
    temperature?: string; // "28°C"
    feels_like?: string;  // "30°C"
    humidity?: string;    // "65%"
    description?: string;
    wind_speed?: string;  // "3.5 m/s"
    visibility?: string;
    emoji?: string;
  } | null;
  error?: string | null;
  tool_name?: string;
}

// Direct data format (for backwards compatibility)
interface DirectWeatherData {
  city?: string;
  location?: string;
  temperature: number | string;
  feels_like?: number | string;
  condition?: string;
  description?: string;
  humidity?: number | string;
  wind_speed?: number | string;
  wind_direction?: string;
  uv_index?: number;
  visibility?: number | string;
}

interface WeatherCardProps {
  data: ToolResult | DirectWeatherData;
}

// Helper to parse numeric value from string like "28°C" or "65%"
function parseNumeric(value: string | number | undefined): number | null {
  if (value === undefined || value === null) return null;
  if (typeof value === 'number') return value;
  const match = value.toString().match(/^[\d.]+/);
  return match ? parseFloat(match[0]) : null;
}

// Helper to check if data is a ToolResult
function isToolResult(data: any): data is ToolResult {
  return data && typeof data === 'object' && 'success' in data && 'data' in data;
}

// Normalize the data format
function normalizeWeatherData(rawData: ToolResult | DirectWeatherData) {
  // Handle ToolResult format from backend
  if (isToolResult(rawData)) {
    const inner = rawData.data;
    if (!inner || !rawData.success) return null;
    return {
      location: inner.location || "Unknown",
      temperature: parseNumeric(inner.temperature),
      feels_like: parseNumeric(inner.feels_like),
      condition: inner.description || "Unknown",
      humidity: parseNumeric(inner.humidity),
      wind_speed: inner.wind_speed, // Keep as string for display
      visibility: inner.visibility,
    };
  }

  // Handle direct data format
  const direct = rawData as DirectWeatherData;
  return {
    location: direct.city || direct.location || "Unknown",
    temperature: parseNumeric(direct.temperature),
    feels_like: parseNumeric(direct.feels_like),
    condition: direct.condition || direct.description || "Unknown",
    humidity: parseNumeric(direct.humidity),
    wind_speed: direct.wind_speed,
    visibility: direct.visibility,
  };
}

const weatherIcons: Record<string, React.ReactNode> = {
  clear: <Sun className="h-16 w-16 text-yellow-400" />,
  sunny: <Sun className="h-16 w-16 text-yellow-400" />,
  cloudy: <Cloud className="h-16 w-16 text-zinc-400" />,
  partly: <Cloud className="h-16 w-16 text-zinc-300" />,
  rain: <CloudRain className="h-16 w-16 text-blue-400" />,
  drizzle: <CloudRain className="h-16 w-16 text-blue-300" />,
  snow: <CloudSnow className="h-16 w-16 text-blue-200" />,
  default: <Cloud className="h-16 w-16 text-zinc-400" />,
};

function getWeatherIcon(condition: string | undefined) {
  if (!condition) return weatherIcons.default;
  const lower = condition.toLowerCase();
  for (const [key, icon] of Object.entries(weatherIcons)) {
    if (lower.includes(key)) return icon;
  }
  return weatherIcons.default;
}

function getBackgroundGradient(condition: string | undefined) {
  if (!condition) return "from-violet-500/20 via-fuchsia-500/10 to-transparent";
  const lower = condition.toLowerCase();
  if (lower.includes("sunny") || lower.includes("clear")) {
    return "from-orange-500/20 via-yellow-500/10 to-transparent";
  }
  if (lower.includes("rain") || lower.includes("drizzle")) {
    return "from-blue-500/20 via-blue-400/10 to-transparent";
  }
  if (lower.includes("snow")) {
    return "from-blue-200/20 via-white/10 to-transparent";
  }
  if (lower.includes("cloud")) {
    return "from-zinc-500/20 via-zinc-400/10 to-transparent";
  }
  return "from-violet-500/20 via-fuchsia-500/10 to-transparent";
}

export function WeatherCard({ data: rawData }: WeatherCardProps) {
  if (!rawData) return null;

  // Normalize the data from either ToolResult or direct format
  const data = normalizeWeatherData(rawData);
  if (!data) return null;

  const hasDetailedData = data.humidity !== null || data.wind_speed !== undefined;

  return (
    <Card className="bg-gradient-to-br from-zinc-900 to-zinc-950 border-zinc-800 overflow-hidden">
      <CardContent className="p-0">
        {/* Main Weather Display */}
        <div className={`p-6 bg-gradient-to-br ${getBackgroundGradient(data.condition)}`}>
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center gap-2 text-zinc-400 mb-2">
                <MapPin className="h-4 w-4" />
                <span className="text-sm">{data.location}</span>
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-5xl font-bold text-white">
                  {data.temperature !== null ? Math.round(data.temperature) : '--'}°
                </span>
                <span className="text-zinc-400 text-lg">C</span>
              </div>
              <p className="text-lg text-zinc-300 mt-1 capitalize">{data.condition}</p>
              {data.feels_like !== null && (
                <p className="text-sm text-zinc-500">
                  Feels like {Math.round(data.feels_like)}°C
                </p>
              )}
            </div>
            <div className="flex-shrink-0">
              {getWeatherIcon(data.condition)}
            </div>
          </div>
        </div>

        {/* Weather Details Grid - Only show if we have detailed data */}
        {hasDetailedData && (
          <div className="grid grid-cols-3 gap-4 p-4 border-t border-zinc-800 bg-zinc-900/50">
            {data.humidity !== null && (
              <div className="text-center">
                <Droplets className="h-5 w-5 mx-auto text-blue-400 mb-1" />
                <p className="text-xs text-zinc-500">Humidity</p>
                <p className="text-sm font-medium text-white">{data.humidity}%</p>
              </div>
            )}
            {data.wind_speed !== undefined && (
              <div className="text-center">
                <Wind className="h-5 w-5 mx-auto text-zinc-400 mb-1" />
                <p className="text-xs text-zinc-500">Wind</p>
                <p className="text-sm font-medium text-white">{data.wind_speed}</p>
              </div>
            )}
            {data.visibility !== undefined && (
              <div className="text-center">
                <Thermometer className="h-5 w-5 mx-auto text-orange-400 mb-1" />
                <p className="text-xs text-zinc-500">Visibility</p>
                <p className="text-sm font-medium text-white">{data.visibility}</p>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
