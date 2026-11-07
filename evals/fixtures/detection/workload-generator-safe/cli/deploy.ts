function create(wrangler,eu) {return wrangler.run(['r2','bucket','create',name,...(eu?['--jurisdiction','eu']:[])]);}
function render(config) {
 const deployment={main:'worker.js',observability:{enabled:true}};
 deployment.r2_buckets=[{binding:'REPLAYS',bucket_name:config.bucket,jurisdiction:config.eu?'eu':undefined}];
 if(config.lake) deployment.pipelines=[{binding:'EVENTS_STREAM',stream:config.stream}];
 return `// generated
${JSON.stringify(deployment)}`;
}
