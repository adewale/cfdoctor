function estimate(input) {
 const store=input.store==='lake';
 const lines=[line('D1 rows written',input.writes),line('R2 storage',input.bytes)];
 const overageUsd=lines.reduce((n,l)=>n+l.overage,0);
 return {overageUsd,store};
}
