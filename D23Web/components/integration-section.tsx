"use client"

import { useState } from "react"
import Image from "next/image"

interface Tab {
  id: string
  label: string
}

interface Feature {
  id: string
  name: string
  description: string
  details: string
  howToUse: string
  image: string
  tabs: Tab[]
}

interface IntegrationSectionProps {
  id: string
  title: string
  features: Feature[]
  index: number
}

export function IntegrationSection({ id, title, features, index }: IntegrationSectionProps) {
  const [activeTab, setActiveTab] = useState(0)
  const feature = features[0]

  const isEven = index % 2 === 0

  return (
    <section id={id} className="py-20 px-4 scroll-mt-16">
      <div className="container mx-auto max-w-6xl">
        <h2 className="text-3xl md:text-4xl font-bold mb-16">{title}</h2>

        <div className={`grid md:grid-cols-2 gap-16 items-center ${isEven ? "" : "md:grid-flow-dense"}`}>
          {/* Text Content */}
          <div className={isEven ? "md:order-1" : "md:order-2"}>
            {/* Tab Navigation */}
            <div className="flex gap-1.5 mb-8">
              {feature.tabs.map((tab, idx) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(idx)}
                  className="relative h-0.5 flex-1 bg-border rounded-full overflow-hidden"
                  aria-label={tab.label}
                >
                  <div
                    className={`absolute inset-0 bg-brand transition-all duration-300 ${
                      activeTab === idx ? "opacity-100" : "opacity-0"
                    }`}
                  />
                </button>
              ))}
            </div>

            <h3 className="text-2xl md:text-3xl font-semibold mb-4">{feature.name}</h3>
            <p className="text-base text-muted-foreground mb-4 leading-relaxed">{feature.description}</p>
            <p className="text-sm text-muted-foreground/80 mb-8 leading-relaxed">{feature.details}</p>

            <div className="bg-muted/20 rounded-lg p-5 border border-border/30">
              <h4 className="text-sm font-semibold mb-3">How to use:</h4>
              <p className="text-sm text-muted-foreground leading-relaxed">{feature.howToUse}</p>
            </div>
          </div>

          {/* Phone Mockup */}
          <div className={`flex justify-center ${isEven ? "md:order-2" : "md:order-1"}`}>
            <div className="relative w-full max-w-[340px]">
              <div className="relative aspect-[9/19] bg-gradient-to-br from-brand/10 via-transparent to-brand/5 rounded-[2.5rem] overflow-hidden shadow-2xl border border-border/20">
                <Image
                  src={feature.image || "/placeholder.svg"}
                  alt={feature.name}
                  fill
                  className="object-cover"
                  unoptimized
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
