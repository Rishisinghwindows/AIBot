"use client";

import { Train, Calendar, MapPin, Users, CheckCircle, Clock, AlertCircle } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface Passenger {
  booking_status: string;
  current_status: string;
  coach?: string;
  berth?: string;
}

interface PNRData {
  pnr: string;
  train_number: string;
  train_name: string;
  from_station: string;
  to_station: string;
  journey_date: string;
  class: string;
  chart_prepared: boolean;
  passengers: Passenger[];
}

interface PNRCardProps {
  data: PNRData;
}

export function PNRCard({ data }: PNRCardProps) {
  const getStatusColor = (status: string) => {
    const s = status.toUpperCase();
    if (s.includes("CNF") || s.includes("CONFIRMED")) return "bg-green-500/20 text-green-400 border-green-500/30";
    if (s.includes("RAC")) return "bg-yellow-500/20 text-yellow-400 border-yellow-500/30";
    if (s.includes("WL") || s.includes("WAITLIST")) return "bg-red-500/20 text-red-400 border-red-500/30";
    return "bg-muted text-muted-foreground border-muted-foreground/30";
  };

  return (
    <Card className="bg-card border-border overflow-hidden">
      {/* Header with Train Info */}
      <CardHeader className="pb-3 bg-gradient-to-r from-primary/10 to-primary/5 border-b border-border">
        <div className="flex items-start justify-between">
          <div>
            <CardTitle className="text-lg font-bold text-foreground flex items-center gap-2">
              <Train className="h-5 w-5 text-primary" />
              {data.train_name}
            </CardTitle>
            <p className="text-sm text-muted-foreground mt-1">Train #{data.train_number}</p>
          </div>
          <Badge variant="outline" className="text-xs bg-muted/50 border-border text-muted-foreground">
            PNR: {data.pnr}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="pt-4 space-y-4">
        {/* Journey Route */}
        <div className="flex items-center gap-3">
          <div className="flex-1">
            <div className="flex items-center gap-2 text-foreground font-medium">
              <MapPin className="h-4 w-4 text-green-400" />
              {data.from_station}
            </div>
          </div>
          <div className="flex-shrink-0 flex items-center gap-1">
            <div className="h-[2px] w-8 bg-border"></div>
            <Train className="h-4 w-4 text-muted-foreground" />
            <div className="h-[2px] w-8 bg-border"></div>
          </div>
          <div className="flex-1 text-right">
            <div className="flex items-center gap-2 justify-end text-foreground font-medium">
              {data.to_station}
              <MapPin className="h-4 w-4 text-red-400" />
            </div>
          </div>
        </div>

        {/* Journey Details */}
        <div className="grid grid-cols-3 gap-3 py-3 border-y border-border">
          <div className="text-center">
            <Calendar className="h-4 w-4 mx-auto text-muted-foreground mb-1" />
            <p className="text-xs text-muted-foreground">Date</p>
            <p className="text-sm font-medium text-foreground">{data.journey_date}</p>
          </div>
          <div className="text-center">
            <Badge variant="outline" className="mx-auto bg-primary/20 text-primary border-primary/30">
              {data.class}
            </Badge>
          </div>
          <div className="text-center">
            {data.chart_prepared ? (
              <div className="flex flex-col items-center">
                <CheckCircle className="h-4 w-4 text-green-400 mb-1" />
                <p className="text-xs text-green-400">Chart Ready</p>
              </div>
            ) : (
              <div className="flex flex-col items-center">
                <Clock className="h-4 w-4 text-yellow-400 mb-1" />
                <p className="text-xs text-yellow-400">Chart Pending</p>
              </div>
            )}
          </div>
        </div>

        {/* Passengers */}
        <div>
          <div className="flex items-center gap-2 mb-3">
            <Users className="h-4 w-4 text-muted-foreground" />
            <h4 className="text-sm font-medium text-foreground">Passengers ({data.passengers.length})</h4>
          </div>
          <div className="space-y-2">
            {data.passengers.map((passenger, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between p-2 rounded-lg bg-muted/50 border border-border"
              >
                <span className="text-sm text-foreground">Passenger {idx + 1}</span>
                <div className="flex items-center gap-2">
                  <Badge className={cn("text-xs", getStatusColor(passenger.current_status))}>
                    {passenger.current_status}
                  </Badge>
                  {passenger.coach && passenger.berth && (
                    <span className="text-xs text-muted-foreground">
                      {passenger.coach}/{passenger.berth}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
