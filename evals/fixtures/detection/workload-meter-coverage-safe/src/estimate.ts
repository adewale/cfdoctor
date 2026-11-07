function estimate(input) {
 const lines=[line('D1 rows written',input.writes),line('D1 rows read',input.reads),line('R2 storage',input.bytes),line('R2 Class B reads',input.gets)];
 const overageUsd=lines.reduce((n,l)=>n+l.overage,0);
 return {overageUsd,excluded:['Worker CPU; not a complete bill']};
}
