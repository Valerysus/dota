const assert = require('assert');
const { loadPureFunctions } = require('./helpers.js');

const ctx = loadPureFunctions();
const { formatAccountAudit } = ctx;

assert.strictEqual(typeof formatAccountAudit, 'function', 'formatAccountAudit must be defined');

// 1. Private / empty / failed returns null
assert.strictEqual(formatAccountAudit(null), null);
assert.strictEqual(formatAccountAudit({}), null);
assert.strictEqual(formatAccountAudit({ win: 0, lose: 0 }), null);

// 2. High winrate with small history (30 <= N < 400, WR > 56%)
const sampleHighWr = { win: 120, lose: 60 }; // N = 180, WR = 67%
const audit1 = formatAccountAudit(sampleHighWr);
assert.ok(audit1);
assert.strictEqual(audit1.games, 180);
assert.strictEqual(audit1.winrate, 67);
assert.strictEqual(audit1.line, 'Усього ігор: 180 · Вінрейт: 67%');
assert.strictEqual(audit1.note, 'Малий обсяг історії при високому вінрейті. Це не доказ, перевірте профіль.');

// Forbidden words check: no "смурф" and no "підтверджено"
assert.strictEqual(/смурф/i.test(audit1.note), false, 'Must not contain "смурф"');
assert.strictEqual(/підтверджено/i.test(audit1.note), false, 'Must not contain "підтверджено"');

// 3. Established account with large history (N >= 400): no note
const sampleLargeHistory = { win: 600, lose: 300 }; // N = 900, WR = 67%
const audit2 = formatAccountAudit(sampleLargeHistory);
assert.ok(audit2);
assert.strictEqual(audit2.line, 'Усього ігор: 900 · Вінрейт: 67%');
assert.strictEqual(audit2.note, null, 'No note should be shown for N >= 400');

// 4. Low winrate (WR <= 56%): no note
const sampleLowWr = { win: 100, lose: 100 }; // N = 200, WR = 50%
const audit3 = formatAccountAudit(sampleLowWr);
assert.ok(audit3);
assert.strictEqual(audit3.line, 'Усього ігор: 200 · Вінрейт: 50%');
assert.strictEqual(audit3.note, null, 'No note should be shown for WR <= 56%');

console.log('All Task A4 tests passed successfully!');
