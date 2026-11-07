async function erase(db, ids) {
 const marks = ids.map(() => '?').join(',');
 await db.prepare(`DELETE FROM e WHERE project=? AND (a IN (${marks}) OR b IN (${marks}) OR c IN (${marks}))`).bind(project,...ids,...ids,...ids).run();
}
