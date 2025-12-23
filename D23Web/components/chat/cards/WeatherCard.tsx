"use client";

import { Cloud, Sun, CloudRain, CloudSnow, Wind, Droplets, Thermometer, MapPin } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";

interface WeatherData {
  city?: string;
  location?: string;
  temperature: number;
  feels_like?: number;
  condition: string;
  humidity?: number;
  wind_speed?: number;
  wind_direction?: string;
  uv_index?: number;
  visibility?: number;
}

interface WeatherCardProps {
  data: WeatherData;
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

function getWeatherIcon(condition: string) {
  const lower = condition.toLowerCase();
  for (const [key, icon] of Object.entries(weatherIcons)) {
    if (lower.includes(key)) return icon;
  }
  return weatherIcons.default;
}

function getBackgroundGradient(condition: string) {
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

export function WeatherCard({ data }: WeatherCardProps) {
  const locationName = data.city || data.location || "Unknown";
  const hasDetailedData = data.humidity !== undefined || data.wind_speed !== undefined;

  return (
    <Card className="bg-gradient-to-br from-zinc-900 to-zinc-950 border-zinc-800 overflow-hidden">
      <CardContent className="p-0">
        {/* Main Weather Display */}
        <div className={`p-6 bg-gradient-to-br ${getBackgroundGradient(data.condition)}`}>
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center gap-2 text-zinc-400 mb-2">
                <MapPin className="h-4 w-4" />
                <span className="text-sm">{locationName}</span>
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-5xl font-bold text-white">{Math.round(data.temperature)}°</span>
                <span className="text-zinc-400 text-lg">C</span>
              </div>
              <p className="text-lg text-zinc-300 mt-1 capitalize">{data.condition}</p>
              {data.feels_like !== undefined && (
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
            {data.humidity !== undefined && (
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
                <p className="text-sm font-medium text-white">
                  {data.wind_speed} km/h
                  {data.wind_direction && <span className="text-zinc-500 text-xs ml-1">{data.wind_direction}</span>}
                </p>
              </div>
            )}
            {data.uv_index !== undefined && (
              <div className="text-center">
                <Thermometer className="h-5 w-5 mx-auto text-orange-400 mb-1" />
                <p className="text-xs text-zinc-500">UV Index</p>
                <p className="text-sm font-medium text-white">{data.uv_index}</p>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
