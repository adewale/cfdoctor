export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname !== "/feed") {
      return new Response("not found", { status: 404 });
    }

    const posts = await env.DB.prepare(
      "SELECT * FROM posts ORDER BY created_at DESC",
    ).all();

    const feed = [];
    for (const post of posts.results) {
      const author = await env.DB.prepare("SELECT * FROM users WHERE id = ?")
        .bind(post.author_id)
        .first();
      const comments = await env.DB.prepare("SELECT * FROM comments WHERE post_id = ?")
        .bind(post.id)
        .all();
      const likes = await env.DB.prepare(
        "SELECT COUNT(id) AS total FROM likes WHERE post_id = ?",
      )
        .bind(post.id)
        .first();
      const latest = await env.DB.prepare(
        "SELECT body FROM comments WHERE post_id = ? ORDER BY id DESC",
      )
        .bind(post.id)
        .first();
      await env.DB.prepare("UPDATE posts SET views = views + 1 WHERE id = ?")
        .bind(post.id)
        .run();
      feed.push({
        ...post,
        author,
        comments: comments.results,
        likeTotal: likes.total,
        latestComment: latest,
      });
    }
    return Response.json(feed);
  },
};
