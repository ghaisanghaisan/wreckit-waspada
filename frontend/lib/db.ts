import postgres from "postgres"

type DbConfig = {
  host: string
  port: number
  database: string
  username: string
  password: string
}

function buildConfig(): DbConfig {
  return {
    host: process.env.POSTGRES_HOST ?? "localhost",
    port: Number(process.env.POSTGRES_PORT ?? 5432),
    database: process.env.POSTGRES_DB ?? "waspada",
    username: process.env.POSTGRES_USER ?? "postgres",
    password: process.env.POSTGRES_PASSWORD ?? "postgres",
  }
}

const databaseUrl = process.env.DATABASE_URL

export const sql = databaseUrl
  ? postgres(databaseUrl, { max: 1 })
  : postgres({
      ...buildConfig(),
      max: 1,
    })
