const assert = require('node:assert/strict');
const {BonsaiRunMachine} = require('../web/fsm.js');

const active = new BonsaiRunMachine();
active.begin({
  id: 'job-1',
  state: 'synthesizing',
  events: [{state: 'queued'}, {state: 'retrieving'}, {state: 'synthesizing'}],
  error: null,
  failed_stage: null,
});
assert.equal(active.state, 'synthesizing');
assert.deepEqual(active.planStatuses(6), ['done', 'done', 'active', 'pending', 'pending', 'pending']);

const noEvidence = new BonsaiRunMachine();
noEvidence.begin({
  id: 'job-2',
  state: 'awaiting_review',
  events: [{state: 'queued'}, {state: 'retrieving'}, {state: 'validating'}, {state: 'checkpointing'}, {state: 'awaiting_review'}],
  error: null,
  failed_stage: null,
});
assert.equal(noEvidence.state, 'awaiting_review');
assert.deepEqual(noEvidence.planStatuses(6), ['done', 'done', 'done', 'done', 'done', 'active']);

const disconnected = new BonsaiRunMachine();
disconnected.reset(true);
disconnected.transportFailure('Failed to fetch');
assert.equal(disconnected.state, 'unreachable');
assert.deepEqual(disconnected.planStatuses(6), ['done', 'pending', 'pending', 'pending', 'pending', 'pending']);
disconnected.reconnect({
  id: 'job-recovered', state: 'failed', failed_stage: 'synthesizing',
  error: {kind: 'ProcessRestart', message: 'restarted', retryable: true},
  events: [{state: 'queued'}, {state: 'retrieving'}, {state: 'synthesizing'}, {state: 'failed'}],
});
assert.equal(disconnected.state, 'failed');
assert.deepEqual(disconnected.planStatuses(6), ['done', 'done', 'blocked', 'pending', 'pending', 'pending']);

assert.throws(() => {
  const invalid = new BonsaiRunMachine();
  invalid.begin({id: 'bad', state: 'validating', events: [{state: 'queued'}, {state: 'validating'}]});
}, /Illegal run transition/);

console.log('frontend FSM tests passed');
