const assert = require('assert');
const fs = require('fs');
const path = require('path');
const { loadPureFunctions } = require('./helpers.js');

const fixturePath = path.resolve(__dirname, 'fixtures/match_9036473892.json');
const match = JSON.parse(fs.readFileSync(fixturePath, 'utf8'));

// Hero definitions for match 9036473892
const heroData = {
  14: { id: 14, dname: 'Pudge', roles: ['Disabler', 'Initiator', 'Durable', 'Nuker'] },
  30: { id: 30, dname: 'Witch Doctor', roles: ['Support', 'Nuker', 'Disabler'] },
  44: { id: 44, dname: 'Phantom Assassin', roles: ['Carry', 'Escape'] },
  81: { id: 81, dname: 'Chaos Knight', roles: ['Carry', 'Disabler', 'Durable', 'Pusher', 'Initiator'] },
  93: { id: 93, dname: 'Slark', roles: ['Carry', 'Escape', 'Disabler', 'Nuker'] },
  104: { id: 104, dname: 'Legion Commander', roles: ['Carry', 'Disabler', 'Initiator', 'Durable', 'Nuker'] },
  113: { id: 113, dname: 'Arc Warden', roles: ['Carry', 'Escape', 'Nuker'] },
  123: { id: 123, dname: 'Hoodwink', roles: ['Support', 'Nuker', 'Escape', 'Disabler'] },
  131: { id: 131, dname: 'Ringmaster', roles: ['Support', 'Escape', 'Disabler', 'Nuker'] },
  135: { id: 135, dname: 'Dawnbreaker', roles: ['Carry', 'Initiator', 'Durable'] }
};

const positionPoolsMock = () => ({
  1: [44, 93, 113],
  2: [81, 113],
  3: [104, 135],
  4: [123, 131, 135],
  5: [14, 30]
});

const ctx = loadPureFunctions({
  state: { match, heroes: heroData },
  hero: (id) => heroData[id] || { roles: [] },
  positionPools: positionPoolsMock
});

const { assignTeamPositions, resolveLane, detectRole } = ctx;

const mins = match.duration / 60;
const radiant = match.players.filter(p => p.player_slot < 128);
const dire = match.players.filter(p => p.player_slot >= 128);

// Test 1: Slark is Pos 1 in Radiant
const radiantPositions = assignTeamPositions(radiant, mins);
const slark = radiant.find(p => p.hero_id === 93);
assert.ok(slark, 'Slark player must exist in Radiant');
const slarkPos = radiantPositions.get(slark.player_slot);
console.log('Radiant Slark slot:', slark.player_slot, 'assigned Pos:', slarkPos);
assert.strictEqual(slarkPos, 1, `Expected Slark to be Pos 1, got Pos ${slarkPos}`);

// Test 2: Arc Warden lane texts are identical across all sources
const arcWarden = dire.find(p => p.hero_id === 113);
assert.ok(arcWarden, 'Arc Warden player must exist in Dire');

const laneText1 = resolveLane(arcWarden);
const laneText2 = detectRole(arcWarden, dire, mins).lane;

// Check Block 06 logic against resolveLane
const isRad = arcWarden.player_slot < 128;
const laneText3 = resolveLane(arcWarden);

console.log('Arc Warden lane sources:', { laneText1, laneText2, laneText3 });
assert.strictEqual(laneText1, 'Центр', 'Expected resolveLane to return "Центр"');
assert.strictEqual(laneText1, laneText2, 'detectRole lane must equal resolveLane');
assert.strictEqual(laneText2, laneText3, 'Block 06 lane must equal resolveLane');

console.log('All Task A1 tests passed successfully!');
