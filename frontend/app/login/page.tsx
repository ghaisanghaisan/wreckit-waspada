"use client"

import { LoginForm } from "@/components/login-form"
import Image from "next/image"

export default function LoginPage() {
  return (
    <div className="flex min-h-svh flex-col items-center justify-center gap-6 bg-background p-6 md:p-10">
      <div className="flex w-full max-w-sm flex-col gap-6">
        <a href="/" className="flex items-center gap-2 self-center font-extrabold">
            <Image
              src="/logo_waspada.png"
              alt="Waspada logo"
              width={36}
              height={36}
              className="object-contain"
            />
        WASPADA
        </a>
        <LoginForm />
      </div>
    </div>
  )
}
