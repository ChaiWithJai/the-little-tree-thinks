const $=selector=>document.querySelector(selector);const $$=selector=>[...document.querySelectorAll(selector)];
const esc=value=>String(value??'').replace(/[&<>"']/g,char=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[char]));
const state={status:null,cases:[],pagePresets:[],reviewIssues:[],runs:[],selectedCase:null,currentRun:null,currentImage:null,imageStatus:'idle',imageError:null,mode:'html',dayZero:true,detailsExpanded:false,draftId:null,routeVersion:0,machine:new BonsaiFSM.BonsaiRunMachine(),verdict:null,openEvents:new Set(),pollVersion:0};
const defaultPlan=['Define a checkable case','Retrieve local evidence','Synthesize with the selected model','Resolve cited source IDs','Checkpoint the inspectable artifact','Apply and retain human judgment'];
const DRAFTS_KEY='bonsai-drafts-v1';

async function json(url,options){const response=await fetch(url,options);let data={};try{data=await response.json()}catch{}if(!response.ok){const error=new Error(data.error||`Request failed (${response.status})`);error.status=response.status;throw error}return data}
function estimatedTokens(value){return Math.max(0,Math.round(String(value||'').length/4))}
function fileName(path){return String(path||'source').split('/').pop()}
function formatTime(epoch){return new Date(epoch*1000).toLocaleString([], {month:'short',day:'numeric',hour:'numeric',minute:'2-digit'})}
function routeFromLocation(){const parts=location.pathname.split('/').filter(Boolean);if(!parts.length)return{kind:'home'};if(parts.length===2&&['draft','jobs','runs'].includes(parts[0])&&/^[\w-]+$/.test(parts[1]))return{kind:parts[0]==='jobs'?'job':parts[0]==='runs'?'run':'draft',id:parts[1]};return{kind:'unknown'}}
function writeRoute(path,{replace=false}={}){if(location.pathname===path)return;(replace?history.replaceState:history.pushState).call(history,{bonsai:true},'',path)}
function readDrafts(){try{const value=JSON.parse(localStorage.getItem(DRAFTS_KEY)||'{}');return value&&typeof value==='object'?value:{}}catch{return{}}}
function draftId(){return globalThis.crypto?.randomUUID?.().replaceAll('-','')||`${Date.now().toString(36)}${Math.random().toString(36).slice(2)}`}
function saveDraft(surface){const input=surface==='home'?$('#agent-request'):$('#question');const prompt=input?.value||'';if(!prompt.trim()&&!state.draftId)return null;if(!state.draftId){state.draftId=draftId();writeRoute(`/draft/${state.draftId}`)}const drafts=readDrafts();drafts[state.draftId]={id:state.draftId,surface,prompt,mode:surface==='home'?(input.dataset.mode||inferMode(prompt)):state.mode,corpus:$('#corpus').value||'',pageType:$('#page-type').value||'custom',image:state.currentImage||null,updatedAt:Date.now()};const retained=Object.values(drafts).sort((a,b)=>b.updatedAt-a.updatedAt).slice(0,20);localStorage.setItem(DRAFTS_KEY,JSON.stringify(Object.fromEntries(retained.map(item=>[item.id,item]))));return drafts[state.draftId]}
function loadDraft(id){return readDrafts()[id]||null}

function renderState(){
  if(state.mode==='image'){
    const steps=[['idle','Prompt'],['synthesizing','Render'],['awaiting_review','Ready']];const active=state.imageStatus==='generating'?'synthesizing':state.imageStatus==='ready'?'awaiting_review':'idle';
    $('#state-pills').innerHTML=steps.map(([key,label])=>`<span class="state-pill ${key===active?'active':''}" data-state="${key}"><i></i>${label}</span>`).join('');
    $('#checkpoint').textContent=state.currentImage?`image · seed ${state.currentImage.seed}`:'No image generated';return
  }
  $('#state-pills').innerHTML=state.machine.pills().map(item=>`<span class="state-pill ${item.active?'active':''}" data-state="${item.key}"><i></i>${item.label}</span>`).join('');
  const run=state.currentRun;$('#checkpoint').textContent=run?`run ${run.id.slice(0,8)} · ${run.review?'review retained':'awaiting review'}`:state.machine.jobId?`job ${state.machine.jobId.slice(0,8)} · ${state.machine.state}`:state.selectedCase?`case ${state.selectedCase.id}`:'No run selected';
}
function renderCases(){
  $('#case-count').textContent=state.cases.length;
  $('#cases').innerHTML=state.cases.map(item=>`<button class="case ${state.selectedCase?.id===item.id&&!state.currentRun?'active':''}" data-id="${esc(item.id)}"><strong><span class="dot"></span>${esc(item.title)}</strong><small>${esc(item.benchmark||item.corpus||'local')}</small></button>`).join('');
  $$('.case').forEach(button=>button.onclick=()=>selectCase(state.cases.find(item=>item.id===button.dataset.id)));
}
function renderRuns(){
  $('#runs').innerHTML=state.runs.length?state.runs.map(run=>{const verdict=run.review?.verdict||'open';return `<button class="session ${state.currentRun?.id===run.id?'active':''}" data-id="${esc(run.id)}"><strong><span class="dot ${esc(verdict)}"></span>${esc((run.question||'Untitled run').slice(0,42))}</strong><small>${esc(verdict)} · ${formatTime(run.created_at)}</small></button>`}).join(''):'<p class="muted">No retained runs yet.</p>';
  $$('.session').forEach(button=>button.onclick=()=>selectRun(state.runs.find(run=>run.id===button.dataset.id)));
}
function clearActiveJob(){localStorage.removeItem('bonsai-active-job');localStorage.removeItem('bonsai-active-mode')}
function abandonPolling(){state.pollVersion+=1;clearActiveJob()}
function inferMode(prompt){const value=String(prompt||'').toLowerCase();if(/\b(image|illustration|portrait|photo|visual direction|key art|render|poster)\b/.test(value))return'image';if(/\b(page|website|landing|moodboard|lookbook|dashboard|interface|storyboard|product detail|collection grid|html)\b/.test(value))return'html';return'text'}
function updateAgentStart(){const input=$('#agent-request');if(!input)return;const prompt=input.value.trim();const mode=input.dataset.mode||inferMode(prompt);const labels={html:'Page and interface creation',image:'Local image creation',text:'Research and synthesis'};$('#agent-go').disabled=!prompt;$('#agent-route').innerHTML=prompt?`<i></i> Bonsai will start with ${labels[mode]}`:'<i></i> Bonsai chooses the best local capability';$('#agent-start-error').textContent=''}
function setMode(mode){state.mode=mode;$('#request-mode').value=mode;$('#corpus-control').classList.toggle('hidden',mode!=='text');$('#page-type-control').classList.toggle('hidden',mode!=='html');const copy={image:['Describe the image you want to create…','Bonsai Image 4B renders locally from this same conversation.'],html:['Describe the HTML page you want to build…','Choose a page type or customize the prompt; Bonsai opens the result in a sandboxed preview.'],text:['Ask a question grounded in your local evidence…','Answers use local evidence and retain inspectable citations.']}[mode];$('#question').placeholder=copy[0];$('#composer-hint').textContent=copy[1]}
function renderCorpora(){const corpora=state.status?.harness?.corpora||[];$('#corpus').innerHTML=['<option value="">All indexed sources</option>',...corpora.map(item=>`<option value="${esc(item.id)}">${esc(item.label)}</option>`)].join('')}
function renderPagePresets(){const options=['<option value="custom">Custom page</option>',...state.pagePresets.map(item=>`<option value="${esc(item.id)}">${esc(item.label)}</option>`)];$('#page-type').innerHTML=options.join('')}
function applyPagePreset(id){const preset=state.pagePresets.find(item=>item.id===id);if(!preset)return;state.dayZero=false;state.draftId=null;state.selectedCase={id:preset.id,title:preset.label,benchmark:preset.source,category:preset.category,intent:preset.intent,question:preset.prompt,acceptance:preset.acceptance,corpus:null};$('#question').value=preset.prompt+`\n\nAcceptance criteria:\n${preset.acceptance.map(value=>`- ${value}`).join('\n')}`;state.currentRun=null;state.machine.reset(true);saveDraft('prompt');renderAll()}
function selectCase(item){abandonPolling();state.dayZero=false;state.draftId=null;setMode('html');$('#page-type').value='custom';state.selectedCase=item;state.currentRun=null;state.currentImage=null;state.verdict=null;const criteria=(item.acceptance||[]).map(value=>`- ${value}`).join('\n');$('#question').value=item.question+(criteria?`\n\nAcceptance criteria:\n${criteria}`:'');$('#corpus').value=item.corpus||'';state.machine.reset(true);saveDraft('prompt');renderAll()}
function selectRun(run,options={}){abandonPolling();state.dayZero=false;state.detailsExpanded=false;state.draftId=null;setMode(run.mode==='html'?'html':'text');state.currentImage=null;state.currentRun=run;state.selectedCase=state.cases.find(item=>item.id===run.case_id)||{id:run.case_id||'ad-hoc',title:'Ad hoc task',question:run.question,corpus:run.corpus,intent:'Previously retained local run.'};state.verdict=run.review?.verdict||null;state.machine.hydrateRun(!!run.review);if(options.updateUrl!==false)writeRoute(`/runs/${run.id}`);renderAll()}
function newRun(options={}){abandonPolling();state.dayZero=true;state.detailsExpanded=false;state.draftId=null;state.currentRun=null;state.currentImage=null;state.imageStatus='idle';state.imageError=null;state.selectedCase=null;state.verdict=null;$('#question').value='';$('#agent-request').value='';$('#agent-request').dataset.mode='';$('#corpus').value='';$('#page-type').value='custom';$('#composer-error').textContent='';state.machine.reset(false);if(options.updateUrl!==false)writeRoute('/');renderAll();requestAnimationFrame(()=>$('#day-zero-title').focus())}
function beginStarter(mode,options={}){state.dayZero=false;setMode(mode);state.currentRun=null;state.currentImage=null;state.selectedCase=null;state.imageStatus='idle';state.imageError=null;state.verdict=null;$('#question').value='';$('#page-type').value='custom';state.machine.reset(false);if(options.updateUrl!==false)saveDraft('prompt');renderAll();requestAnimationFrame(()=>$('#question').focus())}
function startUniversalTask(event){event.preventDefault();const input=$('#agent-request');const prompt=input.value.trim();if(!prompt){$('#agent-start-error').textContent='Tell Bonsai what outcome you need.';input.focus();return}saveDraft('home');const mode=input.dataset.mode||inferMode(prompt);beginStarter(mode,{updateUrl:false});$('#question').value=prompt;saveDraft('prompt');renderAll();requestAnimationFrame(()=>$('#composer').requestSubmit())}

function renderDayZero(){const prompting=!state.dayZero&&!state.currentRun&&!state.machine.jobId;const working=state.machine.isRunning||state.imageStatus==='generating';const reviewing=!!state.currentRun&&!state.currentRun.review;document.body.classList.toggle('day-zero',state.dayZero);document.body.classList.toggle('prompting',prompting);document.body.classList.toggle('working',working);document.body.classList.toggle('reviewing',reviewing);document.body.classList.toggle('show-details',state.detailsExpanded);$('#day-zero').classList.toggle('hidden',!state.dayZero);const resume=$('#resume-latest');resume.classList.toggle('hidden',!state.runs.length);if(state.runs.length)resume.innerHTML=`Resume “${esc((state.runs[0].question||'latest work').slice(0,46))}${(state.runs[0].question||'').length>46?'…':''}” <span>→</span>`}

function renderHeader(){
  if(document.body.classList.contains('prompting')){const copy={html:['page','Describe the page you want to make','A sentence is enough. Choose a page shape below if it helps you get started.'],image:['visual','What should the image feel like?','Describe the subject, mood, material, or moment. Bonsai will render it privately on this Mac.'],text:['knowledge','What do you want to understand?','Ask naturally. Bonsai will ground the answer in your indexed local sources.']}[state.mode];$('#task-corpus').textContent='start';$('#task-case').textContent=copy[0];$('#task-title').textContent=copy[1];$('#task-intent').textContent=copy[2];return}
  if(state.mode==='image'){$('#task-corpus').textContent='local';$('#task-case').textContent='image';$('#task-title').textContent=state.currentImage?.prompt||'Create an image with Bonsai';$('#task-intent').textContent='Describe a visual in the same composer used for text. The artifact renders locally with Bonsai Image 4B.';return}
  if(state.mode==='html'){$('#task-corpus').textContent=state.selectedCase?.benchmark||'local';$('#task-case').textContent=state.selectedCase?.category||'html-page';$('#task-title').textContent=state.currentRun?.question||state.selectedCase?.title||'Build and preview an HTML page';$('#task-intent').textContent=state.currentRun?'Previously created page. Review, refine, or export it.':state.selectedCase?.intent||'Generate a self-contained page, validate it, and inspect the sandboxed preview.';return}
  const item=state.selectedCase;const run=state.currentRun;const prompt=$('#question').value.trim();const adHoc=item?.id==='ad-hoc';
  $('#task-corpus').textContent=item?.benchmark||(run?.corpus??item?.corpus??'local')||'local';$('#task-case').textContent=adHoc?'research':item?.category||item?.id||'research';
  $('#task-title').textContent=run?.question||item?.title||prompt||'Ask Bonsai to research and synthesize';
  $('#task-intent').textContent=(!adHoc&&item?.intent)||(run?'Review the answer, inspect its sources, or continue with a follow-up.':'Bonsai is finding the strongest local evidence, drafting an answer, and checking every reference.');
}
function renderPlan(){
  if(state.mode==='image'){
    const plan=['Describe the visual','Render with Bonsai Image 4B','Inspect the generated artifact'];let statuses=[$('#question').value.trim()?'done':'active','pending','pending'];if(state.imageStatus==='generating')statuses=['done','active','pending'];if(state.imageStatus==='ready')statuses=['done','done','done'];if(state.imageStatus==='failed')statuses=['done','blocked','pending'];const done=statuses.filter(value=>value==='done').length;
    $('#plan-progress').textContent=`${done} of ${plan.length} · creating your visual`;$('#plan').innerHTML=plan.map((title,index)=>{const status=statuses[index];const labels={done:'Done',active:'Creating',blocked:'Needs attention',pending:'Next'};const icons={done:'✓',active:'',blocked:'!',pending:''};return `<li class="plan-step ${status}"><span class="step-icon">${icons[status]}</span><span>${title}</span><span class="step-tag">${labels[status]}</span></li>`}).join('');return
  }
  if(state.mode==='html'){
    const plan=['Describe the page','Prepare your request','Create the page','Check the result','Open the preview'];const statuses=state.machine.planStatuses(plan.length);const done=statuses.filter(value=>value==='done').length;$('#plan-progress').textContent=`${done} of ${plan.length} · making your page`;$('#plan').innerHTML=plan.map((title,index)=>{const status=statuses[index];const labels={done:'Done',active:'Working',blocked:'Needs attention',pending:'Next'};const icons={done:'✓',active:'',blocked:'!',pending:''};return `<li class="plan-step ${status}"><span class="step-icon">${icons[status]}</span><span>${title}</span><span class="step-tag">${labels[status]}</span></li>`}).join('');return
  }
  const plan=['Understand the question','Find the strongest local sources','Draft a grounded answer','Check every reference','Save this version','Review the result'];const statuses=state.machine.planStatuses(plan.length);const done=statuses.filter(value=>value==='done').length;
  $('#plan-progress').textContent=`${done} of ${plan.length} · answering from your sources`;
  $('#plan').innerHTML=plan.map((title,index)=>{const status=statuses[index];const labels={done:'Done',active:'Working',blocked:'Needs attention',pending:'Next'};const icons={done:'✓',active:'',blocked:'!',pending:''};return `<li class="plan-step ${status}"><span class="step-icon">${icons[status]}</span><span>${esc(title)}</span><span class="step-tag">${labels[status]}</span></li>`}).join('');
}
function runEvents(run){
  if(!run)return[];
  if(run.mode==='html'){
    const checks=Object.entries(run.checks||{}).map(([key,value])=>`${value?'✓':'×'} ${key.replaceAll('_',' ')}`).join('\n');const qualityChecks=Object.entries(run.quality?.checks||{}).map(([key,value])=>`${value?'✓':'×'} ${key.replaceAll('_',' ')}`).join('\n');const generation=run.generation||{};const distilled=generation.render_strategy==='teacher-distilled';return [
      {id:'received',icon:'›_',title:'HTML specification received',duration:'',kind:'text',content:run.question},
      {id:'preview',icon:'</>',title:'Your page is ready',duration:'saved locally',kind:'html-preview',content:run.artifact},
      ...(distilled?[{id:'distillation',icon:'⇢',title:'Student → teacher distillation',duration:run.quality?.distillation_version||'teacher-v1',kind:'terminal',content:`Student score: ${generation.model_quality_score??'runtime failure'}\nFinal score: ${run.quality?.score??0}\nStrategy: ${generation.render_strategy}\nReason: ${generation.fallback_reason||'teacher bar selected'}`}]:[]),
      {id:'quality',icon:'◇',title:`Art-direction fidelity → ${run.quality?.score??0}/100`,duration:run.quality?.distillation_version||'measured',kind:'terminal',content:qualityChecks},
      {id:'checks',icon:'✓',title:'HTML contract checks',duration:'deterministic',kind:'terminal',content:checks},
    ]
  }
  const sourceLines=(run.hits||[]).map((hit,index)=>`S${index+1}  ${fileName(hit.path)}  · ${hit.corpus} · score ${hit.score}`).join('\n');
  const checks=Object.entries(run.checks||{}).map(([key,value])=>`${value===true?'✓':value===false?'×':'·'} ${key.replaceAll('_',' ')}: ${value}`).join('\n');
  const events=[
    {id:'received',icon:'›_',title:'Task received and normalized',duration:'',kind:'text',content:`${run.question}\nCorpus: ${run.corpus||'both corpora'}`},
    {id:'retrieval',icon:'⌕',title:`retrieval → ${(run.hits||[]).length} local source chunks`,duration:'local',kind:'terminal',content:sourceLines||'No matching local source chunks.'},
    {id:'model',icon:'B',title:`${run.model} → cited artifact`,duration:`${(run.latency_ms/1000).toFixed(1)}s`,kind:'answer',content:run.answer||run.error||'No answer returned.'},
    {id:'checks',icon:'✓',title:'citation-checker → automated contract checks',duration:'deterministic',kind:'terminal',content:checks},
  ];
  if(run.review)events.push({id:'review',icon:'◆',title:`human review → ${run.review.verdict}`,duration:formatTime(run.review.reviewed_at),kind:'text',content:[...(run.review.issues||[]),run.review.note].filter(Boolean).join('\n')||'No review note.'});
  return events;
}
function inlineMarkdown(text){
  const code=[];let value=esc(text).replace(/`([^`]+)`/g,(_,content)=>{const token=`\u0000CODE${code.length}\u0000`;code.push(`<code>${content}</code>`);return token});
  value=value.replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g,'<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>')
    .replace(/\*\*(.+?)\*\*/g,'<strong>$1</strong>').replace(/__(.+?)__/g,'<strong>$1</strong>')
    .replace(/(^|[\s(])\*([^*\n]+)\*/g,'$1<em>$2</em>').replace(/(^|[\s(])_([^_\n]+)_/g,'$1<em>$2</em>')
    .replace(/\[S(\d+)\]/g,'<button type="button" class="citation" data-source="$1" aria-label="Open source $1">S$1</button>');
  return value.replace(/\u0000CODE(\d+)\u0000/g,(_,index)=>code[Number(index)]);
}
function markdownCells(line){return line.trim().replace(/^\||\|$/g,'').split('|').map(cell=>cell.trim())}
function markdownBody(text){
  const lines=String(text||'').replace(/\r\n?/g,'\n').split('\n');const output=[];let index=0;
  const startsBlock=(line,next='')=>!line.trim()||/^\s*(```|#{1,4}\s|>|[-+*]\s+|\d+[.)]\s+|(?:-{3,}|\*{3,}|_{3,})\s*$)/.test(line)||(/\|/.test(line)&&/^\s*\|?\s*:?-{3,}/.test(next));
  while(index<lines.length){
    const line=lines[index];if(!line.trim()){index+=1;continue}
    const fence=line.match(/^\s*```([\w-]+)?\s*$/);if(fence){const body=[];index+=1;while(index<lines.length&&!/^\s*```\s*$/.test(lines[index]))body.push(lines[index++]);if(index<lines.length)index+=1;output.push(`<pre class="code-block"><code${fence[1]?` data-language="${esc(fence[1])}"`:''}>${esc(body.join('\n'))}</code></pre>`);continue}
    const heading=line.match(/^\s*(#{1,4})\s+(.+)$/);if(heading){const level=Math.min(4,heading[1].length+1);output.push(`<h${level}>${inlineMarkdown(heading[2])}</h${level}>`);index+=1;continue}
    if(/^\s*(?:-{3,}|\*{3,}|_{3,})\s*$/.test(line)){output.push('<hr>');index+=1;continue}
    if(/^\s*>/.test(line)){const quote=[];while(index<lines.length&&/^\s*>/.test(lines[index]))quote.push(lines[index++].replace(/^\s*>\s?/,''));output.push(`<blockquote>${quote.map(inlineMarkdown).join('<br>')}</blockquote>`);continue}
    const list=line.match(/^\s*([-+*]|\d+[.)])\s+(.+)$/);if(list){const ordered=/\d/.test(list[1]);const items=[];while(index<lines.length){const match=lines[index].match(/^\s*([-+*]|\d+[.)])\s+(.+)$/);if(!match||/\d/.test(match[1])!==ordered)break;items.push(`<li>${inlineMarkdown(match[2])}</li>`);index+=1}const tag=ordered?'ol':'ul';output.push(`<${tag}>${items.join('')}</${tag}>`);continue}
    if(index+1<lines.length&&/\|/.test(line)&&/^\s*\|?\s*:?-{3,}/.test(lines[index+1])){const headers=markdownCells(line);index+=2;const rows=[];while(index<lines.length&&/\|/.test(lines[index])&&lines[index].trim())rows.push(markdownCells(lines[index++]));output.push(`<div class="table-scroll" role="region" aria-label="Scrollable result table" tabindex="0"><table><thead><tr>${headers.map(cell=>`<th scope="col">${inlineMarkdown(cell)}</th>`).join('')}</tr></thead><tbody>${rows.map(row=>`<tr>${headers.map((_,cellIndex)=>`<td>${inlineMarkdown(row[cellIndex]||'')}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`);continue}
    const paragraph=[line.trim()];index+=1;while(index<lines.length&&!startsBlock(lines[index],lines[index+1]||'')){paragraph.push(lines[index].trim());index+=1}output.push(`<p>${paragraph.map(inlineMarkdown).join('<br>')}</p>`)
  }
  return output.join('');
}
function citationAnswer(text){return `<div class="result-tools"><span>Grounded answer</span><button type="button" class="copy-result">Copy answer</button></div><div class="markdown-body">${markdownBody(text)}</div><aside id="source-peek" class="source-peek hidden" aria-live="polite"></aside>`}
function legacyCopy(text){const input=document.createElement('textarea');input.value=text;input.setAttribute('readonly','');input.style.position='fixed';input.style.opacity='0';document.body.append(input);input.select();let copied=false;try{copied=document.execCommand('copy')}catch{}input.remove();return copied}
async function copyResult(text,button){let copied=legacyCopy(text);try{if(navigator.clipboard?.writeText){await navigator.clipboard.writeText(text);copied=true}}catch{}button.textContent=copied?'Copied':'Copy unavailable';button.classList.toggle('copied',copied);setTimeout(()=>{button.textContent='Copy answer';button.classList.remove('copied')},1600)}
function showSource(index,button){const hit=state.currentRun?.hits?.[index];const target=$('#source-peek');if(!hit||!target)return;$$('.citation').forEach(item=>item.setAttribute('aria-expanded',String(item===button)));target.classList.remove('hidden');target.innerHTML=`<div><span>Source ${index+1}</span><button type="button" class="close-source" aria-label="Close source">×</button></div><strong>${esc(fileName(hit.path))}</strong><small>${esc(hit.corpus||'local evidence')} · relevance ${esc(hit.score??'')}</small><p>${esc(hit.text)}</p>`;const close=$('.close-source');close.onclick=()=>{target.classList.add('hidden');button.setAttribute('aria-expanded','false');button.focus()};close.focus()}
function renderEvents(){
  const events=state.mode==='image'&&state.currentImage?[{id:'image',icon:'✦',title:'Bonsai Image 4B → visual artifact',duration:`seed ${state.currentImage.seed}`,kind:'image',content:state.currentImage}]:runEvents(state.currentRun);$('#event-count').textContent=events.length?`${events.length} observed event${events.length===1?'':'s'}`:'';
  $('#events').innerHTML=events.map(event=>{const primary=['model','image','preview'].includes(event.id);const open=state.openEvents.has(event.id)||primary;let body=event.kind==='answer'?citationAnswer(event.content):event.kind==='terminal'?`<pre>${esc(event.content)}</pre>`:event.kind==='image'?`<figure class="generated-image"><img src="${esc(event.content.url)}" alt="${esc(event.content.prompt)}"><figcaption>${esc(event.content.prompt)}<span>${esc(event.content.size)} · ${event.content.steps} steps</span></figcaption></figure>`:event.kind==='html-preview'?`<div class="preview-toolbar"><span>${esc(event.content.filename)}</span><span><a href="${esc(event.content.url)}" target="_blank" rel="noopener">Open preview ↗</a><a href="${esc(event.content.url)}" download="${esc(event.content.filename)}">Export HTML ↓</a></span></div><iframe class="html-preview" src="${esc(event.content.url)}" sandbox="allow-scripts" title="Generated HTML preview"></iframe>`:esc(event.content).replace(/\n/g,'<br>');return `<article class="event ${primary?'primary-result':'technical-event'}"><button class="event-head" data-event="${event.id}"><span class="event-icon">${esc(event.icon)}</span><strong>${esc(event.title)}</strong><small>${esc(event.duration)}</small><span>${open?'▾':'▸'}</span></button>${open?`<div class="event-detail ${event.kind}">${body}</div>`:''}</article>`}).join('');
  $('.loop-label>span:first-child').textContent=state.currentRun?'Your result':'Execution';
  $$('.event-head').forEach(button=>button.onclick=()=>{state.openEvents.has(button.dataset.event)?state.openEvents.delete(button.dataset.event):state.openEvents.add(button.dataset.event);renderEvents()});
  $$('.citation').forEach(button=>{button.setAttribute('aria-expanded','false');button.onclick=()=>showSource(Number(button.dataset.source)-1,button)});
  $$('.copy-result').forEach(button=>button.onclick=()=>copyResult(events.find(event=>event.kind==='answer')?.content||'',button));
}
function renderActivity(){
  const target=$('#activity');
  if(state.mode==='image'){
    if(state.imageStatus==='generating'){target.className='activity-card running';target.innerHTML='<strong><span class="spinner"></span>Creating your visual</strong><p>Bonsai is rendering locally. This usually takes about 15 seconds, and you can keep this window open.</p>';return}
    if(state.imageStatus==='failed'){target.className='activity-card failed';target.innerHTML=`<h2>Bonsai couldn’t finish this image</h2><p>Your description is still here. ${esc(state.imageError)}</p><div class="recovery-actions"><button id="retry-run" class="primary">Try again</button><button id="edit-request">Edit description</button></div>`;$('#retry-run').onclick=()=>$('#composer').requestSubmit();$('#edit-request').onclick=()=>$('#question').focus();requestAnimationFrame(()=>target.focus());return}
    if(state.currentImage){target.className='activity-card hidden';target.innerHTML='';return}
    target.className='activity-card idle';target.innerHTML='<span class="event-icon">✦</span><h2>Create in the conversation</h2><p>Describe an image below. It will appear here without switching tools or destinations.</p>';return
  }
  const stageCopy=state.mode==='html'?{queued:['Your page is in line','It will begin as soon as the local model is free.'],retrieving:['Shaping the direction','Bonsai is applying the layout, type, responsive, and accessibility guidance for this page.'],synthesizing:['Building your page','The local model is composing the page. This usually takes 30–45 seconds.'],validating:['Checking the result','Bonsai is checking the composition, responsiveness, accessibility, and completeness.'],checkpointing:['Preparing your preview','Saving this version so you can review it safely.']}:{queued:['Your question is in line','It will begin as soon as the local model is free.'],retrieving:['Finding the best sources','Bonsai is reading the strongest matching passages on this Mac.'],synthesizing:['Drafting your answer','Bonsai is writing from those sources and adding references.'],validating:['Checking the references','Every citation is being matched back to a real local source.'],checkpointing:['Saving this version','Your answer and its evidence are being kept together for review.']};
  if(state.machine.isRunning){const copy=stageCopy[state.machine.state];target.className='activity-card running';target.innerHTML=`<strong><span class="spinner"></span>${copy[0]}</strong><p>${copy[1]}</p>`;return}
  if(state.machine.state==='unreachable'){target.className='activity-card failed';target.innerHTML=`<h2>Harness connection interrupted</h2><p>${esc(state.machine.error?.message||'The browser could not reach the local server.')}</p><button id="retry-run" class="primary">Reconnect to this run</button>`;$('#retry-run').onclick=()=>pollJob(state.machine.jobId);return}
  if(state.machine.state==='failed'){target.className='activity-card failed';target.innerHTML=`<h2>Bonsai couldn’t finish this pass</h2><p>Your prompt and previous work are safe. ${esc(state.machine.error?.message||'The local model stopped before the result was ready.')}</p><div class="recovery-actions"><button id="retry-run" class="primary">Try again</button><button id="edit-request">Edit request</button></div>`;$('#retry-run').onclick=()=>$('#composer').requestSubmit();$('#edit-request').onclick=()=>$('#question').focus();requestAnimationFrame(()=>target.focus());return}
  if(state.currentRun){target.className='activity-card hidden';target.innerHTML='';return}
  if(document.body.classList.contains('prompting')){const copy={html:['▱','Start with a shape','Choose a page type below, or leave it on Custom and describe your own.'],text:['⌕','Ask it the way you would ask a person','You can narrow the source collection if you already know where the answer should come from.']}[state.mode];if(copy){target.className='activity-card prompt-help';target.innerHTML=`<span class="event-icon">${copy[0]}</span><h2>${copy[1]}</h2><p>${copy[2]}</p>`;return}}
  target.className='activity-card idle';target.innerHTML='<span class="event-icon">⌁</span><h2>No active run</h2><p>Choose a benchmark or describe a task below. Every result remains inspectable as an answer, evidence set, contract check, and human review.</p>';
}
function renderReview(){
  const run=state.currentRun;$('#review-panel').classList.toggle('hidden',!run||state.mode==='image');if(!run||state.mode==='image')return;
  $$('.verdict').forEach(button=>button.classList.toggle('selected',button.dataset.verdict===state.verdict));
  const pageIssueLabels={'functional-failure':'Something does not work','visual-fidelity':'Layout or visual style','accessibility':'Accessibility','responsive-regression':'Mobile layout','missing-tests':'Something is missing','scope-drift':'Content went off direction','runtime-failure':'The page did not finish'};
  $('#review-issues').innerHTML=state.reviewIssues.map(issue=>`<label><input type="checkbox" value="${esc(issue.id)}" ${(run.review?.issues||[]).includes(issue.id)?'checked':''}> ${esc(state.mode==='html'?(pageIssueLabels[issue.id]||issue.label):issue.label)}</label>`).join('');
  $('#review-details').classList.toggle('hidden',!['needs-work','fail'].includes(state.verdict));$('#review-note').value=run.review?.note||'';$('#save-review').disabled=!state.verdict;$('#save-review').textContent=state.verdict==='pass'?'Keep this version':state.verdict==='fail'?'Save and start again':'Save change request';$('#review-status').textContent=run.review?'Version saved. You can refine it or export it.':'';$('#toggle-run-details').textContent=state.detailsExpanded?'Hide run details':'Show run details';
}
function renderContext(){
  if(state.mode==='image'){const prompt=state.currentImage?.prompt||$('#question').value;const values=[['Prompt',estimatedTokens(prompt),'#385d87'],['Image',state.currentImage?1:0,'#315b42']];const total=values.reduce((sum,item)=>sum+item[1],0);$('#context-total').textContent=`${total} prompt units`;$('#context-bar').innerHTML=values.map(item=>`<i style="width:${total?Math.max(3,item[1]/total*100):0}%;background:${item[2]}"></i>`).join('');$('#context-legend').innerHTML=values.map(item=>`<div class="context-row"><i style="background:${item[2]}"></i><span>${item[0]}</span><code>${item[1]}</code></div>`).join('');return}
  const run=state.currentRun;const values=state.mode==='html'?[['Prompt',estimatedTokens(run?.question||$('#question').value),'#385d87'],['HTML',estimatedTokens(run?.answer),'#315b42']]:[['Question',estimatedTokens(run?.question),'#385d87'],['Answer',estimatedTokens(run?.answer),'#315b42'],['Evidence',estimatedTokens((run?.hits||[]).map(hit=>hit.text).join(' ')),'#a97823']];const total=values.reduce((sum,item)=>sum+item[1],0);$('#context-total').textContent=`${total.toLocaleString()} est. tokens`;
  $('#context-bar').innerHTML=values.map(item=>`<i style="width:${total?Math.max(3,item[1]/total*100):0}%;background:${item[2]}"></i>`).join('');
  $('#context-legend').innerHTML=values.map(item=>`<div class="context-row"><i style="background:${item[2]}"></i><span>${item[0]}</span><code>${item[1].toLocaleString()}</code></div>`).join('');
}
function renderAdapters(){
  const running=state.machine.isRunning||state.imageStatus==='generating';const adapters=state.status?.harness?.adapters||[];
  $('#adapters').innerHTML=adapters.map(adapter=>{const activeIds=state.mode==='image'?['image']:state.mode==='html'?['html']:['retrieval','synthesis'];const status=running&&activeIds.includes(adapter.id)?'running':adapter.status;return `<article class="adapter ${esc(status)}"><header><i></i><strong>${esc(adapter.name)}</strong><span>${esc(status)}</span></header><p>${esc(adapter.role)}</p></article>`}).join('');
}
function renderFiles(){
  if(state.mode==='image'){const image=state.currentImage;$('#source-count').textContent=image?'1':'';$('#workspace-files').innerHTML=image?`<div class="file-row"><b>IMG</b><span>${esc(image.filename)}</span><code>local</code></div>`:'<p class="muted" style="padding:10px">The generated image appears here.</p>';return}if(state.mode==='html'){const artifact=state.currentRun?.artifact;$('#source-count').textContent=artifact?'1':'';$('#workspace-files').innerHTML=artifact?`<div class="file-row"><b>HTML</b><span>${esc(artifact.filename)}</span><code>${artifact.bytes} B</code></div>`:'<p class="muted" style="padding:10px">The generated HTML file appears here.</p>';return}const hits=state.currentRun?.hits||[];$('#source-count').textContent=hits.length||'';$('#workspace-files').innerHTML=hits.length?hits.map((hit,index)=>`<div class="file-row" title="${esc(hit.path)}"><b>S${index+1}</b><span>${esc(fileName(hit.path))}</span><code>${esc(hit.corpus)}</code></div>`).join(''):'<p class="muted" style="padding:10px">Sources appear after a run.</p>';
}
function renderConfig(){
  const model=state.status?.harness?.adapters?.find(adapter=>adapter.id==='synthesis')?.name||'No text model';const index=state.status?.index;$('#harness-config').innerHTML=`<dl><div><dt>Model adapter</dt><dd>${esc(model)}</dd></div><div><dt>Retrieval</dt><dd>${index?`${index.chunks} chunks`:'index unavailable'}</dd></div><div><dt>Review store</dt><dd>SQLite</dd></div><div><dt>Image</dt><dd>${state.status?.image?.ready?'Bonsai local':'unavailable'}</dd></div></dl>`;
}
function renderComposerState(){const prompt=$('#question').value.trim();const busy=state.machine.isRunning||state.imageStatus==='generating';$('#run-case').disabled=!prompt||busy;$('#composer-error').textContent='';if(state.currentRun)$('#question').placeholder=state.mode==='html'?'Describe a change or ask Bonsai to create the next version…':'Ask a follow-up or give Bonsai the next step…';const hint=state.currentRun?(state.mode==='html'?'Describe one change to create another version. This version will stay saved.':'Continue from this answer. Its sources and this version will stay available.'):state.mode==='html'?'Choose a page shape or describe your own. First previews usually take 30–45 seconds.':state.mode==='image'?'Bonsai Image renders privately on this Mac, usually in about 15 seconds.':'Answers use your indexed local sources and keep their references.';$('#composer-hint').textContent=hint}
function renderAll(){renderDayZero();renderState();renderCases();renderRuns();renderHeader();renderPlan();renderEvents();renderActivity();renderReview();renderContext();renderAdapters();renderFiles();renderComposerState();updateAgentStart()}

async function pollJob(jobId){
  if(!jobId)return;
  const pollVersion=++state.pollVersion;
  let failures=0;
  while(true){
    await new Promise(resolve=>setTimeout(resolve,400));
    if(pollVersion!==state.pollVersion)return;
    let job;try{job=(await json(`/api/jobs/${jobId}`)).job;failures=0}catch(error){
      failures+=1;
      if(error.status===404||failures>=5){state.machine.transportFailure(error.status===404?'The server no longer has this job. Start a clean retry.':`The local server did not respond after ${failures} attempts. Your job ID is retained for recovery.`);renderAll();return}
      await new Promise(resolve=>setTimeout(resolve,Math.min(3000,failures*500)));continue
    }
    if(job.question&&!$('#question').value.trim())$('#question').value=job.question;
    try{state.machine.state==='unreachable'?state.machine.reconnect(job):state.machine.sync(job)}catch(error){state.machine.transportFailure(error.message);renderAll();return}
    renderAll();
    if(job.state==='awaiting_review'){clearActiveJob();state.detailsExpanded=false;state.currentRun=job.run;state.draftId=null;writeRoute(`/runs/${job.run.id}`,{replace:true});$('#question').value='';state.openEvents=new Set([job.run?.mode==='html'?'preview':'model']);await loadRuns();renderAll();requestAnimationFrame(()=>$('.primary-result .event-head')?.focus());return}
    if(job.state==='failed'){clearActiveJob();return}
  }
}
async function runTask(event){event.preventDefault();const question=$('#question').value.trim();if(!question){$('#composer-error').textContent='Describe what you want Bonsai to make first.';$('#question').focus();return}if(state.mode==='image')return generateImage();const corpus=state.mode==='html'?null:($('#corpus').value||null);const selectedMatches=state.selectedCase&&question.startsWith(state.selectedCase.question);state.currentRun=null;$('#run-case').disabled=true;try{const data=await json('/api/jobs',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({mode:state.mode,case_id:selectedMatches?state.selectedCase.id:null,question,corpus})});localStorage.setItem('bonsai-active-job',data.job.id);localStorage.setItem('bonsai-active-mode',state.mode);writeRoute(`/jobs/${data.job.id}`);state.machine.begin(data.job);renderAll();await pollJob(data.job.id)}catch(error){state.machine.transportFailure(error.message);renderAll()}finally{renderComposerState()}}
async function saveReview(){if(!state.currentRun||!state.verdict)return;const issues=$$('#review-issues input:checked').map(input=>input.value);$('#save-review').disabled=true;$('#review-status').textContent='Saving this decision…';try{const data=await json('/api/review',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({run_id:state.currentRun.id,verdict:state.verdict,issues,note:$('#review-note').value})});state.currentRun=data.run;state.machine.hydrateRun(true);await loadRuns();renderAll()}catch(error){$('#review-status').textContent=`Bonsai couldn’t save that yet. ${error.message}`}finally{$('#save-review').disabled=false}}
async function loadRuns(){const data=await json('/api/runs');state.runs=data.runs;renderRuns()}
async function generateImage(){const prompt=$('#question').value.trim();if(!prompt)return;saveDraft('prompt');const button=$('#run-case');state.currentRun=null;state.currentImage=null;state.imageStatus='generating';state.imageError=null;button.disabled=true;renderAll();try{state.currentImage=await json('/api/image',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({prompt,steps:2,size:'512x512'})});state.imageStatus='ready';state.openEvents=new Set(['image']);saveDraft('image')}catch(error){state.imageStatus='failed';state.imageError=error.message;saveDraft('prompt')}finally{button.disabled=false;renderAll()}}

