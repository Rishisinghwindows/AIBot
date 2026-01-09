"use client";

import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { MapPin, Loader2, X } from "lucide-react";

type LocationPromptProps = {
  onLocationShare: (location: { latitude: number; longitude: number; accuracy?: number }) => void;
  onDismiss: () => void;
};

export function LocationPrompt({ onLocationShare, onDismiss }: LocationPromptProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleShareLocation = async () => {
    if (!navigator.geolocation) {
      setError("Geolocation is not supported by your browser");
      return;
    }

    setIsLoading(true);
    setError(null);

    navigator.geolocation.getCurrentPosition(
      (position) => {
        setIsLoading(false);
        onLocationShare({
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
          accuracy: position.coords.accuracy,
        });
      },
      (err) => {
        setIsLoading(false);
        switch (err.code) {
          case err.PERMISSION_DENIED:
            setError("Location permission denied. Please enable it in your browser settings.");
            break;
          case err.POSITION_UNAVAILABLE:
            setError("Location information unavailable.");
            break;
          case err.TIMEOUT:
            setError("Location request timed out.");
            break;
          default:
            setError("An error occurred while getting your location.");
        }
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 0,
      }
    );
  };

  return (
    <div className="flex items-center gap-3 p-3 rounded-xl bg-gradient-to-r from-violet-500/10 to-fuchsia-500/10 border border-violet-500/20">
      <div className="w-10 h-10 rounded-full bg-gradient-to-br from-violet-500 to-fuchsia-500 flex items-center justify-center flex-shrink-0">
        <MapPin className="h-5 w-5 text-white" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-white">Share your location</p>
        <p className="text-xs text-zinc-400 truncate">
          {error || "Help me find nearby places for you"}
        </p>
      </div>
      <div className="flex items-center gap-2 flex-shrink-0">
        <Button
          variant="ghost"
          size="icon"
          onClick={onDismiss}
          className="h-8 w-8 text-zinc-400 hover:text-white hover:bg-zinc-800"
        >
          <X className="h-4 w-4" />
        </Button>
        <Button
          onClick={handleShareLocation}
          disabled={isLoading}
          className="bg-gradient-to-r from-violet-600 to-fuchsia-600 hover:from-violet-700 hover:to-fuchsia-700 text-white px-4"
        >
          {isLoading ? (
            <>
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              Getting...
            </>
          ) : (
            <>
              <MapPin className="h-4 w-4 mr-2" />
              Share
            </>
          )}
        </Button>
      </div>
    </div>
  );
}
