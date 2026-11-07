async function upload(env,key,bytes) {
 await env.REPLAYS.put(key,bytes);
 const receipt=await env.DB.prepare('INSERT OR IGNORE INTO receipts (id) VALUES (?)').bind(key).run();
 if(!receipt.meta.changes) return;
 await env.DB.prepare('INSERT INTO replays (id,chunks) VALUES (?,1) ON CONFLICT(id) DO UPDATE SET chunks=replays.chunks+1').bind(key).run();
}
