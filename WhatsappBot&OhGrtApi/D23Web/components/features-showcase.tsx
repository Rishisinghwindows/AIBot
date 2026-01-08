"use client"

import { useState } from "react"
import Image from "next/image"
import Link from "next/link"

interface Category {
  id: string
  label: string
  active?: boolean
}

interface FeaturesShowcaseProps {
  title: string
  categories: Category[]
  showcase: {
    title: string
    description: string
    ctaText: string
    images: string[]
  }
}

export function FeaturesShowcase({ title, categories, showcase }: FeaturesShowcaseProps) {
  const [activeCategory, setActiveCategory] = useState(categories.find((c) => c.active)?.id || categories[0].id)

  return (
    <section className="py-16 px-6">
      <div className="max-w-6xl mx-auto">
        <h2 className="text-4xl font-bold text-center mb-4">{title}</h2>

        <div className="flex flex-wrap justify-center gap-3 mb-12">
          {categories.map((category) => (
            <button
              key={category.id}
              onClick={() => setActiveCategory(category.id)}
              className={`px-6 py-2 rounded-full font-medium transition-colors ${
                activeCategory === category.id ? "bg-primary text-white" : "bg-muted text-foreground hover:bg-muted/80"
              }`}
            >
              {category.label}
            </button>
          ))}
        </div>

        <div className="grid md:grid-cols-2 gap-8 items-center">
          <div className="flex gap-4 justify-center">
            {showcase.images.map((image, index) => (
              <div key={index} className="relative w-[200px] h-[400px] rounded-3xl overflow-hidden shadow-2xl">
                <Image src={image || "/placeholder.svg"} alt={`Feature ${index + 1}`} fill className="object-cover" />
              </div>
            ))}
          </div>

          <div>
            <h3 className="text-3xl font-bold mb-4">{showcase.title}</h3>
            <p className="text-lg text-muted-foreground mb-6">{showcase.description}</p>
            <Link
              href="#"
              className="inline-flex items-center gap-2 bg-primary hover:bg-primary/90 text-white px-6 py-3 rounded-full font-medium transition-colors"
            >
              {showcase.ctaText}
            </Link>
          </div>
        </div>
      </div>
    </section>
  )
}