async function applyRoute(){
  const version=++state.routeVersion;const route=routeFromLocation();state.pollVersion+=1;
  if(route.kind==='home'){newRun({updateUrl:false});return}
  if(route.kind==='draft'){
    const draft=loadDraft(route.id);if(!draft){writeRoute('/',{replace:true});newRun({updateUrl:false});$('#agent-start-error').textContent='That local draft is no longer available.';return}
    if(draft.surface==='home'){newRun({updateUrl:false});state.draftId=draft.id;$('#agent-request').value=draft.prompt||'';$('#agent-request').dataset.mode=draft.mode||'';renderAll();return}
    beginStarter(draft.mode||inferMode(draft.prompt),{updateUrl:false});state.draftId=draft.id;$('#question').value=draft.prompt||'';$('#corpus').value=draft.corpus||'';$('#page-type').value=draft.pageType||'custom';if(draft.surface==='image'&&draft.image){state.currentImage=draft.image;state.imageStatus='ready';state.openEvents=new Set(['image'])}renderAll();return
  }
  if(route.kind==='run'){
    try{const data=await json(`/api/runs/${route.id}`);if(version!==state.routeVersion)return;selectRun(data.run,{updateUrl:false})}catch(error){if(version!==state.routeVersion)return;writeRoute('/',{replace:true});newRun({updateUrl:false});$('#agent-start-error').textContent='That retained result could not be found.'}return
  }
  if(route.kind==='job'){
    try{const data=await json(`/api/jobs/${route.id}`);if(version!==state.routeVersion)return;const job=data.job;abandonPolling();state.draftId=null;state.dayZero=false;state.currentRun=null;state.currentImage=null;state.selectedCase=state.cases.find(item=>item.id===job.case_id)||null;setMode(job.kind==='html'?'html':'text');$('#question').value=job.question||'';$('#corpus').value=job.corpus||'';state.machine.begin(job);localStorage.setItem('bonsai-active-job',job.id);localStorage.setItem('bonsai-active-mode',state.mode);if(job.state==='awaiting_review'&&job.run){clearActiveJob();writeRoute(`/runs/${job.run.id}`,{replace:true});selectRun(job.run,{updateUrl:false});return}renderAll();if(state.machine.isRunning)pollJob(job.id)}catch(error){if(version!==state.routeVersion)return;state.machine.transportFailure(error.message);renderAll()}return
  }
  writeRoute('/',{replace:true});newRun({updateUrl:false})
}

