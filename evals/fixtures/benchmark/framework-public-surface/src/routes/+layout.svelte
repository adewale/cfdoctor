<script>
  let { data, children } = $props();
</script>

<header>
  <a href="/">Catalogue</a>
  <a href="/categories">Categories</a>
  <a href="/about">About</a>
  <span>{data.productCount} products</span>
</header>

{@render children()}
