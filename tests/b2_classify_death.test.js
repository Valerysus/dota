const assert = require('assert');
const fs = require('fs');
const path = require('path');
const { loadPureFunctions } = require('./helpers.js');

const fixturePath = path.resolve(__dirname, 'fixtures/match_9036473892.json');
const match = JSON.parse(fs.readFileSync(fixturePath, 'utf8'));

const ctx = loadPureFunctions();
const { classifyDeath, getMapConsequence } = ctx;

assert.strictEqual(typeof classifyDeath, 'function', 'classifyDeath must be defined');
assert.strictEqual(typeof getMapConsequence, 'function', 'getMapConsequence must be defined');

// 1. Test classifyDeath on fixture: Ringmaster (slot 131)
const ringmaster = match.players.find(p => p.player_slot === 131);
assert.ok(ringmaster, 'Ringmaster should be in match');
const ringDeaths = ringmaster.deaths_log || [];
const soloDeathsRing = ringDeaths.filter(d => classifyDeath(d.time, ringmaster.player_slot, match.players) === 'Одиночна смерть поза позицією команди').length;
console.log('Ringmaster total deaths:', ringDeaths.length, 'solo deaths:', soloDeathsRing);
assert.strictEqual(soloDeathsRing, 5, 'Ringmaster should have 5 solo deaths');

// 2. Test classifyDeath synthetic test
const mockPlayers = [
  {
    player_slot: 0,
    deaths_log: [{ time: 100 }],
    kills_log: []
  },
  {
    player_slot: 1,
    deaths_log: [{ time: 110 }],
    kills_log: []
  }
];
// At time 100, ally died at 110 (diff = 10s <= 20s) -> team fight
assert.strictEqual(classifyDeath(100, 0, mockPlayers), 'Командна сутичка');

// At time 300, no ally deaths and no team kills in [280, 320] -> solo death
assert.strictEqual(classifyDeath(300, 0, mockPlayers), 'Одиночна смерть поза позицією команди');

// 3. Test getMapConsequence on fixture
// Player 0 died at 1288, radiant tower fell at 1289 (dt = 1)
const consTower = getMapConsequence(1288, 0, match.objectives);
console.log('Player 0 map consequence at 1288:', consTower);
assert.strictEqual(consTower, 'Наслідок на карті: втрата вежі через 1 с після смерті');

// Player 3 died at 2046, throne fell at 2054 (dt = 8)
const consThrone = getMapConsequence(2046, 3, match.objectives);
console.log('Player 3 map consequence at 2046:', consThrone);
assert.strictEqual(consThrone, 'Наслідок на карті: втрата трону через 8 с після смерті');

// Death with no map consequences in [t, t+60]
const consNone = getMapConsequence(100, 0, match.objectives);
assert.strictEqual(consNone, null);

console.log('All Tasks B1 & B2 tests passed successfully!');
