import {writeFileSync} from 'node:fs';
async function setup(token,runtimeReadToken) {
 const wrangler=createWrangler({token,accountId});
 await putSecrets(wrangler,{CF_API_TOKEN:runtimeReadToken},configPath);
}
