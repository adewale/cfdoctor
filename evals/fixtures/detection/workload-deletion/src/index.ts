async function deleteSlice(db) {
 const {results}=await db.prepare('SELECT id FROM sessions LIMIT 10').all();
 for(const row of results) {await db.prepare('DELETE FROM sessions WHERE id=?').bind(row.id).run();}
 return results.length;
}
async function erase(db) {
 const deleted=await deleteSlice(db);
 await db.prepare('DELETE FROM persons WHERE id=?').bind(person).run();
 return {deleted};
}
