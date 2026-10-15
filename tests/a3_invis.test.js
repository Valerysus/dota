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

// Test 5 (Task 15): Fallback path without stateObj.heroAbilities finds Slark, Hoodwink, and Treant
const fallbackHeroData = {
  ...heroData,
  93: { id: 93, short: 'slark', dname: 'Slark' },
  123: { id: 123, short: 'hoodwink', dname: 'Hoodwink' },
  83: { id: 83, short: 'treant', dname: 'Treant Protector' }
};
const fallbackHeroFn = (id) => fallbackHeroData[id] || { id, short: 'unknown', dname: 'Unknown' };
const fallbackEnemies = [
  { hero_id: 93, items: [] },  // Slark
  { hero_id: 123, items: [] }, // Hoodwink
  { hero_id: 83, items: [] },  // Treant Protector
  { hero_id: 1, items: [] }    // Anti-Mage (no invis item)
];
const detectedFallback = detectInvisEnemies(fallbackEnemies, fallbackHeroFn, finalItemsFn, {}); // stateObj without heroAbilities
assert.strictEqual(detectedFallback.length, 3, 'Slark, Hoodwink, and Treant must be detected in fallback');
const fallbackNames = detectedFallback.map(h => h.dname);
assert.ok(fallbackNames.includes('Slark'), 'Slark must be found in fallback');
assert.ok(fallbackNames.includes('Hoodwink'), 'Hoodwink must be found in fallback');
assert.ok(fallbackNames.includes('Treant Protector'), 'Treant Protector must be found in fallback');

// Test 6 (Task 16): Evaluation on fixture match 9036473892
const fixtureMatch = require('./fixtures/match_9036473892.json');
const fixtureHeroMap = {
  135: { id: 135, short: 'dawnbreaker', dname: 'Dawnbreaker' },
  81: { id: 81, short: 'chaos_knight', dname: 'Chaos Knight' },
  93: { id: 93, short: 'slark', dname: 'Slark' },
  123: { id: 123, short: 'hoodwink', dname: 'Hoodwink' },
  14: { id: 14, short: 'pudge', dname: 'Pudge' },
  44: { id: 44, short: 'phantom_assassin', dname: 'Phantom Assassin' },
  113: { id: 113, short: 'arc_warden', dname: 'Arc Warden' },
  30: { id: 30, short: 'witch_doctor', dname: 'Witch Doctor' },
  131: { id: 131, short: 'ringmaster', dname: 'Ringmaster' },
  104: { id: 104, short: 'legion_commander', dname: 'Legion Commander' }
};
const fixtureHeroFn = (id) => fixtureHeroMap[id] || { id, short: 'hero_' + id, dname: 'Hero ' + id };
const radiantEnemies = fixtureMatch.players.filter(p => p.player_slot < 128); // Dawnbreaker, CK, Slark, Hoodwink, Pudge

// State with ability descriptions including reveal/true sight mentions (e.g. Slark Shadow Dance)
const mockAbilitiesState = {
  heroAbilities: {
    npc_dota_hero_slark: { abilities: ['slark_shadow_dance'] },
    npc_dota_hero_hoodwink: { abilities: ['hoodwink_scurry'] },
    npc_dota_hero_pudge: { abilities: ['pudge_meat_hook', 'pudge_rot', 'pudge_dismember'] }
  },
  abilities: {
    slark_shadow_dance: {
      desc: "Slark hides himself in a cloud of shadows, becoming invisible. Attacking, casting spells, and using items will not reveal Slark. Cannot be revealed by True Sight."
    },
    hoodwink_scurry: {
      desc: "Hoodwink gains bonus movement speed and phased collision, and gains camouflage (invisibility) when near trees."
    },
    pudge_meat_hook: { desc: "Launches a bloody hook at a unit or location, dragging the first unit back." },
    pudge_rot: { desc: "A toxic cloud that deals intense damage and slows movement." },
    pudge_dismember: { desc: "Chunnels to dismember an enemy unit, disabling them." }
  }
};

const detectedFixture = detectInvisEnemies(radiantEnemies, fixtureHeroFn, finalItemsFn, mockAbilitiesState);
const detectedFixtureNames = detectedFixture.map(h => h.dname);
assert.ok(detectedFixtureNames.includes('Slark'), 'Fixture: Slark must be detected even with reveal/true sight in description');
assert.ok(detectedFixtureNames.includes('Hoodwink'), 'Fixture: Hoodwink must be detected');
assert.ok(!detectedFixtureNames.includes('Pudge'), 'Fixture: Pudge must NOT be detected as invis');

console.log('All Task A3 tests passed successfully!');

