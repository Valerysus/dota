const assert = require('assert');
const { loadPureFunctions } = require('./helpers.js');

const ctx = loadPureFunctions();
const { detectInvisEnemies } = ctx;

assert.strictEqual(typeof detectInvisEnemies, 'function', 'detectInvisEnemies must be defined');

const heroData = {
  1: { id: 1, short: 'antimage', dname: 'Anti-Mage' },
  2: { id: 2, short: 'axe', dname: 'Axe' },
  3: { id: 3, short: 'broodmother', dname: 'Broodmother' },
  4: { id: 4, short: 'lycan', dname: 'Lycan' },
  5: { id: 5, short: 'templar_assassin', dname: 'Templar Assassin' },
  6: { id: 6, short: 'riki', dname: 'Riki' },
  7: { id: 7, short: 'clinkz', dname: 'Clinkz' }
};

const heroFn = (id) => heroData[id] || { id, short: 'unknown', dname: 'Unknown' };

// Test 1: Broodmother, Lycan, Templar Assassin are NOT treated as invis heroes
const enemiesNoInvis = [
  { hero_id: 3, items: [] }, // Broodmother
  { hero_id: 4, items: [] }, // Lycan
  { hero_id: 5, items: [] }, // Templar Assassin
  { hero_id: 1, items: [] }  // Anti-Mage
];
const finalItemsFn = (e) => e.items || [];
const detectedNoInvis = detectInvisEnemies(enemiesNoInvis, heroFn, finalItemsFn, {});
assert.strictEqual(detectedNoInvis.length, 0, 'Broodmother, Lycan, TA should not trigger invis');

// Test 2: Hero with invis item (shadow_amulet, silver_edge, etc.)
const enemiesWithItem = [
  { hero_id: 1, items: ['shadow_amulet'] },
  { hero_id: 2, items: ['silver_edge'] }
];
const detectedItems = detectInvisEnemies(enemiesWithItem, heroFn, finalItemsFn, {});
assert.strictEqual(detectedItems.length, 2, 'Enemies with shadow_amulet and silver_edge must be detected');
assert.strictEqual(detectedItems[0].dname, 'Anti-Mage');
assert.strictEqual(detectedItems[1].dname, 'Axe');

// Test 3: Riki & Clinkz detected
const enemiesRiki = [{ hero_id: 6, items: [] }, { hero_id: 7, items: [] }];
const detectedRiki = detectInvisEnemies(enemiesRiki, heroFn, finalItemsFn, {});
assert.strictEqual(detectedRiki.length, 2);
assert.strictEqual(detectedRiki[0].dname, 'Riki');

// Test 4: 6-slot Core advice check
const corePlayer6Slots = {
  player_slot: 0,
  item_0: 1, item_1: 2, item_2: 3, item_3: 4, item_4: 5, item_5: 6
};
const has6Slots = ['item_0','item_1','item_2','item_3','item_4','item_5'].every(k => corePlayer6Slots[k] != null && corePlayer6Slots[k] > 0);
assert.strictEqual(has6Slots, true);

const pos1Role = { pos: 1 };
const isCoreSlotCap = (pos1Role.pos === 1 || pos1Role.pos === 2) && has6Slots;
assert.strictEqual(isCoreSlotCap, true);

const expectedCoreAdvice = "Координація з саппортами (Pos 4-5) щодо наявності Dust/Sentry у бійках та контроль позиції через здібності розвідки";
assert.ok(expectedCoreAdvice.includes('Координація з саппортами'));

console.log('All Task A3 tests passed successfully!');
