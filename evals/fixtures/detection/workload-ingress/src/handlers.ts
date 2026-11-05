export async function event(request,env) {
 const project=await getProject(env.DB,id);
 if(project.allowedOrigins.length && !project.allowedOrigins.includes(request.headers.get('Origin'))) throw new Error('denied');
 await env.DB.prepare('INSERT INTO events VALUES (?)').bind(id).run();
}
export async function replay(request,env) {
 const project=await getProject(env.DB,id);

 await env.REPLAYS.put(key,bytes);
}
