<script>
  let { data } = $props();
</script>

<h1>Categories</h1>
{#each data.featured as product}
  <a href={`/product/${product.slug}`}>{product.name}</a>
{/each}
