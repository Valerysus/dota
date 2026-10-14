const test = require('node:test');
const assert = require('node:assert');
const { loadPureFunctions } = require('./helpers');
const fixtureMatch = require('./fixtures/match_9036473892.json');

test('A5: buildActionPlan priority ordering and no-fallback rule', () => {
  const ctxPure = loadPureFunctions();
  assert.strictEqual(typeof ctxPure.buildActionPlan, 'function');

  // Case 1: Core with BKB death, low tower damage, solo deaths >= 2, and low LH@10
  const ctxFull = {
    p: {
      player_slot: 2,
      hero_id: 93,
      purchase_log: [{ key: 'boots', time: 100 }],
      lh_t: { 10: 30 },
      obs_placed: 0,
      sen_placed: 0
    },
    role: { pos: 1, core: true },
    detailedDeaths: [
      { time: 1000, killer: {} } // >900s, core without BKB -> Window without BKB
    ],
    bm: { tower_damage: { pct: 0.25 } }, // <40%
    soloDeaths: 3, // >=2
    mins: 35
  };

  const tasksFull = ctxPure.buildActionPlan(ctxFull);
  // Priority 1: BKB, Priority 2: Tower damage, Priority 3: Solo deaths (max 3 items returned)
  assert.strictEqual(tasksFull.length, 3);
  assert.strictEqual(tasksFull[0].topic, 'bkb');
  assert.strictEqual(tasksFull[1].topic, 'tower_damage');
  assert.strictEqual(tasksFull[2].topic, 'solo_deaths');

  // Case 2: Only 1 issue (e.g. low tower damage only). Must NOT pad with templates!
  const ctxSingle = {
    p: {
      player_slot: 129,
      hero_id: 113,
      purchase_log: [{ key: 'black_king_bar', time: 800 }],
      lh_t: { 10: 70 },
      obs_placed: 2,
      sen_placed: 0
    },
    role: { pos: 2, core: true },
    detailedDeaths: [{ time: 1000 }], // has BKB, so no BKB window death
    bm: { tower_damage: { pct: 0.30 } }, // <40%
    soloDeaths: 0,
    mins: 35
  };

  const tasksSingle = ctxPure.buildActionPlan(ctxSingle);
  // Only tower damage should be present, total length 1, no templates padded
  assert.strictEqual(tasksSingle.length, 1);
  assert.strictEqual(tasksSingle[0].topic, 'tower_damage');

  // Case 3: LH@10 condition: added ONLY if lh_at_10 < target_lh
  const ctxLhPass = {
    p: {
      player_slot: 0,
      hero_id: 1,
      purchase_log: [{ key: 'black_king_bar', time: 700 }],
      lh_t: { 10: 65 } // target for pos 1 is 60 -> passes!
    },
    role: { pos: 1, core: true },
    detailedDeaths: [],
    bm: { tower_damage: { pct: 0.80 } },
    soloDeaths: 0,
    mins: 30
  };
  const tasksLhPass = ctxPure.buildActionPlan(ctxLhPass);
  assert.ok(!tasksLhPass.some(t => t.topic === 'lh10'), 'LH10 should NOT be added when lh10 >= target');

  const ctxLhFail = {
    p: {
      player_slot: 0,
      hero_id: 1,
      purchase_log: [{ key: 'black_king_bar', time: 700 }],
      lh_t: { 10: 45 } // target for pos 1 is 60 -> fails!
    },
    role: { pos: 1, core: true },
    detailedDeaths: [],
    bm: { tower_damage: { pct: 0.80 } },
    soloDeaths: 0,
    mins: 30
  };
  const tasksLhFail = ctxPure.buildActionPlan(ctxLhFail);
  assert.ok(tasksLhFail.some(t => t.topic === 'lh10'), 'LH10 should be added when lh10 < target');
});

test('A5: fixture evaluation on match 9036473892', () => {
  const ctxPure = loadPureFunctions();
  const rad = fixtureMatch.players.filter(p => p.player_slot < 128);
  const dire = fixtureMatch.players.filter(p => p.player_slot >= 128);
  const mins = fixtureMatch.duration / 60;

  // Slark (loss core, hero_id 93)
  const slark = fixtureMatch.players.find(p => p.hero_id === 93);
  const slarkRole = ctxPure.detectRole(slark, rad, mins);
  const slarkDeaths = (slark.deaths_log || []).map(d => ({ time: d.time }));
  const slarkSoloDeaths = (slark.deaths_log || []).filter(d => ctxPure.classifyDeath(d.time, slark.player_slot, fixtureMatch.players) === 'Одиночна смерть поза позицією команди').length;
  const slarkCtx = {
    p: slark,
    role: slarkRole,
    detailedDeaths: slarkDeaths,
    bm: slark.benchmarks,
    soloDeaths: slarkSoloDeaths,
    mins
  };

  const slarkPlan = ctxPure.buildActionPlan(slarkCtx);
  // Slark: died >900s without BKB (Priority 1), tower damage pct 15.1% < 40% (Priority 2), LH10 52 < 60 (Priority 5)
  assert.strictEqual(slarkPlan[0].topic, 'bkb');
  assert.strictEqual(slarkPlan[1].topic, 'tower_damage');
  assert.strictEqual(slarkPlan[2].topic, 'lh10');

  // Arc Warden (winner core, hero_id 113)
  const aw = fixtureMatch.players.find(p => p.hero_id === 113);
  const awRole = ctxPure.detectRole(aw, dire, mins);
  const awDeaths = (aw.deaths_log || []).map(d => ({ time: d.time }));
  const awSoloDeaths = (aw.deaths_log || []).filter(d => ctxPure.classifyDeath(d.time, aw.player_slot, fixtureMatch.players) === 'Одиночна смерть поза позицією команди').length;
  const awCtx = {
    p: aw,
    role: awRole,
    detailedDeaths: awDeaths,
    bm: aw.benchmarks,
    soloDeaths: awSoloDeaths,
    mins
  };

  const awPlan = ctxPure.buildActionPlan(awCtx);
  // AW has TD pct 75.6% (>=40%), 1 death at 672s (<900s), soloDeaths 1 (<2), LH10 65 (>=55).
  // There are fewer than 3 candidates (in fact, 0 built-in candidates). It must NOT pad with 3 templates!
  assert.ok(awPlan.length < 3, 'Arc Warden plan should not be padded with filler templates');
});
