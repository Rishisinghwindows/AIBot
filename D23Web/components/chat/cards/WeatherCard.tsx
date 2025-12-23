"use client";

import { Cloud, Sun, CloudRain, CloudSnow, Droplets, MapPin } from "lucide-react";

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

function getWeatherIcon(condition: string) {
  const lower = condition.toLowerCase();

  if (lower.includes("clear") || lower.includes("sunny")) {
    return <Sun className="h-12 w-12 text-yellow-400" />;
  }
  if (lower.includes("rain") || lower.includes("drizzle")) {
    return <CloudRain className="h-12 w-12 text-blue-400" />;
  }
  if (lower.includes("snow")) {
    return <CloudSnow className="h-12 w-12 text-blue-200" />;
  }
  if (lower.includes("cloud") || lower.includes("overcast")) {
    return <Cloud className="h-12 w-12 text-gray-400" />;
  }
  if (lower.includes("smoke") || lower.includes("haze") || lower.includes("mist") || lower.includes("fog")) {
    return <Cloud className="h-12 w-12 text-gray-500" />;
  }

  return <Cloud className="h-12 w-12 text-gray-400" />;
}

export function WeatherCard({ data }: WeatherCardProps) {
  const locationName = data.city || data.location || "Unknown";

  return (
    <div className="w-full max-w-[280px]">
      {/* Main Weather Card */}
      <div className="rounded-2xl bg-gradient-to-br from-[#2a1f4e] via-[#1e1a3a] to-[#151226] border border-purple-500/30 p-5 shadow-lg">
        {/* Location */}
        <div className="flex items-center gap-2 text-purple-300/80 mb-3">
          <MapPin className="h-4 w-4" />
          <span className="text-sm font-medium">{locationName}</span>
        </div>

        {/* Temperature and Icon Row */}
        <div className="flex items-center justify-between">
          <div className="flex items-baseline">
            <span className="text-6xl font-bold text-white tracking-tight">
              {Math.round(data.temperature)}°
            </span>
            <span className="text-gray-400 text-lg ml-1">C</span>
          </div>
          <div className="flex-shrink-0">
            {getWeatherIcon(data.condition)}
          </div>
        </div>

        {/* Condition */}
        <p className="text-white/90 text-lg mt-2 capitalize">{data.condition}</p>

        {/* Humidity Row */}
        {data.humidity !== undefined && (
          <div className="mt-4 pt-4 border-t border-purple-500/20">
            <div className="flex items-center gap-2">
              <Droplets className="h-5 w-5 text-blue-400" />
              <div>
                <p className="text-purple-300/60 text-xs">Humidity</p>
                <p className="text-white font-semibold">{data.humidity}%</p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Secondary Info Card */}
      <div className="mt-3 rounded-xl bg-[#1a1530]/80 border border-purple-500/20 p-4">
        <p className="text-purple-300/60 text-sm mb-2">Weather in {locationName}</p>
        <div className="space-y-1.5 text-sm">
          <p className="text-white/90 flex items-center gap-2">
            <span className="text-base">🌡️</span>
            Temperature: {data.temperature.toFixed(2)}°C
          </p>
          <p className="text-white/90 flex items-center gap-2">
            <span className="text-base">💧</span>
            Humidity: {data.humidity !== undefined ? `${data.humidity.toFixed(1)}%` : "N/A"}
          </p>
          <p className="text-white/90">
            Condition: {data.condition}
          </p>
        </div>
      </div>
    </div>
  );
}
