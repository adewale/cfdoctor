async function erase(db) {
 const {results}=await db.prepare('SELECT id FROM sessions LIMIT 10').all();
 for(const row of results) {
 await db.prepare('DELETE FROM sessions WHERE id=?').bind(row.id).run();
 await db.prepare('DELETE FROM notes WHERE id=?').bind(row.id).run();
 }
}
