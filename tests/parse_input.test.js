const assert = require('assert');

/* ======================= Розпізнавання ID ======================= */
function parseInput(raw) {
  const s = String(raw || '').trim();
  if (!s) return null;

  // 1. Посилання на матч
  const mUrl = s.match(/(?:matches|match)\/(\d+)/i);
  if (mUrl) return { type: 'match', id: mUrl[1] };

  // 2. Посилання на гравця
  const pUrl = s.match(/(?:players|profiles|id)\/(\d+)/i);
  if (pUrl) {
    if (pUrl[1].length === 17) {
      try {
        const a32 = (BigInt(pUrl[1]) - BigInt('76561197960265728')).toString();
        return { type: 'player', id: a32 };
      } catch {}
    }
    return { type: 'player', id: pUrl[1] };
  }

  // 3. SteamID64 (17 цифр)
  if (/^7656119\d{10}$/.test(s)) {
    try {
      const a32 = (BigInt(s) - BigInt('76561197960265728')).toString();
      return { type: 'player', id: a32 };
    } catch {}
  }

  // 4. Числові ідентифікатори
  // Сучасні Match ID у Dota 2 мають 10 цифр і починаються з 7, 8, 9 (напр. 9044569588)
  // Нові Steam32 акаунти з 10 цифр починаються з 1 (напр. 1737356567, 1011832947)
  if (/^[789]\d{9}$/.test(s)) {
    return { type: 'match', id: s, fallbackType: 'player' };
  }

  // Старіші матчі (9 цифр) або стандартні Steam32 акаунти (до 10 цифр)
  if (/^\d{5,10}$/.test(s)) {
    return { type: 'player', id: s, fallbackType: 'match' };
  }

  return null;
}

// Case 1: '9044569588' -> {type:'match', fallbackType:'player'}
const c1 = parseInput('9044569588');
assert.strictEqual(c1.type, 'match');
assert.strictEqual(c1.id, '9044569588');
assert.strictEqual(c1.fallbackType, 'player');
console.log('✓ Case 1 passed: 9044569588 -> match (fallback player)');

// Case 2: '94054712' -> {type:'player', fallbackType:'match'}
const c2 = parseInput('94054712');
assert.strictEqual(c2.type, 'player');
assert.strictEqual(c2.id, '94054712');
assert.strictEqual(c2.fallbackType, 'match');
console.log('✓ Case 2 passed: 94054712 -> player (fallback match)');

// Case 3: '76561198054320440' -> {type:'player', id:'94054712'}
const c3 = parseInput('76561198054320440');
assert.strictEqual(c3.type, 'player');
assert.strictEqual(c3.id, '94054712');
console.log('✓ Case 3 passed: 76561198054320440 -> player 94054712');

// Case 4: 'https://www.opendota.com/matches/9044569588' -> {type:'match', id:'9044569588'}
const c4 = parseInput('https://www.opendota.com/matches/9044569588');
assert.strictEqual(c4.type, 'match');
assert.strictEqual(c4.id, '9044569588');
console.log('✓ Case 4 passed: https://www.opendota.com/matches/9044569588 -> match 9044569588');

// Case 5: '' -> null
const c5 = parseInput('');
assert.strictEqual(c5, null);
console.log('✓ Case 5 passed: empty string -> null');

console.log('\nAll parseInput tests passed successfully!');
