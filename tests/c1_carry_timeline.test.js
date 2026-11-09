const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { loadPureFunctions } = require('./helpers.js');

const ctx = loadPureFunctions();
const { buildCarryTimelineData, scoreCarryTimeline } = ctx;
assert.equal(typeof buildCarryTimelineData, 'function');
assert.equal(typeof scoreCarryTimeline, 'function');

const player = {
  player_slot: 0,
  lh_t: [0, 3, 6, 8, 11, 13, 16, 20, 24, 28, 33, 38],
  purchase_log: [
    { time: 600, key: 'bfury' },
    { time: 700, key: 'bfury' }
  ],
  kills_log: [{ time: 720, key: 'npc_dota_hero_pudge' }],
  deaths_log: [{ time: 900, key: 'npc_dota_hero_pudge' }],
  runes_log: [{ time: 400, key: '5' }],
  obs_log: [{ time: 500, x: 1, y: 1 }],
  sen_log: [],
  camps_stacked_t: [],
  objectives: []
};
const match = {
  duration: 1200,
  players: [player],
  objectives: [
    { time: 800, type: 'CHAT_MESSAGE_ROSHAN_KILL', player_slot: 0 },
    { time: 850, type: 'building_kill', player_slot: 0, key: 'npc_dota_goodguys_tower1_top' }
  ]
};
const events = buildCarryTimelineData(player, match, {
  coreTimings: { bfury: [870, 'розгін фарму'] },
  itemName: key => key === 'bfury' ? 'Battle Fury' : key,
  heroName: key => key,
  classifyDeath: () => 'Одиночна смерть поза позицією команди'
});

assert.equal(events.map(event => event.time).join(','), [...events.map(event => event.time)].sort((a, b) => a - b).join(','));
assert.equal(events.filter(event => event.title === 'Battle Fury').length, 1, 'duplicate core item purchases are grouped');
assert.ok(events.some(event => event.kind === 'Фарм'));
assert.ok(events.some(event => event.kind === 'Бійка' && event.grade === 'good'));
assert.ok(events.some(event => event.kind === 'Смерть' && event.grade === 'mistake'));
assert.ok(events.some(event => event.kind === 'Руна' && event.grade === 'neutral'));
assert.ok(events.some(event => event.kind === 'Огляд' && event.grade === 'neutral'));
assert.ok(events.some(event => event.title === 'Участь у вбивстві Рошана'));
assert.ok(events.some(event => event.title === 'Знесено споруду'));
assert.ok(events.every(event => event.fact && event.coach && event.confidence), 'every move separates telemetry from coach interpretation');
assert.ok(events.some(event => Number.isFinite(event.scoreValue)), 'decision events carry a numeric score contribution');
assert.ok(events.some(event => event.scoreValue === null), 'neutral events do not affect the score');

const scorecard = scoreCarryTimeline(events);
assert.ok(scorecard.score >= 0 && scorecard.score <= 100);
assert.ok(scorecard.parts.some(part => part.name === 'Фарм'));
assert.ok(scorecard.parts.some(part => part.name === 'Предмети'));
assert.ok(scorecard.parts.some(part => part.name === 'Дисципліна'));
assert.equal(scoreCarryTimeline([{ grade: 'good' }]).score, null, 'unscored facts do not fabricate an overall grade');
assert.equal(scoreCarryTimeline([{ scoreCategory: 'Фарм', scoreValue: 1 }]).score, 75, 'single-category score is normalized from neutral 50');

const fixture = JSON.parse(fs.readFileSync(path.resolve(__dirname, 'fixtures/match_9036473892.json'), 'utf8'));
const fixturePlayer = fixture.players.find(p => p.player_slot === 2);
const fixtureEvents = buildCarryTimelineData(fixturePlayer, fixture, {
  coreTimings: {},
  classifyDeath: () => 'Одиночна смерть поза позицією команди'
});
assert.ok(fixtureEvents.length > 0, 'demo match telemetry produces timeline events');
assert.ok(fixtureEvents.every(event => event.time >= 0 && event.time <= fixture.duration));

console.log('All C1 carry decision timeline tests passed successfully!');
