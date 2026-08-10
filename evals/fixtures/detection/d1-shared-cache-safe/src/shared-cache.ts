import { cachified } from '@epic-web/cachified'
import { LRUCache } from 'lru-cache'

// Per-isolate memory is reserved for values that are cheap to recompute.
const lruCache = new LRUCache({ max: 500 })

// Shared KV-backed adapter: every isolate reads the same cached aggregate, so
// the D1 scan runs once per TTL across the whole deployment.
function kvCache(env: Env) {
  return {
    async get(key: string) {
      return env.CACHE_KV.get(`cache:${key}`, 'json')
    },
    async set(key: string, value: unknown) {
      await env.CACHE_KV.put(`cache:${key}`, JSON.stringify(value), {
        expirationTtl: 3600,
      })
    },
    async delete(key: string) {
      await env.CACHE_KV.delete(`cache:${key}`)
    },
  }
}

export function getReadTotals(env: Env) {
  return cachified({
    key: 'blog:read-totals',
    cache: kvCache(env),
    ttl: 1000 * 60 * 30,
    async getFreshValue() {
      return env.DB.prepare(
        'SELECT slug, SUM(read_ms) AS total_ms FROM post_reads GROUP BY slug',
      ).all()
    },
  })
}

export function getNavLinks() {
  return cachified({
    key: 'nav:links',
    cache: lruCache,
    ttl: 1000 * 60 * 5,
    async getFreshValue() {
      return [
        { href: '/blog', label: 'Blog' },
        { href: '/talks', label: 'Talks' },
      ]
    },
  })
}
