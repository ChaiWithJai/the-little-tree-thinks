(function(root){
  const SERVER_STATES=['queued','retrieving','synthesizing','validating','checkpointing','awaiting_review','failed'];
  const RUNNING_STATES=new Set(['queued','retrieving','synthesizing','validating','checkpointing']);
  const ALLOWED={
    queued:new Set(['retrieving','failed']),
    retrieving:new Set(['synthesizing','validating','failed']),
    synthesizing:new Set(['validating','failed']),
    validating:new Set(['checkpointing','failed']),
    checkpointing:new Set(['awaiting_review','failed']),
    awaiting_review:new Set(),failed:new Set(),
  };
  const STAGE_INDEX={queued:1,retrieving:1,synthesizing:2,validating:3,checkpointing:4,awaiting_review:5};
  const PILL_STATES=[
    ['idle','Idle'],['queued','Queued'],['retrieving','Retrieve'],['synthesizing','Synthesize'],
    ['validating','Validate'],['awaiting_review','Review'],['retained','Retained'],['failed','Failed'],
  ];

  class BonsaiRunMachine{
    constructor(){this.state='idle';this.jobId=null;this.seenEvents=0;this.error=null;this.failedStage=null}
    reset(hasCase=false){this.state=hasCase?'ready':'idle';this.jobId=null;this.seenEvents=0;this.error=null;this.failedStage=null}
    begin(job){this.jobId=job.id;this.state='queued';this.seenEvents=1;this.error=null;this.failedStage=null;this.sync(job)}
    sync(job){
      if(!job||!SERVER_STATES.includes(job.state))throw new Error(`Unknown server run state: ${job?.state}`);
      if(this.jobId!==job.id)this.begin(job);
      const events=job.events||[];
      for(const event of events.slice(this.seenEvents))this.transition(event.state);
      this.seenEvents=events.length;this.error=job.error;this.failedStage=job.failed_stage;
      if(this.state!==job.state)throw new Error(`Run state drift: client=${this.state}, server=${job.state}`);
    }
    transition(next){
      if(next===this.state)return;
      if(!ALLOWED[this.state]?.has(next))throw new Error(`Illegal run transition: ${this.state} -> ${next}`);
      this.state=next;
    }
    transportFailure(message){this.state='unreachable';this.error={kind:'TransportError',message,retryable:true};this.failedStage='transport'}
    reconnect(job){this.state='queued';this.jobId=job.id;this.seenEvents=1;this.error=null;this.failedStage=null;this.sync(job)}
    hydrateRun(reviewed){this.state=reviewed?'retained':'awaiting_review';this.jobId=null;this.seenEvents=0;this.error=null;this.failedStage=null}
    get isRunning(){return RUNNING_STATES.has(this.state)}
    pills(){return PILL_STATES.map(([key,label])=>({key,label,active:key===this.state||(key==='failed'&&this.state==='unreachable')}))}
    planStatuses(length){
      if(this.state==='idle'||this.state==='ready')return Array.from({length},(_,index)=>this.state==='ready'&&index===0?'done':'pending');
      if(this.state==='retained')return Array(length).fill('done');
      if(this.state==='unreachable')return Array.from({length},(_,index)=>index===0?'done':'pending');
      const failedAt=this.state==='failed'?(STAGE_INDEX[this.failedStage]??1):null;
      const activeAt=failedAt??STAGE_INDEX[this.state]??0;
      return Array.from({length},(_,index)=>index<activeAt?'done':index===activeAt?(failedAt!==null?'blocked':'active'):'pending');
    }
  }

  const api={BonsaiRunMachine,SERVER_STATES,RUNNING_STATES};
  root.BonsaiFSM=api;
  if(typeof module!=='undefined'&&module.exports)module.exports=api;
})(typeof globalThis!=='undefined'?globalThis:this);
