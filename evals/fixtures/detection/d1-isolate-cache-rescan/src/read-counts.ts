import { cachified } from '@epic-web/cachified'
import { LRUCache } from 'lru-cache'

// Per-isolate memory only: every new isolate starts empty, so the TTLs below
// bound staleness inside one isolate, not how often the table is scanned.
const lruCache = new LRUCache({ max: 500 })

export function getBlogPostReadCounts(env: Env) {
  return cachified({
    key: 'blog:post-read-counts',
    cache: lruCache,
    ttl: 1000 * 60 * 30,
    async getFreshValue() {
      return env.DB.prepare(
        'SELECT slug, COUNT(id) AS reads FROM post_reads GROUP BY slug',
      ).all()
    },
  })
}

export function getTotalReaderCount(env: Env) {
  return cachified({
    key: 'total-reader-count',
    cache: lruCache,
    ttl: 1000 * 60 * 5,
    async getFreshValue() {
      return env.DB.prepare(
        'SELECT COUNT(DISTINCT client_id) AS total FROM post_reads',
      ).first()
    },
  })
}
