"use client";

import { Hash, Calendar, User, Sparkles, Star, Heart } from "lucide-react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface NumberMeaning {
  trait: string;
  description: string;
}

interface NumerologyData {
  name?: string;
  name_number?: number;
  name_meaning?: NumberMeaning;
  birth_date?: string;
  life_path_number: number;
  life_path_meaning?: NumberMeaning;
  lucky_numbers?: number[];
  // Legacy fields
  expression_number?: number;
  soul_urge_number?: number;
  personality_number?: number;
  interpretation?: string;
  strengths?: string[];
  challenges?: string[];
}

// Backend ToolResult format
interface ToolResult {
  success: boolean;
  data: any;
  error?: string | null;
  tool_name?: string;
}

interface NumerologyCardProps {
  data: NumerologyData | ToolResult | any;
}

// Helper to check if data is a ToolResult
function isToolResult(data: any): data is ToolResult {
  return data && typeof data === 'object' && 'success' in data && 'data' in data;
}

// Normalize the data format
function normalizeNumerologyData(rawData: any): NumerologyData | null {
  if (!rawData) return null;

  // Handle ToolResult format from backend
  if (isToolResult(rawData)) {
    if (!rawData.success || !rawData.data) return null;
    return rawData.data;
  }

  // Return as-is if it looks like valid numerology data
  if (rawData.life_path_number !== undefined || rawData.name_number !== undefined) {
    return rawData;
  }

  return null;
}

const numberMeanings: Record<number, string> = {
  1: "The Leader",
  2: "The Peacemaker",
  3: "The Communicator",
  4: "The Builder",
  5: "The Adventurer",
  6: "The Nurturer",
  7: "The Seeker",
  8: "The Achiever",
  9: "The Humanitarian",
  11: "The Intuitive",
  22: "The Master Builder",
  33: "The Master Teacher",
};

const numberColors: Record<number, string> = {
  1: "from-red-500/20 to-orange-500/10",
  2: "from-blue-500/20 to-cyan-500/10",
  3: "from-yellow-500/20 to-amber-500/10",
  4: "from-green-500/20 to-emerald-500/10",
  5: "from-orange-500/20 to-amber-500/10",
  6: "from-pink-500/20 to-rose-500/10",
  7: "from-purple-500/20 to-violet-500/10",
  8: "from-amber-500/20 to-yellow-500/10",
  9: "from-indigo-500/20 to-blue-500/10",
  11: "from-violet-500/20 to-purple-500/10",
  22: "from-emerald-500/20 to-green-500/10",
  33: "from-fuchsia-500/20 to-pink-500/10",
};

