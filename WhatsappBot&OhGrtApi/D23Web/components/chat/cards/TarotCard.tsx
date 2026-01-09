"use client";

import { Sparkles, Star, Moon, Sun, Heart, HelpCircle, RotateCcw } from "lucide-react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

// Single card format
interface SingleTarotCard {
  card_name: string;
  card_type?: "major" | "minor";
  suit?: string;
  meaning_upright?: string;
  meaning_reversed?: string;
  position?: "upright" | "reversed";
  interpretation?: string;
  advice?: string;
}

// Spread card format
interface SpreadCard {
  position: string;
  card: string;
  reversed: boolean;
  meaning: string;
}

// Multi-card spread format
interface TarotSpread {
  spread_type?: string;
  question?: string;
  cards: SpreadCard[];
  interpretation: string;
}

// Backend ToolResult format
interface ToolResult {
  success: boolean;
  data: any;
  error?: string | null;
  tool_name?: string;
}

interface TarotCardProps {
  data: SingleTarotCard | TarotSpread | ToolResult | any;
  topic?: string;
}

// Helper to check if data is a ToolResult
function isToolResult(data: any): data is ToolResult {
  return data && typeof data === 'object' && 'success' in data && 'data' in data;
}

// Normalize the data format
function normalizeTarotData(rawData: any): SingleTarotCard | TarotSpread | null {
  if (!rawData) return null;

  // Handle ToolResult format from backend
  if (isToolResult(rawData)) {
    if (!rawData.success || !rawData.data) return null;
    return rawData.data;
  }

  // Return as-is if it looks like valid tarot data
  if (rawData.card_name || rawData.cards || rawData.spread_type) {
    return rawData;
  }

  return null;
}

const suitIcons: Record<string, React.ReactNode> = {
  cups: <Heart className="h-5 w-5 text-red-400" />,
  wands: <Sparkles className="h-5 w-5 text-orange-400" />,
  swords: <Moon className="h-5 w-5 text-blue-400" />,
  pentacles: <Star className="h-5 w-5 text-yellow-400" />,
};

const positionColors: Record<string, string> = {
  past: "from-blue-500/20 to-cyan-500/10",
  present: "from-violet-500/20 to-purple-500/10",
  future: "from-amber-500/20 to-yellow-500/10",
};

function isSpread(data: SingleTarotCard | TarotSpread): data is TarotSpread {
  return 'cards' in data && Array.isArray(data.cards);
}

