const assert = require('node:assert/strict');
const { loadPureFunctions } = require('./helpers.js');

const ctx = loadPureFunctions();
const { farmScore, itemScore, disciplineScore, impactScore, scoreStrict, scoreCarryTimeline } = ctx;

for (const [name, fn] of Object.entries({ farmScore, itemScore, disciplineScore, impactScore, scoreStrict, scoreCarryTimeline })) {
  assert.equal(typeof fn, 'function', `${name} is exported from the pure block`);
}

/* ---------- farmScore ---------- */

assert.equal(farmScore([]), null, 'no farm segments means no farm score');
assert.equal(farmScore([1.4, 1.4, 1.4, 1.4]), 100, 'every segment at the upper bound scores 100');
assert.equal(farmScore([0.7, 0.7, 0.7, 0.7]), 0, 'every segment at the lower bound scores 0');
assert.equal(farmScore([1.05, 1.05, 1.05, 1.05]), 50, 'midpoint of the bounds scores 50');
assert.ok(farmScore([1.4, 1.4, 1.4, 0.7]) < farmScore([1.4, 1.4, 1.4, 1.05]), 'the worst segments drag the score down');
assert.equal(farmScore([2.5, 2.5, 2.5, 2.5]), 100, 'segments above the upper bound are clamped, not rewarded');

/* ---------- itemScore ---------- */

assert.equal(itemScore([0, 0]), null, 'fewer than three items is not rated');
assert.equal(itemScore([-200, -200, -200]), 100, 'items bought well before the benchmark score 100');
assert.equal(itemScore([0, 0, 0]), 60, 'items exactly on the benchmark score 60');
assert.equal(itemScore([420, 420, 420]), 0, 'items at the late bound score 0');
assert.ok(itemScore([-100, -100, -100]) > itemScore([100, 100, 100]), 'earlier purchases score higher');

/* ---------- disciplineScore ---------- */

assert.equal(disciplineScore({ deaths: 1, solo: 0, objLoss: 0, lateNoBkb: 0, durationMin: 34 }), 100, 'one death in 34 minutes is within the ideal');
assert.equal(disciplineScore({ deaths: 2, solo: 0, objLoss: 0, lateNoBkb: 0, durationMin: 34 }), 85, 'each death over the ideal costs 15');
assert.equal(disciplineScore({ deaths: 3, solo: 0, objLoss: 0, lateNoBkb: 0, durationMin: 34 }), 70, 'two deaths over the ideal cost 30');
assert.equal(disciplineScore({ deaths: 1, solo: 1, objLoss: 0, lateNoBkb: 0, durationMin: 34 }), 85, 'a solo death costs 15');
assert.equal(disciplineScore({ deaths: 1, solo: 0, objLoss: 1, lateNoBkb: 0, durationMin: 34 }), 90, 'losing a tower costs 10');
assert.equal(disciplineScore({ deaths: 1, solo: 0, objLoss: 0, lateNoBkb: 1, durationMin: 34 }), 90, 'a late death without BKB costs 10');
assert.equal(disciplineScore({ deaths: 40, solo: 5, objLoss: 5, lateNoBkb: 5, durationMin: 34 }), 0, 'discipline clamps at zero');

/* ---------- impactScore ---------- */

assert.equal(impactScore({ towerPct: null, kp: 0.5 }), null, 'missing tower percentile means no impact score');
assert.equal(impactScore({ towerPct: 0.5, kp: null }), null, 'missing kill participation means no impact score');
assert.equal(impactScore({ towerPct: 0.95, kp: 0.75 }), 100, 'top tower damage and kill participation score 100');
assert.equal(impactScore({ towerPct: 0.5, kp: 0.35 }), 0, 'baseline tower damage and kill participation score 0');

/* ---------- scoreStrict ---------- */

assert.equal(scoreStrict({}, {}).score, null, 'no categories means no score');
assert.equal(scoreStrict({}, {}).label, 'Ще немає даних');

const reference = scoreStrict(
  { farm: 100, items: 100, discipline: 100, impact: 100 },
  { episodes: 12, solo: 0, deaths: 1, ideal: 1, win: true }
);
assert.equal(reference.score, 100, 'a flawless winning game scores 100');
assert.equal(reference.label, 'Еталонна гра');
assert.equal(reference.caps.length, 0, 'a flawless game has no caps');

