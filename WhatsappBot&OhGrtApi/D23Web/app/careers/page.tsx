import { Header } from "@/components/header"
import { Footer } from "@/components/footer"
import { Button } from "@/components/ui/button"
import careersData from "@/data/careers.json"

export default function CareersPage() {
  return (
    <div className="min-h-screen">
      <Header />
      <main className="pt-24 pb-16">
        {/* Hero Section */}
        <section className="relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-brand/5 via-transparent to-brand/10" />
          <div className="container relative mx-auto px-4 py-20 text-center">
            <h1 className="text-5xl font-bold mb-4">
              Join <span className="text-brand">our team</span>
            </h1>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">{careersData.hero.subtitle}</p>
          </div>
        </section>

        {/* Open Roles */}
        <section className="container mx-auto px-4 py-16">
          <div className="max-w-3xl mx-auto">
            <h2 className="text-3xl font-bold mb-8">{careersData.openRoles.title}</h2>
            <div className="space-y-4">
              {careersData.openRoles.positions.map((position) => (
                <div
                  key={position.id}
                  className="flex items-center justify-between p-6 rounded-lg border bg-card hover:border-brand/50 transition-colors"
                >
                  <div>
                    <h3 className="text-xl font-semibold mb-1">{position.title}</h3>
                    <p className="text-sm text-muted-foreground">{position.location}</p>
                  </div>
                  <Button className="bg-brand text-white hover:bg-brand/90">Apply →</Button>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="relative overflow-hidden mt-20">
          <div className="absolute inset-0 bg-gradient-to-br from-brand/10 via-brand/5 to-transparent" />
          <div className="container relative mx-auto px-4 py-20">
            <div className="max-w-3xl mx-auto text-center">
              <h2 className="text-4xl font-bold mb-6">Ready to make an impact?</h2>
              <p className="text-lg text-muted-foreground mb-8">
                Join our mission to make AI accessible to everyone in India
              </p>
              <Button size="lg" className="bg-brand text-white hover:bg-brand/90">
                View all positions
              </Button>
            </div>
          </div>
        </section>
      </main>
      <Footer />
    </div>
  )
}
