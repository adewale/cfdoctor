async function touch(db, ids) {
 for (let i=0;i<ids.length;i+=98) {
 const chunk = ids.slice(i,i+98);
 await db.prepare(`UPDATE persons SET seen=? WHERE project=? AND id IN (${chunk.map(()=>'?').join(',')})`).bind(now,project,...chunk).run();
 }
}
