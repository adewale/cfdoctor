async function decode(stream) {
 const reader=stream.pipeThrough(new DecompressionStream('gzip')).getReader();
 let total=0;
 while(true) {const {value,done}=await reader.read(); if(done) break;
 total+=value.byteLength; if(total>1000000) {await reader.cancel();throw new Error('large');}
 await sink.write(value);}
}
