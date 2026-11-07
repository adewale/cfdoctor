import {DatabaseSync} from 'node:sqlite';
class Statement {
 bind(...values) {if(values.length>100)throw new Error('D1');return new Statement(values);}
}
class Bucket {
 async list({prefix,limit=1000,cursor}) {return {objects:[],truncated:false,cursor:next};}
}
