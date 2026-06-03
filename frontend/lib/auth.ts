import { compare } from "bcryptjs"
import { getServerSession, type NextAuthOptions } from "next-auth"
import CredentialsProvider from "next-auth/providers/credentials"

import { sql } from "./db"

type AgencyRecord = {
  id: string
  name: string
  email: string
  password: string
}

async function findAgencyByEmail(email: string): Promise<AgencyRecord | null> {
  const rows = await sql<AgencyRecord[]>`
    SELECT id, name, email, password
    FROM agencies
    WHERE email = ${email}
    LIMIT 1
  `
  return rows[0] ?? null
}

export const authOptions: NextAuthOptions = {
  session: {
    strategy: "jwt",
    maxAge: 30 * 24 * 60 * 60,
  },
  providers: [
    CredentialsProvider({
      name: "Agency Credentials",
      credentials: {
        email: { label: "Email", type: "email", placeholder: "you@example.com" },
        password: { label: "Password", type: "password" },
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) {
          return null
        }

        const normalizedEmail = credentials.email.trim().toLowerCase()
        const agency = await findAgencyByEmail(normalizedEmail)
        if (!agency) {
          return null
        }

        const isPasswordValid = await compare(credentials.password, agency.password)
        if (!isPasswordValid) {
          return null
        }

        return {
          id: agency.id,
          name: agency.name,
          email: agency.email,
        }
      },
    }),
  ],
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        return {
          ...token,
          id: user.id,
          name: user.name,
          email: user.email,
        }
      }
      return token
    },
    async session({ session, token }) {
      if (token?.id) {
        session.user = {
          ...session.user,
          id: String(token.id),
          name: token.name as string | undefined,
          email: token.email as string | undefined,
        }
      }
      return session
    },
  },
  pages: {
    signIn: "/login",
  },
  secret: process.env.NEXTAUTH_SECRET,
}

export async function auth() {
  return await getServerSession(authOptions)
}
