const test = require('node:test');
const assert = require('node:assert');
const { loadPureFunctions } = require('./helpers');
const fixtureMatch = require('./fixtures/match_9036473892.json');

test('B4: IMP thresholds and verdictFromImp', () => {
  const ctx = loadPureFunctions();
  assert.strictEqual(typeof ctx.verdictFromImp, 'function');
  assert.strictEqual(ctx.IMP_HI, 10);
  assert.strictEqual(ctx.IMP_LO, -10);

  // Decisive impact (IMP >= 10)
  assert.strictEqual(ctx.verdictFromImp({ imp: 25, kda: 5.0, soloDeaths: 0 }), 'Вирішальний внесок');
  assert.strictEqual(ctx.verdictFromImp({ imp: 10, kda: 3.0, soloDeaths: 1 }), 'Вирішальний внесок');

  // Stable play (0 <= IMP < 10)
  assert.strictEqual(ctx.verdictFromImp({ imp: 0, kda: 2.5, soloDeaths: 0 }), 'Стабільний відіграш');
  assert.strictEqual(ctx.verdictFromImp({ imp: 9, kda: 3.2, soloDeaths: 1 }), 'Стабільний відіграш');

  // Passive role (-10 < IMP < 0, soloDeaths < 3)
  assert.strictEqual(ctx.verdictFromImp({ imp: -1, kda: 2.0, soloDeaths: 0 }), 'Пасивна роль');
  assert.strictEqual(ctx.verdictFromImp({ imp: -9, kda: 1.5, soloDeaths: 2 }), 'Пасивна роль');

  // Critical drop (IMP <= -10 or (IMP < 0 && soloDeaths >= 3))
  assert.strictEqual(ctx.verdictFromImp({ imp: -10, kda: 1.0, soloDeaths: 0 }), 'Критичне просідання');
  assert.strictEqual(ctx.verdictFromImp({ imp: -15, kda: 0.8, soloDeaths: 1 }), 'Критичне просідання');
  assert.strictEqual(ctx.verdictFromImp({ imp: -3, kda: 1.2, soloDeaths: 3 }), 'Критичне просідання');
  assert.strictEqual(ctx.verdictFromImp({ imp: -1, kda: 1.0, soloDeaths: 5 }), 'Критичне просідання');
});

test('B4: filterMajorPurchases filters cheap items, recipes, consumables, and duplicates', () => {
  const ctx = loadPureFunctions();
  assert.strictEqual(typeof ctx.filterMajorPurchases, 'function');

  const mockItems = {
    tango: { cost: 90, qual: 'consumable' },
    flask: { cost: 100, qual: 'consumable' },
    boots: { cost: 500 },
    javelin: { cost: 900 },
    hand_of_midas: { cost: 2200 },
    yasha: { cost: 2050 },
    manta: { cost: 4600, components: ['yasha'] },
    recipe_manta: { cost: 650 },
    ninja_gear: { cost: 0, tier: 3 }
  };

  const sampleLog = [
    { key: 'tango', time: 10 },
    { key: 'boots', time: 180 },
    { key: 'javelin', time: 300 },
    { key: 'hand_of_midas', time: 360 },
    { key: 'yasha', time: 1200 },
    { key: 'recipe_manta', time: 1350 },
    { key: 'manta', time: 1400 },
    { key: 'ninja_gear', time: 1500 }
  ];

  const filtered = ctx.filterMajorPurchases(sampleLog, mockItems);
  const keys = filtered.map(x => x.key);

  // tango, boots, javelin (<1000) excluded
  assert.ok(!keys.includes('tango'));
  assert.ok(!keys.includes('boots'));
  assert.ok(!keys.includes('javelin'));
  // recipes excluded
  assert.ok(!keys.includes('recipe_manta'));
  // neutrals excluded
  assert.ok(!keys.includes('ninja_gear'));
  // Hand of Midas (2200 >= 1000) included
  assert.ok(keys.includes('hand_of_midas'));
  // Yasha excluded because upgraded to Manta at 1400 (diff = 200 <= 300)
  assert.ok(!keys.includes('yasha'));
  // Manta included
  assert.ok(keys.includes('manta'));
});

