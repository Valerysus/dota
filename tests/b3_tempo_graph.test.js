const assert = require('assert');
const fs = require('fs');
const path = require('path');
const { loadPureFunctions } = require('./helpers.js');

const fixturePath = path.resolve(__dirname, 'fixtures/match_9036473892.json');
const match = JSON.parse(fs.readFileSync(fixturePath, 'utf8'));

const ctx = loadPureFunctions();
const { calcDeathCost } = ctx;

assert.strictEqual(typeof calcDeathCost, 'function', 'calcDeathCost must be defined');

const maxMins = Math.floor(match.duration / 60);

// Test 1: Radiant player (player_slot 0) death cost
// Death at t = 1288 (min 21): adv[23] - adv[21]
const costRad = calcDeathCost(1288, 0, match.radiant_gold_adv, maxMins);
console.log('Radiant player death cost at 1288s:', costRad);
assert.strictEqual(costRad, -3531, 'Radiant death cost should be -3531');

// Test 2: Dire player (Arc Warden, player_slot 129) death cost
// Death at t = 672 (min 11): (-adv[13]) - (-adv[11])
const costDire = calcDeathCost(672, 129, match.radiant_gold_adv, maxMins);
console.log('Dire Arc Warden death cost at 672s:', costDire);
assert.strictEqual(costDire, -2559, 'Dire death cost should be -2559');

// Test 3: index.html markup check for accessibility and data attributes
const htmlPath = path.resolve(__dirname, '../index.html');
const html = fs.readFileSync(htmlPath, 'utf8');

assert.ok(html.includes('class="graph-death-dot"'), 'index.html must contain graph-death-dot class');
assert.ok(html.includes('tabindex="0"'), 'index.html must include tabindex="0" for accessibility');
assert.ok(html.includes('Смерть, хвилина'), 'index.html must contain aria-label definition with "Смерть, хвилина"');
assert.ok(html.includes('Ціна:'), 'index.html must contain 2-min cost label');

console.log('All Task B3 tests passed successfully!');
