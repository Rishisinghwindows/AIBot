"use client";

import { Star, Moon, Sun, Sparkles } from "lucide-react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface HoroscopeData {
  zodiac_sign?: string;
  sign?: string;
  date?: string;
  period?: string;
  daily_horoscope?: string;
  horoscope?: string;
  lucky_number?: number;
  lucky_color?: string;
  mood?: string;
  compatibility?: string;
  focus_area?: string;
  advice?: string;
}

interface HoroscopeCardProps {
  data: HoroscopeData;
}

const zodiacEmojis: Record<string, string> = {
  aries: "♈",
  taurus: "♉",
  gemini: "♊",
  cancer: "♋",
  leo: "♌",
  virgo: "♍",
  libra: "♎",
  scorpio: "♏",
  sagittarius: "♐",
  capricorn: "♑",
  aquarius: "♒",
  pisces: "♓",
};

const zodiacColors: Record<string, string> = {
  aries: "from-red-500/20 to-orange-500/10",
  taurus: "from-green-500/20 to-emerald-500/10",
  gemini: "from-yellow-500/20 to-amber-500/10",
  cancer: "from-blue-500/20 to-cyan-500/10",
  leo: "from-orange-500/20 to-yellow-500/10",
  virgo: "from-emerald-500/20 to-green-500/10",
  libra: "from-pink-500/20 to-rose-500/10",
  scorpio: "from-purple-500/20 to-violet-500/10",
  sagittarius: "from-indigo-500/20 to-blue-500/10",
  capricorn: "from-muted/50 to-muted/20",
  aquarius: "from-cyan-500/20 to-blue-500/10",
  pisces: "from-violet-500/20 to-purple-500/10",
};

export function HoroscopeCard({ data }: HoroscopeCardProps) {
  const zodiacSign = data.zodiac_sign || data.sign || "Unknown";
  const signLower = zodiacSign.toLowerCase();
  const emoji = zodiacEmojis[signLower] || "⭐";
  const gradient = zodiacColors[signLower] || "from-violet-500/20 to-fuchsia-500/10";
  const horoscopeText = data.daily_horoscope || data.horoscope || "";
  const dateText = data.date || data.period || "Today";

  return (
    <Card className="bg-card border-border overflow-hidden">
      <CardHeader className={`pb-3 bg-gradient-to-r ${gradient} border-b border-border`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="text-4xl">{emoji}</div>
            <div>
              <h3 className="text-lg font-bold text-foreground capitalize">{zodiacSign}</h3>
              <p className="text-sm text-muted-foreground capitalize">{dateText}</p>
            </div>
          </div>
          <Sparkles className="h-6 w-6 text-yellow-400" />
        </div>
      </CardHeader>

      <CardContent className="pt-4 space-y-4">
        {/* Daily Horoscope */}
        <div className="p-3 rounded-lg bg-muted/30 border border-border">
          <div className="flex items-center gap-2 mb-2">
            <Star className="h-4 w-4 text-yellow-400" />
            <span className="text-sm font-medium text-foreground">Today's Reading</span>
          </div>
          <p className="text-sm text-muted-foreground leading-relaxed">{horoscopeText}</p>
        </div>

        {/* Lucky Elements */}
        <div className="grid grid-cols-2 gap-3">
          {data.lucky_number && (
            <div className="p-3 rounded-lg bg-muted/50 border border-border text-center">
              <p className="text-xs text-muted-foreground mb-1">Lucky Number</p>
              <p className="text-2xl font-bold text-primary">{data.lucky_number}</p>
            </div>
          )}
          {data.lucky_color && (
            <div className="p-3 rounded-lg bg-muted/50 border border-border text-center">
              <p className="text-xs text-muted-foreground mb-1">Lucky Color</p>
              <Badge variant="outline" className="bg-muted/50 text-foreground border-border">
                {data.lucky_color}
              </Badge>
            </div>
          )}
        </div>

        {/* Mood, Focus Area & Compatibility */}
        {(data.mood || data.compatibility || data.focus_area) && (
          <div className="flex flex-wrap items-center gap-3 pt-2 border-t border-border">
            {data.mood && (
              <div className="flex items-center gap-2">
                <Moon className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm text-muted-foreground">Mood: <span className="text-foreground capitalize">{data.mood}</span></span>
              </div>
            )}
            {data.focus_area && (
              <div className="flex items-center gap-2">
                <Star className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm text-muted-foreground">Focus: <span className="text-foreground capitalize">{data.focus_area}</span></span>
              </div>
            )}
            {data.compatibility && (
              <div className="flex items-center gap-2">
                <Sun className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm text-muted-foreground">Best match: <span className="text-foreground">{data.compatibility}</span></span>
              </div>
            )}
          </div>
        )}

        {/* Advice */}
        {data.advice && (
          <div className="p-3 rounded-lg bg-primary/10 border border-primary/20">
            <div className="flex items-start gap-2">
              <Sun className="h-4 w-4 text-primary mt-0.5" />
              <p className="text-sm text-foreground/80">{data.advice}</p>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
