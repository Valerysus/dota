const fs = require('fs');
const path = require('path');
const vm = require('vm');

/**
 * Extracts and evaluates all blocks between // @pure-start and // @pure-end
 * from index.html in an isolated node:vm context with necessary stubs.
 */
function loadPureFunctions(customContext = {}) {
  const htmlPath = path.resolve(__dirname, '../index.html');
  const html = fs.readFileSync(htmlPath, 'utf8');

  const matches = [...html.matchAll(/\/\/\s*@pure-start([\s\S]*?)\/\/\s*@pure-end/g)];
  if (!matches.length) {
    throw new Error('No pure code blocks found between // @pure-start and // @pure-end in index.html');
  }

  const code = matches.map(m => m[1]).join('\n;\n');

  const defaultContext = {
    console,
    Math,
    Map,
    Set,
    Array,
    Object,
    Number,
    String,
    Boolean,
    RegExp,
    state: { match: null, heroes: {}, items: {}, itemById: {} },
    hero: (id) => ({ roles: [] }),
    positionPools: () => ({ 1: [], 2: [], 3: [], 4: [], 5: [] }),
    getWardsData: (p) => ({ obs: 0, sen: 0, total: 0 }),
    POS_NAMES: {
      1: 'Pos 1 · Carry',
      2: 'Pos 2 · Mid',
      3: 'Pos 3 · Offlane',
      4: 'Pos 4 · Soft Support',
      5: 'Pos 5 · Hard Support'
    },
    LANE_NAMES: {
      1: 'Легка лінія',
      2: 'Центр',
      3: 'Складна лінія',
      4: 'Ліс'
    },
    IMP_HI: 10,
    IMP_LO: -10,
    ...customContext
  };

  const context = vm.createContext(defaultContext);
  vm.runInContext(code, context);

  return context;
}

module.exports = {
  loadPureFunctions
};
