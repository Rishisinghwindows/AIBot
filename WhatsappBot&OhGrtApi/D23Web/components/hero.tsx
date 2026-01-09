import integrationsData from "@/data/integrations.json"

export function Hero() {
  return (
    <section className="pt-32 pb-16 px-4">
      <div className="container mx-auto max-w-4xl text-center">
        <h1 className="text-4xl md:text-6xl font-bold mb-6 text-balance">{integrationsData.hero.title}</h1>
        <p className="text-lg text-muted-foreground max-w-3xl mx-auto text-pretty">
          {integrationsData.hero.description}
        </p>
      </div>
    </section>
  )
}
