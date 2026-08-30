export async function load({ platform }) {
  const [products, categories] = await platform.env.DB.batch([
    platform.env.DB.prepare("SELECT COUNT(id) AS total FROM products"),
    platform.env.DB.prepare(
      "SELECT category, COUNT(id) AS total FROM products GROUP BY category ORDER BY total DESC LIMIT 20"
    ),
  ]);
  return { productCount: products.results[0].total, categories: categories.results };
}
