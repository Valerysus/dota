const test = require('node:test');
const assert = require('node:assert');
const { loadPureFunctions } = require('./helpers');
const fixtureMatch = require('./fixtures/match_9036473892.json');

test('B5: buildMacroScorecard function exists and handles empty/minimal input', () => {
  const pure = loadPureFunctions();
  assert.strictEqual(typeof pure.buildMacroScorecard, 'function');

  // Minimal input
  const res = pure.buildMacroScorecard({}, {}, { pos: 1, core: true });
  assert.ok(Array.isArray(res));
  assert.ok(res.length > 0);
  for (const item of res) {
    assert.ok(item.title, 'Scorecard item must have a title');
    assert.ok(item.text, 'Scorecard item must have text');
    assert.ok(['done', 'failed', 'warn', 'info'].includes(item.status), 'Valid status');
  }
});

test('B5: fixture evaluation on match 9036473892 - Arc Warden (winning Pos 2 core)', () => {
  const pure = loadPureFunctions();
  const aw = fixtureMatch.players.find(p => p.hero_id === 113);
  assert.ok(aw, 'Arc Warden player found');

  const scorecard = pure.buildMacroScorecard(aw, fixtureMatch, { pos: 2, core: true });
  assert.ok(Array.isArray(scorecard));
  assert.ok(scorecard.length >= 6);

  // Roshan: Dire team killed Roshan
  const rosh = scorecard.find(s => s.title.includes('Рошан'));
  assert.ok(rosh, 'Roshan item present');
  assert.strictEqual(rosh.status, 'done');

  // Tormentor: Dire team killed Tormentor
  const tor = scorecard.find(s => s.title.includes('Терзатель'));
  assert.ok(tor, 'Tormentor item present');
  assert.strictEqual(tor.status, 'done');

  // Tower push: 12161 tower damage + 5 towers killed
  const push = scorecard.find(s => s.title.includes('споруд'));
  assert.ok(push, 'Structure push item present');
  assert.strictEqual(push.status, 'done');
  assert.ok(push.text.includes('12'));

  // Farm tempo: 1023 GPM >= 600
  const farm = scorecard.find(s => s.title.includes('Темп фарму'));
  assert.ok(farm, 'Farm tempo item present');
  assert.strictEqual(farm.status, 'done');
  assert.ok(farm.title.includes('1023 GPM'));

  // Teamfight presence: 21 kills, 76% KP
  const fight = scorecard.find(s => s.title.includes('Бойова присутність'));
  assert.ok(fight, 'Fight presence item present');
  assert.strictEqual(fight.status, 'done');
  assert.ok(fight.text.includes('21'));

  // Runes: 13 runes picked up
  const runes = scorecard.find(s => s.title.includes('руні') || s.title.includes('рун'));
  assert.ok(runes, 'Runes item present');
  assert.strictEqual(runes.status, 'done');
});

test('B5: fixture evaluation on match 9036473892 - Slark (losing Pos 1 core)', () => {
  const pure = loadPureFunctions();
  const slark = fixtureMatch.players.find(p => p.hero_id === 93);
  assert.ok(slark, 'Slark player found');

  const scorecard = pure.buildMacroScorecard(slark, fixtureMatch, { pos: 1, core: true });
  assert.ok(Array.isArray(scorecard));

  // Roshan: Radiant lost Roshan to Dire
  const rosh = scorecard.find(s => s.title.includes('Рошан'));
  assert.ok(rosh, 'Roshan item present');
  assert.strictEqual(rosh.status, 'failed');

  // Tormentor: Radiant lost Tormentor
  const tor = scorecard.find(s => s.title.includes('Терзатель'));
  assert.ok(tor, 'Tormentor item present');
  assert.strictEqual(tor.status, 'failed');

  // Tower push: Slark had 0 tower damage
  const push = scorecard.find(s => s.title.includes('споруд'));
  assert.ok(push, 'Structure push item present');
  assert.strictEqual(push.status, 'failed');

  // Farm tempo: 436 GPM < 650 for Pos 1
  const farm = scorecard.find(s => s.title.includes('темпом фарму') || s.title.includes('Темп фарму'));
  assert.ok(farm, 'Farm tempo item present');
  assert.strictEqual(farm.status, 'failed');

  // Fight presence: 3 kills, low KP
  const fight = scorecard.find(s => s.title.includes('участь') || s.title.includes('Бойова присутність'));
  assert.ok(fight, 'Fight presence item present');
  assert.strictEqual(fight.status, 'failed');
});

test('B5: support role receives info for structure push instead of penalty', () => {
  const pure = loadPureFunctions();
  const ringmaster = fixtureMatch.players.find(p => p.hero_id === 131);
  assert.ok(ringmaster, 'Ringmaster player found');

  const scorecard = pure.buildMacroScorecard(ringmaster, fixtureMatch, { pos: 5, core: false });
  const push = scorecard.find(s => s.title.includes('споруд'));
  assert.ok(push, 'Structure push item present');
  // Support with 335 tower damage is informative, not marked as failed
  assert.notStrictEqual(push.status, 'failed');
});

test('B5: no forbidden characters or emojis in scorecard output', () => {
  const pure = loadPureFunctions();
  const aw = fixtureMatch.players.find(p => p.hero_id === 113);
  const scorecard = pure.buildMacroScorecard(aw, fixtureMatch, { pos: 2, core: true });
  const forbiddenRegex = /[\u{1F000}-\u{1FAFF}\u{2600}-\u{27BF}\u{2B00}-\u{2BFF}]/u;

  for (const item of scorecard) {
    assert.strictEqual(forbiddenRegex.test(item.title), false, `Forbidden char in title: ${item.title}`);
    assert.strictEqual(forbiddenRegex.test(item.text), false, `Forbidden char in text: ${item.text}`);
  }
});
