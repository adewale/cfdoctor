import {writeFileSync} from 'node:fs';
async function setup(token) {
 const wrangler=createWrangler({token,accountId});
 await putSecrets(wrangler,{CF_API_TOKEN:token},configPath);
}