async function boot(){
  const [status,catalog,presets,runs]=await Promise.all([json('/api/status'),json('/api/cases'),json('/api/page-presets'),json('/api/runs')]);state.status=status;state.cases=catalog.cases;state.pagePresets=presets.presets||[];state.reviewIssues=catalog.review_issues||[];state.runs=runs.runs;
  const ready=status.harness.ready;$('#runtime').classList.toggle('ready',ready);$('#runtime span').textContent=ready?'Ready on this Mac':'Runtime attention';renderConfig();renderCorpora();renderPagePresets();setMode(state.mode);renderAll();
  const activeJob=localStorage.getItem('bonsai-active-job');if(routeFromLocation().kind==='home'&&activeJob)writeRoute(`/jobs/${activeJob}`,{replace:true});await applyRoute()
}
$('#composer').onsubmit=runTask;$('#new-run').onclick=newRun;$('#refresh-runs').onclick=loadRuns;$('#save-review').onclick=saveReview;$('#request-mode').onchange=event=>{abandonPolling();setMode(event.target.value);state.currentRun=null;state.currentImage=null;state.imageStatus='idle';state.imageError=null;state.selectedCase=null;state.machine.reset(false);saveDraft('prompt');renderAll()};
$('#page-type').onchange=event=>{abandonPolling();event.target.value==='custom'?beginStarter('html'):applyPagePreset(event.target.value)};
$('#question').oninput=()=>{$('#composer-error').textContent='';if(!state.currentRun&&!state.machine.jobId)saveDraft('prompt');renderComposerState();if(['image','html'].includes(state.mode)){renderPlan();renderContext()}};
$$('.verdict').forEach(button=>button.onclick=()=>{state.verdict=button.dataset.verdict;$$('.verdict').forEach(item=>item.classList.toggle('selected',item===button));$('#review-status').textContent='';renderReview()});
$('#agent-start').onsubmit=startUniversalTask;
$('#agent-request').oninput=event=>{if(!event.isComposing)event.currentTarget.dataset.mode='';saveDraft('home');updateAgentStart()};
$$('[data-journey]').forEach(button=>button.onclick=()=>{const input=$('#agent-request');input.value=button.dataset.prompt;input.dataset.mode=button.dataset.mode;saveDraft('home');updateAgentStart();input.focus();input.setSelectionRange(input.value.length,input.value.length)});
$('#resume-latest').onclick=()=>{if(state.runs[0])selectRun(state.runs[0])};
$('#back-start').onclick=newRun;
$('#toggle-run-details').onclick=()=>{state.detailsExpanded=!state.detailsExpanded;renderAll();requestAnimationFrame(()=>$('#toggle-run-details').focus())};
window.addEventListener('popstate',applyRoute);
boot().catch(error=>{$('#runtime span').textContent=`Workbench unavailable: ${error.message}`;state.machine.transportFailure(error.message);renderState();renderPlan();renderActivity()});