test('B4: fixture test on match 9036473892', () => {
  const ctx = loadPureFunctions();
  const aw = fixtureMatch.players.find(p => p.hero_id === 113); // Arc Warden
  assert.ok(aw, 'Arc Warden must exist in fixture');

  const mockCosts = {
    circlet: { cost: 155 },
    branches: { cost: 50 },
    tango: { cost: 90, qual: 'consumable' },
    faerie_fire: { cost: 65, qual: 'consumable' },
    gloves: { cost: 450 },
    flask: { cost: 100, qual: 'consumable' },
    hand_of_midas: { cost: 2200 },
    boots: { cost: 500 },
    clarity: { cost: 50, qual: 'consumable' },
    javelin: { cost: 900 },
    mithril_hammer: { cost: 1600 },
    tpscroll: { cost: 100, qual: 'consumable' },
    maelstrom: { cost: 2700 },
    smoke_of_deceit: { cost: 50, qual: 'consumable' },
    travel_boots: { cost: 2500 },
    hyperstone: { cost: 2000 },
    mjollnir: { cost: 5600 },
    blitz_knuckles: { cost: 1000 },
    sobi_mask: { cost: 175 },
    oblivion_staff: { cost: 1500 },
    robe: { cost: 450 },
    claymore: { cost: 1350 },
    orchid: { cost: 3475 },
    bloodthorn: { cost: 6800 },
    aghanims_shard: { cost: 1400 },
    blade_of_alacrity: { cost: 1000 },
    boots_of_elves: { cost: 450 },
    yasha: { cost: 2050 },
    diadem: { cost: 1000 },
    manta: { cost: 4600, components: ['yasha'] },
    orb_of_frost: { cost: 1000 },
    ultimate_orb: { cost: 2050 },
    skadi: { cost: 5300 }
  };

  const major = ctx.filterMajorPurchases(aw.purchase_log, mockCosts);
  const keys = major.map(x => x.key);

  // Major items present
  assert.ok(keys.includes('hand_of_midas'));
  assert.ok(keys.includes('maelstrom'));
  assert.ok(keys.includes('travel_boots'));
  assert.ok(keys.includes('mjollnir'));
  assert.ok(keys.includes('bloodthorn'));
  assert.ok(keys.includes('manta'));
  assert.ok(keys.includes('skadi'));

  // Yasha excluded due to Manta
  assert.ok(!keys.includes('yasha'));

  // Consumables and cheap items excluded
  assert.ok(!keys.includes('tango'));
  assert.ok(!keys.includes('clarity'));
  assert.ok(!keys.includes('tpscroll'));
  assert.ok(!keys.includes('boots'));
  assert.ok(!keys.includes('javelin'));

  // Arc Warden verdict check
  const awSoloDeaths = (aw.deaths_log || []).filter(d => ctx.classifyDeath(d.time, aw.player_slot, fixtureMatch.players) === 'Одиночна смерть поза позицією команди').length;
  // Arc Warden had high kills/gold, IMP is positive
  const verdictHigh = ctx.verdictFromImp({ imp: 49, kda: 5.8, soloDeaths: awSoloDeaths });
  assert.strictEqual(verdictHigh, 'Вирішальний внесок');

  // Slark (loss team, imp -2, 0 solo deaths)
  const verdictSlark = ctx.verdictFromImp({ imp: -2, kda: 2.8, soloDeaths: 0 });
  assert.strictEqual(verdictSlark, 'Пасивна роль');

  // Pudge (loss team, imp -10)
  const verdictPudge = ctx.verdictFromImp({ imp: -10, kda: 1.1, soloDeaths: 1 });
  assert.strictEqual(verdictPudge, 'Критичне просідання');
});
