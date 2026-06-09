import Image from "next/image";
import { AnimateOnView } from "../motion";
export function LogoCloudSection() {
  // TODO: Replace logo placeholders with real client/partner names or logos
  const logos = ["logo_kemhan", "logo_unhan", "logo_menkorps"];

  return (
    <section className="border-y bg-muted/30 py-12">
      <div className="mx-auto w-full max-w-6xl px-4 sm:px-6">
        {/* TODO: Replace with your trust/partner statement */}
        <p className="text-center text-sm font-medium text-muted-foreground">
          Trusted by teams monitoring critical public sentiment.
        </p>
        <div className="mt-8 flex justify-center gap-8 text-center text-sm font-semibold text-muted-foreground sm:grid-cols-3 ">
          {logos.map((logo, idx) => (
            <AnimateOnView animation="fadeUp" delay={idx * 0.1} margin="-60px">
              <div
                key={logo}
                className="relative flex w-32 aspect-square items-center justify-center"
              >
                <Image
                  src={"/" + logo + ".png"}
                  alt={logo}
                  fill
                  className="object-contain filter grayscale  transition-all duration-200 ease-in hover:grayscale-0"
                />
              </div>
            </AnimateOnView>
          ))}
        </div>
      </div>
    </section>
  );
}
