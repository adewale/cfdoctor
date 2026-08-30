export function GET() {
  return new Response(
    '<?xml version="1.0"?><urlset>' +
      '<url><loc>https://catalog.example.com/</loc></url>' +
      '<url><loc>https://catalog.example.com/categories</loc></url>' +
    '</urlset>',
    { headers: { "content-type": "application/xml" } }
  );
}
