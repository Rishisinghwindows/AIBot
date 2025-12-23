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

interface TarotCardProps {
  data: SingleTarotCard | TarotSpread;
  topic?: string;
}

const suitIcons: Record<string, React.ReactNode> = {
  cups: <Heart className="h-5 w-5 text-red-400" />,
  wands: <Sparkles className="h-5 w-5 text-orange-400" />,
  swords: <Moon className="h-5 w-5 text-blue-400" />,
  pentacles: <Star className="h-5 w-5 text-yellow-400" />,
};

const positionColors: Record<string, string> = {
  past: "from-blue-500/20 to-cyan-500/10",
  present: "from-primary/20 to-primary/10",
  future: "from-amber-500/20 to-yellow-500/10",
};

function isSpread(data: SingleTarotCard | TarotSpread): data is TarotSpread {
  return 'cards' in data && Array.isArray(data.cards);
}

export function TarotCard({ data, topic }: TarotCardProps) {
  // Handle multi-card spread
  if (isSpread(data)) {
    return (
      <Card className="bg-card border-border overflow-hidden">
        <CardHeader className="pb-3 bg-gradient-to-r from-primary/10 to-primary/5 border-b border-border">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-primary to-primary/70 flex items-center justify-center">
                <Sparkles className="h-5 w-5 text-primary-foreground" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-foreground">Tarot Reading</h3>
                <p className="text-sm text-muted-foreground capitalize">
                  {data.spread_type?.replace('_', ' ') || 'Three Card Spread'}
                </p>
              </div>
            </div>
          </div>
        </CardHeader>

        <CardContent className="pt-4 space-y-4">
          {/* Question if provided */}
          {(data.question || topic) && (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <HelpCircle className="h-4 w-4" />
              <span>Reading for: <span className="text-foreground">{data.question || topic}</span></span>
            </div>
          )}

          {/* Cards Grid */}
          <div className="grid grid-cols-3 gap-3">
            {data.cards.map((card, idx) => {
              const posLower = card.position.toLowerCase();
              const gradient = positionColors[posLower] || "from-muted/50 to-muted/20";

              return (
                <div
                  key={idx}
                  className={`p-3 rounded-lg bg-gradient-to-br ${gradient} border border-border`}
                >
                  <div className="text-center">
                    <p className="text-xs text-muted-foreground mb-1">{card.position}</p>
                    <p className="text-sm font-bold text-foreground mb-1">{card.card}</p>
                    {card.reversed && (
                      <Badge variant="outline" className="text-xs bg-purple-500/20 text-purple-400 border-purple-500/30 mb-1">
                        <RotateCcw className="h-3 w-3 mr-1" />
                        Reversed
                      </Badge>
                    )}
                    <p className="text-xs text-muted-foreground mt-1">{card.meaning}</p>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Interpretation */}
          <div className="p-3 rounded-lg bg-primary/10 border border-primary/20">
            <div className="flex items-center gap-2 mb-2">
              <Sparkles className="h-4 w-4 text-primary" />
              <span className="text-sm font-medium text-primary">Interpretation</span>
            </div>
            <p className="text-sm text-foreground/80 leading-relaxed">{data.interpretation}</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Handle single card format
  const singleCard = data as SingleTarotCard;
  const gradient = singleCard.suit
    ? (singleCard.suit.toLowerCase() === 'cups' ? 'from-red-500/20 to-pink-500/10' :
       singleCard.suit.toLowerCase() === 'wands' ? 'from-orange-500/20 to-amber-500/10' :
       singleCard.suit.toLowerCase() === 'swords' ? 'from-blue-500/20 to-cyan-500/10' :
       'from-yellow-500/20 to-amber-500/10')
    : 'from-primary/20 to-primary/10';
  const icon = singleCard.suit ? suitIcons[singleCard.suit.toLowerCase()] : <Sparkles className="h-5 w-5 text-primary" />;

  return (
    <Card className="bg-card border-border overflow-hidden">
      <CardHeader className={`pb-3 bg-gradient-to-r ${gradient} border-b border-border`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-primary to-primary/70 flex items-center justify-center">
              {icon}
            </div>
            <div>
              <h3 className="text-lg font-bold text-foreground">{singleCard.card_name}</h3>
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
                  <Badge variant="outline" className="bg-primary/20 text-primary border-primary/30">
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
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <HelpCircle className="h-4 w-4" />
            <span>Reading for: <span className="text-foreground">{topic}</span></span>
          </div>
        )}

        {/* Card Meaning */}
        <div className="p-3 rounded-lg bg-muted/30 border border-border">
          <div className="flex items-center gap-2 mb-2">
            <Star className="h-4 w-4 text-yellow-400" />
            <span className="text-sm font-medium text-foreground">
              {singleCard.position === "upright" ? "Upright Meaning" : "Reversed Meaning"}
            </span>
          </div>
          <p className="text-sm text-muted-foreground">
            {singleCard.position === "upright" ? singleCard.meaning_upright : singleCard.meaning_reversed}
          </p>
        </div>

        {/* Interpretation */}
        {singleCard.interpretation && (
          <div className="p-3 rounded-lg bg-primary/10 border border-primary/20">
            <div className="flex items-center gap-2 mb-2">
              <Sparkles className="h-4 w-4 text-primary" />
              <span className="text-sm font-medium text-primary">Your Interpretation</span>
            </div>
            <p className="text-sm text-foreground/80 leading-relaxed">{singleCard.interpretation}</p>
          </div>
        )}

        {/* Advice */}
        {singleCard.advice && (
          <div className="pt-3 border-t border-border">
            <div className="flex items-start gap-2">
              <Sun className="h-4 w-4 text-yellow-400 mt-0.5" />
              <div>
                <span className="text-sm font-medium text-foreground">Advice: </span>
                <span className="text-sm text-muted-foreground">{singleCard.advice}</span>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
