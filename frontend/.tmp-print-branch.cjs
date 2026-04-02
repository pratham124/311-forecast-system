const coverage = require('./coverage/coverage-final.json');

const file = '/Users/sahmed/Documents/capstone/311-forecast-system/frontend/src/features/historical-demand/hooks/useHistoricalDemand.ts';
const entry = coverage[file];

if (!entry) {
  console.log('File not found in coverage report');
  process.exit(1);
}

for (const [id, branch] of Object.entries(entry.branchMap)) {
  const hits = entry.b[id];
  const line = (branch.locations && branch.locations[0] && branch.locations[0].start.line)
    || (branch.loc && branch.loc.start.line)
    || -1;
  console.log(`id=${id} line=${line} hits=${JSON.stringify(hits)} type=${branch.type}`);
}
