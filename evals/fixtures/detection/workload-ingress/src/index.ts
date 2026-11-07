async function route(request,env,path) {switch(path) {
 case '/e': if(request.method!=='POST') break; await event(request,env); return new Response();
 case '/r': if(request.method!=='POST') break; await replay(request,env); return new Response();
}}
