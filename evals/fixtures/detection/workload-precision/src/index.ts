async function ingest(request,env) {
 const ua=request.headers.get('User-Agent');
 for(const [key,value] of Object.entries(headers)) response.headers.set(key,value);
 await env.DB.prepare('SELECT 1').run();return new Response(ua);
}
