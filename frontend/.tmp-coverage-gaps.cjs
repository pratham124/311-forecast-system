const fs = require('fs');

const coveragePath = '/Users/sahmed/Documents/capstone/311-forecast-system/frontend/coverage/coverage-final.json';
const report = JSON.parse(fs.readFileSync(coveragePath, 'utf8'));

function percentage(covered, total) {
  return total === 0 ? 100 : (covered / total) * 100;
}

for (const [filePath, coverage] of Object.entries(report)) {
  const statementEntries = Object.entries(coverage.s || {});
  const functionEntries = Object.entries(coverage.f || {});
  const branchEntries = Object.entries(coverage.b || {});

  const coveredStatements = statementEntries.filter(([, hits]) => hits > 0).length;
  const statementPct = percentage(coveredStatements, statementEntries.length);

  const coveredFunctions = functionEntries.filter(([, hits]) => hits > 0).length;
  const functionPct = percentage(coveredFunctions, functionEntries.length);

  const allBranchHits = branchEntries.flatMap(([, hits]) => hits);
  const coveredBranches = allBranchHits.filter((hits) => hits > 0).length;
  const branchPct = percentage(coveredBranches, allBranchHits.length);

  const lineHitMap = new Map();
  for (const [id, hits] of statementEntries) {
    const line = coverage.statementMap?.[id]?.start?.line;
    if (!line) continue;
    const existing = lineHitMap.get(line) || 0;
    lineHitMap.set(line, Math.max(existing, hits));
  }
  const coveredLines = Array.from(lineHitMap.values()).filter((hits) => hits > 0).length;
  const linePct = percentage(coveredLines, lineHitMap.size);

  if (statementPct === 100 && functionPct === 100 && branchPct === 100 && linePct === 100) {
    continue;
  }

  const missingStatementLines = [...new Set(
    statementEntries
      .filter(([, hits]) => hits === 0)
      .map(([id]) => coverage.statementMap?.[id]?.start?.line)
      .filter(Boolean),
  )].sort((a, b) => a - b);

  const missingFunctions = functionEntries
    .filter(([, hits]) => hits === 0)
    .map(([id]) => {
      const name = coverage.fnMap?.[id]?.name ?? '(anonymous)';
      const line = coverage.fnMap?.[id]?.decl?.start?.line;
      return line ? `${name}@${line}` : null;
    })
    .filter(Boolean);

  const missingBranchLines = [];
  for (const [id, hits] of branchEntries) {
    hits.forEach((count, idx) => {
      if (count > 0) return;
      const location = coverage.branchMap?.[id]?.locations?.[idx] || coverage.branchMap?.[id]?.loc;
      const line = location?.start?.line;
      if (line) missingBranchLines.push(line);
    });
  }
  const uniqueMissingBranchLines = [...new Set(missingBranchLines)].sort((a, b) => a - b);

  console.log(filePath);
  console.log(
    `  pct statements=${statementPct.toFixed(2)} branches=${branchPct.toFixed(2)} functions=${functionPct.toFixed(2)} lines=${linePct.toFixed(2)}`,
  );
  if (missingStatementLines.length) {
    console.log(`  missing statements: ${missingStatementLines.join(',')}`);
  }
  if (missingFunctions.length) {
    console.log(`  missing functions: ${missingFunctions.join(',')}`);
  }
  if (uniqueMissingBranchLines.length) {
    console.log(`  missing branches: ${uniqueMissingBranchLines.join(',')}`);
  }
}
