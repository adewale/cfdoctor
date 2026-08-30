export async function load({ params, platform }) {
  return platform.env.DB.prepare(
    "SELECT slug, name, summary FROM products WHERE slug = ?1 LIMIT 1"
  ).bind(params.slug).first();
}
