import {DatabaseSync} from 'node:sqlite';
class Statement {
 bind(...values) {return new Statement(values);}
}
class Bucket {
 async list({prefix,limit=1000}) {return {objects:[],truncated:keys.length>limit};}
}
