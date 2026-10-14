const assert = require('assert');
const fs = require('fs');
const path = require('path');
const { loadPureFunctions } = require('./helpers.js');

const fixturePath = path.resolve(__dirname, 'fixtures/match_9036473892.json');
const match = JSON.parse(fs.readFileSync(fixturePath, 'utf8'));

const ctx = loadPureFunctions();
const { filterComponentItems } = ctx;

assert.strictEqual(typeof filterComponentItems, 'function', 'filterComponentItems must be defined and pure');

// Find Arc Warden (hero 113) in fixture
const arc = match.players.find(p => p.hero_id === 113);
assert.ok(arc, 'Arc Warden must exist in fixture');

const rawLog = arc.purchase_log || [];
const rawYasha = rawLog.find(e => e.key === 'yasha');
const rawManta = rawLog.find(e => e.key === 'manta');

assert.ok(rawYasha, 'Raw purchase log must have Yasha');
assert.ok(rawManta, 'Raw purchase log must have Manta');
assert.strictEqual(rawYasha.time, 1498, 'Yasha should be at 24:58 (1498s)');
assert.strictEqual(rawManta.time, 1697, 'Manta should be at 28:17 (1697s)');

// Filter items
const filteredLog = filterComponentItems(rawLog);

// 1. Yasha (component upgraded within 300s / after 1080s) must be excluded
const filteredYasha = filteredLog.find(e => e.key === 'yasha');
assert.strictEqual(filteredYasha, undefined, 'Yasha (24:58) must be filtered out as component of Manta');

// 2. Manta must remain in filteredLog for norm checking
const filteredManta = filteredLog.find(e => e.key === 'manta');
assert.ok(filteredManta, 'Manta (28:17) must remain in filtered log');
assert.strictEqual(filteredManta.time, 1697, 'Manta time should be preserved');

// 3. Early independent Yasha test: Yasha at 10:00 (600s), no Manta or Manta at 30:00
const independentLog = [
  { key: 'yasha', time: 600 },
  { key: 'manta', time: 1800 }
];
const filteredIndependent = filterComponentItems(independentLog);
assert.strictEqual(filteredIndependent.length, 2, 'Independent early Yasha (tc <= 1080 and dt > 300) should NOT be filtered out');

console.log('All Task A2 tests passed successfully!');
