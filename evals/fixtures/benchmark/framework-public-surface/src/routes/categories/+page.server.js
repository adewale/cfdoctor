export async function load({ platform }) {
  const featured = await platform.env.DB.prepare(
    "SELECT slug, name FROM products ORDER BY published_at DESC LIMIT 50"
  ).all();
  return { featured: featured.results };
}
