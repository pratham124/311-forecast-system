#!/usr/bin/env node
/**
 * Post-run check: every PNG in test-results/ui-smoke is non-trivial size (not blank/error stub).
 * Writes evaluation-report.json next to the screenshots. Exit 1 if any file missing or too small.
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const shotDir = path.join(__dirname, '..', 'test-results', 'ui-smoke');
const minBytes = Number(process.env.E2E_MIN_SCREENSHOT_BYTES ?? '4096');

const expectedPrefixes = [
  '01-entry',
  '02-forecasts-initial',
  '03-forecasts-weekly-window',
  '10-demand-comparisons',
  '04-historical-initial',
  '05-historical-dates-changed',
  '06-historical-after-submit',
  '11-evaluations',
  '07-ingestion-page',
  '09-back-to-forecasts',
];

function main() {
  const report = { ok: true, shotDir, minBytes, steps: [], missing: [] };

  if (!fs.existsSync(shotDir)) {
    console.error(`evaluate-run: directory missing: ${shotDir} (run Playwright first)`);
    process.exit(1);
  }

  for (const base of expectedPrefixes) {
    const file = `${base}.png`;
    const full = path.join(shotDir, file);
    if (!fs.existsSync(full)) {
      report.missing.push(file);
      report.ok = false;
      continue;
    }
    const st = fs.statSync(full);
    const stepOk = st.size >= minBytes;
    report.steps.push({ file, bytes: st.size, ok: stepOk });
    if (!stepOk) report.ok = false;
  }

  const extras = fs
    .readdirSync(shotDir)
    .filter((f) => f.endsWith('.png') && !expectedPrefixes.some((p) => f === `${p}.png`));
  for (const file of extras.sort()) {
    const full = path.join(shotDir, file);
    const st = fs.statSync(full);
    report.steps.push({ file, bytes: st.size, ok: st.size >= minBytes, extra: true });
  }

  const outPath = path.join(shotDir, 'evaluation-report.json');
  fs.writeFileSync(outPath, `${JSON.stringify(report, null, 2)}\n`);
  console.log(JSON.stringify(report, null, 2));
  if (report.missing.length) {
    console.error('evaluate-run: missing expected screenshots:', report.missing.join(', '));
  }
  process.exit(report.ok ? 0 : 1);
}

main();