const soloCap = scoreStrict(
  { farm: 100, items: 100, discipline: 100, impact: 100 },
  { episodes: 12, solo: 1, deaths: 1, ideal: 1, win: true }
);
assert.ok(soloCap.score <= 89, 'a solo death caps the score at 89');
assert.ok(soloCap.caps.some(([name]) => name === 'Є соло-смерть'));

const lossCap = scoreStrict(
  { farm: 100, items: 100, discipline: 100, impact: 100 },
  { episodes: 12, solo: 0, deaths: 1, ideal: 1, win: false }
);
assert.ok(lossCap.score <= 94, 'a loss caps the score at 94');
assert.ok(lossCap.caps.some(([name]) => name === 'Поразка'));

const fewData = scoreStrict({ farm: 90 }, { episodes: 2, solo: 0, deaths: 0, ideal: 1, win: true });
assert.ok(fewData.score <= 85, 'too few categories caps the score at 85');
assert.ok(fewData.label.startsWith('Попередня оцінка:'), 'a capped score is labelled as preliminary');

const lowCategory = scoreStrict(
  { farm: 30, items: 100, discipline: 100, impact: 100 },
  { episodes: 12, solo: 0, deaths: 1, ideal: 1, win: true }
);
assert.ok(lowCategory.score <= 69, 'a category below 40 caps the score at 69');

/* ---------- scoreCarryTimeline ---------- */

const farmEvents = ratios => ratios.map((ratio, i) => ({ time: (i + 1) * 300, kind: 'Фарм', scoreValue: ratio, deviation: Math.round(ratio * 100) - 100 }));
const itemEvents = deltas => deltas.map((delta, i) => ({ time: 600 + i * 60, kind: 'Предмет', delta }));
const deathEvents = (count, extra = {}) => Array.from({ length: count }, (_, i) => ({ time: 600 + i * 60, kind: 'Смерть', ...extra }));
const impactEvent = (towerPct, kp, win) => ({ time: 2040, kind: 'Вплив', towerPct, kp, win });

const perfect = scoreCarryTimeline([
  ...farmEvents([1.44, 1.81, 1.40, 1.83, 1.65, 1.55]),
  ...itemEvents([-200, -200, -200]),
  ...deathEvents(1),
  impactEvent(0.97, 0.8, true)
]);
assert.equal(perfect.score, 100, 'the reference game scores 100');
assert.equal(perfect.label, 'Еталонна гра');

const screenshot = scoreCarryTimeline([
  ...farmEvents([1.44, 1.81, 1.40, 1.83, 0.65, 0.88]),
  ...deathEvents(4),
  { time: 2040, kind: 'Вплив', towerPct: null, kp: null, win: true }
]);
assert.ok(screenshot.score >= 50 && screenshot.score <= 58, `screenshot match scores 50..58, got ${screenshot.score}`);
assert.equal(screenshot.label, 'Попередня оцінка: Посередня гра');
assert.ok(screenshot.parts.find(part => part.key === 'items').score == null, 'items are not rated without three purchases');
assert.ok(screenshot.parts.find(part => part.key === 'impact').score == null, 'impact is not rated without benchmarks');

const onPar = scoreCarryTimeline([
  ...farmEvents([1, 1, 1, 1, 1, 1]),
  ...itemEvents([0, 0, 0]),
  ...deathEvents(3),
  impactEvent(0.5, 0.55, true)
]);
assert.ok(onPar.score >= 48 && onPar.score <= 54, `an average game scores 48..54, got ${onPar.score}`);

const withSolo = scoreCarryTimeline([
  ...farmEvents([1.44, 1.81, 1.40, 1.83, 1.65, 1.55]),
  ...itemEvents([-200, -200, -200]),
  ...deathEvents(1, { solo: true }),
  impactEvent(0.97, 0.8, true)
]);
assert.ok(withSolo.score <= 89, 'a solo death caps the timeline score at 89');

const loss = scoreCarryTimeline([
  ...farmEvents([1.44, 1.81, 1.40, 1.83, 1.65, 1.55]),
  ...itemEvents([-200, -200, -200]),
  ...deathEvents(1),
  impactEvent(0.97, 0.8, false)
]);
assert.ok(loss.score <= 94, 'a loss caps the timeline score at 94');

assert.equal(scoreCarryTimeline([]).score, null, 'an empty timeline has no score');
assert.equal(scoreCarryTimeline([{ kind: 'Руна', time: 300 }]).score, null, 'neutral facts alone do not produce a score');

console.log('All C2 strict score tests passed successfully!');
