import { NextResponse } from "next/server"
import { withAuth } from "next-auth/middleware"

export default withAuth(
  () => {
    return NextResponse.next()
  },
  {
    callbacks: {
      authorized: ({ token }) => !!token,
    },
    pages: {
      signIn: "/login",
    },
  }
)

export const config = {
  matcher: ["/dashboard/:path*"],
}