export function TarotCard({ data: rawData, topic }: TarotCardProps) {
  // Normalize the data from ToolResult or direct format
  const data = normalizeTarotData(rawData);
  if (!data) return null;

  // Handle multi-card spread
  if (isSpread(data)) {
    return (
      <Card className="bg-gradient-to-br from-zinc-900 to-zinc-950 border-zinc-800 overflow-hidden">
        <CardHeader className="pb-3 bg-gradient-to-r from-violet-500/10 to-purple-500/10 border-b border-zinc-800">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-violet-500 to-fuchsia-500 flex items-center justify-center">
                <Sparkles className="h-5 w-5 text-white" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-white">Tarot Reading</h3>
                <p className="text-sm text-zinc-400 capitalize">
                  {data.spread_type?.replace('_', ' ') || 'Three Card Spread'}
                </p>
              </div>
            </div>
          </div>
        </CardHeader>

        <CardContent className="pt-4 space-y-4">
          {/* Question if provided */}
          {(data.question || topic) && (
            <div className="flex items-center gap-2 text-sm text-zinc-400">
              <HelpCircle className="h-4 w-4" />
              <span>Reading for: <span className="text-white">{data.question || topic}</span></span>
            </div>
          )}

          {/* Cards Grid */}
          <div className="grid grid-cols-3 gap-3">
            {data.cards.map((card, idx) => {
              const posLower = (card.position || "unknown").toLowerCase();
              const gradient = positionColors[posLower] || "from-zinc-500/20 to-zinc-400/10";

              return (
                <div
                  key={idx}
                  className={`p-3 rounded-lg bg-gradient-to-br ${gradient} border border-zinc-700/50`}
                >
                  <div className="text-center">
                    <p className="text-xs text-zinc-500 mb-1">{card.position}</p>
                    <p className="text-sm font-bold text-white mb-1">{card.card}</p>
                    {card.reversed && (
                      <Badge variant="outline" className="text-xs bg-purple-500/20 text-purple-400 border-purple-500/30 mb-1">
                        <RotateCcw className="h-3 w-3 mr-1" />
                        Reversed
                      </Badge>
                    )}
                    <p className="text-xs text-zinc-400 mt-1">{card.meaning}</p>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Interpretation */}
          <div className="p-3 rounded-lg bg-violet-500/10 border border-violet-500/20">
            <div className="flex items-center gap-2 mb-2">
              <Sparkles className="h-4 w-4 text-violet-400" />
              <span className="text-sm font-medium text-violet-300">Interpretation</span>
            </div>
            <p className="text-sm text-zinc-300 leading-relaxed">{data.interpretation}</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Handle single card format
  const singleCard = data as SingleTarotCard;
  const suitLower = (singleCard.suit || "").toLowerCase();
  const gradient = singleCard.suit
    ? (suitLower === 'cups' ? 'from-red-500/20 to-pink-500/10' :
       suitLower === 'wands' ? 'from-orange-500/20 to-amber-500/10' :
       suitLower === 'swords' ? 'from-blue-500/20 to-cyan-500/10' :
       'from-yellow-500/20 to-amber-500/10')
    : 'from-violet-500/20 to-purple-500/10';
  const icon = singleCard.suit ? suitIcons[suitLower] : <Sparkles className="h-5 w-5 text-violet-400" />;

  return (
    <Card className="bg-gradient-to-br from-zinc-900 to-zinc-950 border-zinc-800 overflow-hidden">
      <CardHeader className={`pb-3 bg-gradient-to-r ${gradient} border-b border-zinc-800`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-violet-500 to-fuchsia-500 flex items-center justify-center">
              {icon}
            </div>
            <div>
              <h3 className="text-lg font-bold text-white">{singleCard.card_name}</h3>
              <div className="flex items-center gap-2 mt-1">
                <Badge
                  variant="outline"
                  className={singleCard.position === "upright"
                    ? "bg-green-500/20 text-green-400 border-green-500/30"
                    : "bg-purple-500/20 text-purple-400 border-purple-500/30"
                  }
                >
                  {singleCard.position === "upright" ? "↑ Upright" : "↓ Reversed"}
                </Badge>
                {singleCard.card_type === "major" && (
                  <Badge variant="outline" className="bg-violet-500/20 text-violet-300 border-violet-500/30">
                    Major Arcana
                  </Badge>
                )}
              </div>
            </div>
          </div>
        </div>
      </CardHeader>

      <CardContent className="pt-4 space-y-4">
        {topic && (
          <div className="flex items-center gap-2 text-sm text-zinc-400">
            <HelpCircle className="h-4 w-4" />
            <span>Reading for: <span className="text-white">{topic}</span></span>
          </div>
        )}

        {/* Card Meaning */}
        <div className="p-3 rounded-lg bg-zinc-800/30 border border-zinc-700/50">
          <div className="flex items-center gap-2 mb-2">
            <Star className="h-4 w-4 text-yellow-400" />
            <span className="text-sm font-medium text-zinc-300">
              {singleCard.position === "upright" ? "Upright Meaning" : "Reversed Meaning"}
            </span>
          </div>
          <p className="text-sm text-zinc-400">
            {singleCard.position === "upright" ? singleCard.meaning_upright : singleCard.meaning_reversed}
          </p>
        </div>

        {/* Interpretation */}
        {singleCard.interpretation && (
          <div className="p-3 rounded-lg bg-violet-500/10 border border-violet-500/20">
            <div className="flex items-center gap-2 mb-2">
              <Sparkles className="h-4 w-4 text-violet-400" />
              <span className="text-sm font-medium text-violet-300">Your Interpretation</span>
            </div>
            <p className="text-sm text-zinc-300 leading-relaxed">{singleCard.interpretation}</p>
          </div>
        )}

        {/* Advice */}
        {singleCard.advice && (
          <div className="pt-3 border-t border-zinc-800">
            <div className="flex items-start gap-2">
              <Sun className="h-4 w-4 text-yellow-400 mt-0.5" />
              <div>
                <span className="text-sm font-medium text-zinc-300">Advice: </span>
                <span className="text-sm text-zinc-400">{singleCard.advice}</span>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
