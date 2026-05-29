import { FeaturesSection } from "@/components/landing/features"
import { HeroSection } from "@/components/landing/hero"
import { LogoCloudSection } from "@/components/landing/logo-cloud"
import { LandingNavbar } from "@/components/landing/navbar"
import { LandingFooter } from "@/components/landing/footer"

export default function HomePage() {
	return (
		<div className="min-h-screen bg-background text-foreground">
			<LandingNavbar />

			<main>
				<HeroSection />
				<LogoCloudSection />
				<FeaturesSection />

				<section id="pricing" className="border-t bg-muted/20 py-20 sm:py-24">
					<div className="mx-auto w-full max-w-6xl px-4 sm:px-6">
						{/* TODO: Replace pricing section content */}
						<h2 className="text-3xl font-semibold text-foreground sm:text-4xl">Pricing built for scale</h2>
						<p className="mt-3 max-w-2xl text-base text-muted-foreground">
							Add your pricing tiers, billing cadence, and plan comparison here.
						</p>
					</div>
				</section>

				<section id="about" className="py-20 sm:py-24">
					<div className="mx-auto w-full max-w-6xl px-4 sm:px-6">
						{/* TODO: Replace about section content */}
						<h2 className="text-3xl font-semibold text-foreground sm:text-4xl">Purpose-built for critical teams</h2>
						<p className="mt-3 max-w-2xl text-base text-muted-foreground">
							Describe your mission, the story behind the product, and why teams trust you.
						</p>
					</div>
				</section>

				<section id="contact" className="border-t bg-muted/20 py-20 sm:py-24">
					<div className="mx-auto w-full max-w-6xl px-4 sm:px-6">
						{/* TODO: Replace contact section content */}
						<h2 className="text-3xl font-semibold text-foreground sm:text-4xl">Let’s talk</h2>
						<p className="mt-3 max-w-2xl text-base text-muted-foreground">
							Add a contact form, calendar embed, or support details here.
						</p>
					</div>
				</section>
			</main>

			<LandingFooter />
		</div>
	)
}
