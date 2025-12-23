import Link from "next/link"
import Image from "next/image"

interface City {
  name: string
  date: string
}

interface AnnouncementBannerProps {
  title: string
  subtitle: string
  cities: City[]
  ctaText: string
  image: string
}

export function AnnouncementBanner({ title, subtitle, cities, ctaText, image }: AnnouncementBannerProps) {
  return (
    <section className="px-6 py-12">
      <div className="max-w-4xl mx-auto bg-gradient-to-r from-emerald-200 via-cyan-200 to-blue-300 rounded-3xl overflow-hidden">
        <div className="grid md:grid-cols-2 items-center">
          <div className="p-8">
            <h2 className="text-3xl font-bold mb-2">{title}</h2>
            <p className="text-sm text-muted-foreground mb-6">{subtitle}</p>
            <div className="grid grid-cols-2 gap-4 mb-6">
              {cities.map((city) => (
                <div key={city.name} className="text-center">
                  <div className="font-bold text-lg">{city.name}</div>
                  <div className="text-sm">{city.date}</div>
                </div>
              ))}
            </div>
            <Link
              href="#"
              className="inline-flex items-center gap-2 bg-primary hover:bg-primary/90 text-white px-6 py-3 rounded-full font-medium transition-colors"
            >
              {ctaText}
            </Link>
          </div>
          <div className="relative h-full min-h-[300px]">
            <Image src={image || "/placeholder.svg"} alt="Messi" fill className="object-cover object-center" />
          </div>
        </div>
      </div>
    </section>
  )
}