export function NumerologyCard({ data: rawData }: NumerologyCardProps) {
  // Normalize the data from ToolResult or direct format
  const data = normalizeNumerologyData(rawData);
  if (!data) return null;

  const gradient = numberColors[data.life_path_number] || "from-violet-500/20 to-fuchsia-500/10";
  const meaning = data.life_path_meaning?.trait || numberMeanings[data.life_path_number] || "Unique Path";
  const description = data.life_path_meaning?.description || data.interpretation;

  return (
    <Card className="bg-gradient-to-br from-zinc-900 to-zinc-950 border-zinc-800 overflow-hidden">
      <CardHeader className={`pb-3 bg-gradient-to-r ${gradient} border-b border-zinc-800`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-violet-500 to-fuchsia-500 flex items-center justify-center">
              <span className="text-2xl font-bold text-white">{data.life_path_number}</span>
            </div>
            <div>
              <h3 className="text-lg font-bold text-white">Life Path {data.life_path_number}</h3>
              <p className="text-sm text-zinc-400">{meaning}</p>
            </div>
          </div>
          <Hash className="h-6 w-6 text-violet-400" />
        </div>
      </CardHeader>

      <CardContent className="pt-4 space-y-4">
        {/* Personal Info */}
        {(data.name || data.birth_date) && (
          <div className="flex items-center gap-4 text-sm text-zinc-400">
            {data.name && (
              <span className="flex items-center gap-1">
                <User className="h-4 w-4" />
                {data.name}
              </span>
            )}
            {data.birth_date && (
              <span className="flex items-center gap-1">
                <Calendar className="h-4 w-4" />
                {data.birth_date}
              </span>
            )}
          </div>
        )}

        {/* Name Number & Life Path side by side */}
        <div className="grid grid-cols-2 gap-3">
          {data.name_number && (
            <div className="p-3 rounded-lg bg-zinc-800/50 border border-zinc-700/50">
              <p className="text-xs text-zinc-500 mb-1">Name Number</p>
              <div className="flex items-center gap-2">
                <span className="text-2xl font-bold text-violet-400">{data.name_number}</span>
                {data.name_meaning && (
                  <span className="text-sm text-zinc-400">{data.name_meaning.trait}</span>
                )}
              </div>
              {data.name_meaning?.description && (
                <p className="text-xs text-zinc-500 mt-1">{data.name_meaning.description}</p>
              )}
            </div>
          )}

          {/* Legacy number fields */}
          {data.expression_number && (
            <div className="p-2 rounded-lg bg-zinc-800/50 border border-zinc-700/50 text-center">
              <p className="text-xs text-zinc-500">Expression</p>
              <p className="text-xl font-bold text-violet-400">{data.expression_number}</p>
            </div>
          )}
          {data.soul_urge_number && (
            <div className="p-2 rounded-lg bg-zinc-800/50 border border-zinc-700/50 text-center">
              <p className="text-xs text-zinc-500">Soul Urge</p>
              <p className="text-xl font-bold text-pink-400">{data.soul_urge_number}</p>
            </div>
          )}
          {data.personality_number && (
            <div className="p-2 rounded-lg bg-zinc-800/50 border border-zinc-700/50 text-center">
              <p className="text-xs text-zinc-500">Personality</p>
              <p className="text-xl font-bold text-blue-400">{data.personality_number}</p>
            </div>
          )}
        </div>

        {/* Life Path Meaning / Interpretation */}
        {description && (
          <div className="p-3 rounded-lg bg-zinc-800/30 border border-zinc-700/50">
            <div className="flex items-center gap-2 mb-2">
              <Sparkles className="h-4 w-4 text-yellow-400" />
              <span className="text-sm font-medium text-zinc-300">Your Life Path</span>
            </div>
            <p className="text-sm text-zinc-400 leading-relaxed">{description}</p>
          </div>
        )}

        {/* Lucky Numbers */}
        {data.lucky_numbers && data.lucky_numbers.length > 0 && (
          <div className="p-3 rounded-lg bg-violet-500/10 border border-violet-500/20">
            <div className="flex items-center gap-2 mb-2">
              <Star className="h-4 w-4 text-violet-400" />
              <span className="text-sm font-medium text-violet-300">Lucky Numbers</span>
            </div>
            <div className="flex gap-2">
              {data.lucky_numbers.map((num, i) => (
                <Badge key={i} variant="outline" className="bg-zinc-800/50 text-white border-zinc-600">
                  {num}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {/* Strengths & Challenges (Legacy) */}
        {(data.strengths?.length || data.challenges?.length) && (
          <div className="grid grid-cols-2 gap-3">
            {data.strengths && data.strengths.length > 0 && (
              <div className="p-3 rounded-lg bg-green-500/10 border border-green-500/20">
                <div className="flex items-center gap-1 mb-2">
                  <Star className="h-4 w-4 text-green-400" />
                  <span className="text-xs font-medium text-green-400">Strengths</span>
                </div>
                <ul className="text-xs text-zinc-400 space-y-1">
                  {data.strengths.slice(0, 3).map((s, i) => (
                    <li key={i}>• {s}</li>
                  ))}
                </ul>
              </div>
            )}
            {data.challenges && data.challenges.length > 0 && (
              <div className="p-3 rounded-lg bg-orange-500/10 border border-orange-500/20">
                <div className="flex items-center gap-1 mb-2">
                  <Heart className="h-4 w-4 text-orange-400" />
                  <span className="text-xs font-medium text-orange-400">Growth Areas</span>
                </div>
                <ul className="text-xs text-zinc-400 space-y-1">
                  {data.challenges.slice(0, 3).map((c, i) => (
                    <li key={i}>• {c}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
