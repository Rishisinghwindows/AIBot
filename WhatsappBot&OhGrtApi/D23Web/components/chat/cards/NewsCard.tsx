"use client";

import { Newspaper, ExternalLink, Clock, Tag } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface NewsItem {
  title: string;
  summary?: string;
  description?: string;
  source?: string;
  url?: string;
  published_at?: string;
  category?: string;
  image_url?: string;
}

interface NewsCardProps {
  items: NewsItem[] | any; // Accept any to handle ToolResult format
  category?: string;
}

// Helper to extract news items from various formats
function extractNewsItems(data: any): NewsItem[] {
  if (!data) return [];

  // If it's already an array of items
  if (Array.isArray(data)) {
    return data.filter(item => item && (item.title || item.headline));
  }

  // If it's a ToolResult format: {success: true, data: {articles: [...]}}
  if (data.success && data.data) {
    const inner = data.data;
    if (Array.isArray(inner.articles)) return inner.articles;
    if (Array.isArray(inner.items)) return inner.items;
    if (Array.isArray(inner.news)) return inner.news;
    // Single article in data
    if (inner.title || inner.headline) return [inner];
    return [];
  }

  // Direct data format: {articles: [...]} or {items: [...]}
  if (Array.isArray(data.articles)) return data.articles;
  if (Array.isArray(data.items)) return data.items;
  if (Array.isArray(data.news)) return data.news;

  // Single item
  if (data.title || data.headline) return [data];

  return [];
}

export function NewsCard({ items: rawItems, category }: NewsCardProps) {
  const items = extractNewsItems(rawItems);

  if (!items || items.length === 0) {
    return null;
  }
  return (
    <Card className="bg-gradient-to-br from-zinc-900 to-zinc-950 border-zinc-800 overflow-hidden">
      <CardHeader className="pb-3 bg-gradient-to-r from-blue-500/10 to-cyan-500/10 border-b border-zinc-800">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-bold text-white flex items-center gap-2">
            <Newspaper className="h-5 w-5 text-blue-400" />
            {category ? `${category} News` : "Latest News"}
          </CardTitle>
          <Badge variant="outline" className="bg-zinc-800/50 text-zinc-300 border-zinc-700">
            {items.length} articles
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="pt-4 space-y-3">
        {items.map((item, idx) => (
          <div
            key={idx}
            className="p-3 rounded-lg bg-zinc-800/30 border border-zinc-700/50 hover:bg-zinc-800/50 transition-colors"
          >
            <div className="flex gap-3">
              {/* Thumbnail */}
              {item.image_url && (
                <div className="flex-shrink-0 w-16 h-16 rounded-lg overflow-hidden bg-zinc-800">
                  <img
                    src={item.image_url}
                    alt=""
                    className="w-full h-full object-cover"
                    onError={(e) => {
                      (e.target as HTMLImageElement).style.display = 'none';
                    }}
                  />
                </div>
              )}

              {/* Content */}
              <div className="flex-1 min-w-0">
                <h4 className="text-sm font-medium text-white line-clamp-2 mb-1">
                  {item.url ? (
                    <a
                      href={item.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="hover:text-blue-400 transition-colors inline-flex items-center gap-1"
                    >
                      {item.title}
                      <ExternalLink className="h-3 w-3 flex-shrink-0" />
                    </a>
                  ) : (
                    item.title
                  )}
                </h4>

                {(item.summary || item.description) && (
                  <p className="text-xs text-zinc-500 line-clamp-2 mb-2">{item.summary || item.description}</p>
                )}

                <div className="flex items-center gap-3 text-xs text-zinc-500">
                  {item.source && (
                    <span className="flex items-center gap-1">
                      <Tag className="h-3 w-3" />
                      {item.source}
                    </span>
                  )}
                  {item.published_at && (
                    <span className="flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      {formatTimeAgo(item.published_at)}
                    </span>
                  )}
                </div>
              </div>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

function formatTimeAgo(dateString: string): string {
  try {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  } catch {
    return dateString;
  }
}
