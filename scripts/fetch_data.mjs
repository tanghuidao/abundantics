/**
 * fetch_data.mjs
 *
 * Pulls CSV data from tanghuidao/token-parity repo and converts to latest.json.
 * This script ONLY converts — it never computes index values.
 *
 * If the fetch fails, it preserves existing latest.json and history.csv
 * and logs a warning. If no existing data is found, it generates MOCK data.
 *
 * Usage: node scripts/fetch_data.mjs
 */

import fs from 'node:fs';
import path from 'node:path';

const REPO_OWNER = 'tanghuidao';
const REPO_NAME = 'token-parity';
const BRANCH = 'main';
const OUTPUT_DIR = path.resolve(process.cwd(), 'public/api/parity');

// --- Utility functions ---

function parseCSV(csvText) {
  const lines = csvText.trim().split('\n').filter((l) => l.trim());
  if (lines.length === 0) return { headers: [], rows: [] };
  const headers = lines[0].split(',').map((h) => h.trim());
  const rows = lines.slice(1).map((line) => {
    const values = line.split(',').map((v) => v.trim());
    const obj = {};
    headers.forEach((h, i) => { obj[h] = values[i] ?? ''; });
    return obj;
  });
  return { headers, rows };
}

function safeParseFloat(v) {
  if (!v || v === '' || v === 'null' || v === 'NaN') return null;
  const n = parseFloat(v);
  return isNaN(n) ? null : n;
}

function formatFloat(n, decimals = 3) {
  if (n === null) return null;
  return parseFloat(n.toFixed(decimals));
}

// --- Core logic ---

async function fetchText(url) {
  try {
    const res = await fetch(url);
    if (res.ok) return await res.text();
    throw new Error(`HTTP ${res.status}`);
  } catch (err) {
    // Fallback to curl. Helps in sandboxed/local environments where Node's
    // DNS resolution is blocked but system tooling can still reach the network.
    // On GitHub Actions the primary fetch path is used and this rarely triggers.
    const { execFileSync } = await import('node:child_process');
    const out = execFileSync('curl', ['-sS', '--max-time', '30', '-L', url], {
      encoding: 'utf-8',
      stdio: ['ignore', 'pipe', 'pipe'],
    });
    if (!out) throw new Error(`curl returned empty body (${err.message})`);
    return out;
  }
}

async function fetchRemoteCSV() {
  // Try multiple possible CSV paths in the token-parity repo
  // parity_series.csv is the canonical main series (verified 2026-08-19)
  const possiblePaths = [
    'parity_series.csv',
    'history.csv',
    'data/history.csv',
    'output/history.csv',
    'tepi_history.csv',
    'data/tepi_history.csv',
  ];

  for (const csvPath of possiblePaths) {
    const url = `https://raw.githubusercontent.com/${REPO_OWNER}/${REPO_NAME}/${BRANCH}/${csvPath}`;
    try {
      console.log(`[fetch_data] Trying ${url}...`);
      const text = await fetchText(url);
      console.log(`[fetch_data] Successfully fetched ${text.split('\n').length} lines from ${csvPath}`);
      return text;
    } catch (err) {
      console.log(`[fetch_data] Failed to fetch from ${csvPath}: ${err.message}`);
    }
  }

  throw new Error('Could not fetch CSV from any known path in token-parity repo');
}

function convertToLatest(historyRows) {
  // Sort by date descending
  const sorted = [...historyRows].sort((a, b) => b.date.localeCompare(a.date));
  const latest = sorted[0];
  const prev = sorted[1];

  if (!latest) throw new Error('No data rows in history');

  const changeOr = (curr, prevVal) => {
    if (curr === null || prevVal === null) return null;
    const dec = Math.abs(curr) < 1 || Math.abs(prevVal) < 1 ? 4 : 3;
    return parseFloat((curr - prevVal).toFixed(dec));
  };

  return {
    schema_version: '1.0',
    method_version: latest.method_version || '0.1',
    date: latest.date,
    generated_at: new Date().toISOString().replace(/\.\d+Z$/, 'Z'),
    indices: {
      R_M: {
        value: formatFloat(latest.R_M, 4),
        unit: 'USD/kWh',
        change_1d: changeOr(latest.R_M, prev?.R_M ?? null),
      },
      R_A: {
        value: formatFloat(latest.R_A, 2),
        unit: 'USD/kWh',
        change_1d: changeOr(latest.R_A, prev?.R_A ?? null),
      },
      Lambda: {
        value: formatFloat(latest.Lambda, 1),
        unit: 'dimensionless',
        change_1d: changeOr(latest.Lambda, prev?.Lambda ?? null),
      },
      Omega: {
        value: formatFloat(latest.Omega, 2),
        unit: 'dimensionless',
        change_1d: changeOr(latest.Omega, prev?.Omega ?? null),
      },
    },
    sources: [`${REPO_OWNER}/${REPO_NAME}`],
    license: 'CC-BY-4.0',
  };
}

function generateMockHistory(days = 120) {
  const rows = [];
  const today = new Date();
  today.setUTCHours(0, 0, 0, 0);

  // Use deterministic seed for reproducibility
  let seed = 42;
  function rand() {
    seed = (seed * 9301 + 49297) % 233280;
    return seed / 233280;
  }

  let lambda = 218.0;
  let omega = 5.5;
  let rM = 0.064;
  let rA = 15.0;

  for (let i = days - 1; i >= 0; i--) {
    const date = new Date(today);
    date.setUTCDate(date.getUTCDate() - i);
    const dateStr = date.toISOString().slice(0, 10);

    // Random walk with slight upward trend for Lambda
    lambda += (rand() - 0.45) * 1.2;
    omega += (rand() - 0.48) * 0.05;
    rM += (rand() - 0.5) * 0.002;
    rA += (rand() - 0.5) * 0.15;

    rows.push({
      date: dateStr,
      R_M: parseFloat(rM.toFixed(4)),
      R_A: parseFloat(rA.toFixed(2)),
      Lambda: parseFloat(lambda.toFixed(1)),
      Omega: parseFloat(omega.toFixed(2)),
      Lambda_chained: parseFloat(lambda.toFixed(1)),
      method_version: '0.1',
    });
  }

  return rows;
}

function rowsToCSV(rows) {
  if (rows.length === 0) return '';
  const headers = ['date', 'R_M', 'R_A', 'Lambda', 'Omega', 'Lambda_chained', 'method_version'];
  const lines = [headers.join(',')];
  for (const row of rows) {
    lines.push(headers.map((h) => row[h] ?? '').join(','));
  }
  return lines.join('\n') + '\n';
}

function ensureOutputDir() {
  if (!fs.existsSync(OUTPUT_DIR)) {
    fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  }
}

function writeData(latestJson, historyCSV) {
  ensureOutputDir();
  const latestPath = path.join(OUTPUT_DIR, 'latest.json');
  const historyPath = path.join(OUTPUT_DIR, 'history.csv');
  fs.writeFileSync(latestPath, JSON.stringify(latestJson, null, 2) + '\n', 'utf-8');
  fs.writeFileSync(historyPath, historyCSV, 'utf-8');
  console.log(`[fetch_data] Wrote ${latestPath}`);
  console.log(`[fetch_data] Wrote ${historyPath}`);
}

// --- Main ---

async function main() {
  console.log('[fetch_data] Starting data fetch...');

  // Check if existing data exists (for fallback)
  const existingLatestPath = path.join(OUTPUT_DIR, 'latest.json');
  const existingHistoryPath = path.join(OUTPUT_DIR, 'history.csv');
  const hasExisting = fs.existsSync(existingLatestPath) && fs.existsSync(existingHistoryPath);

  try {
    // Attempt to fetch from token-parity repo
    const csvText = await fetchRemoteCSV();
    const { rows } = parseCSV(csvText);

    // Normalize column names (handle possible variations)
    const normalizedRows = rows.map((r) => ({
      date: r.date || r.Date || r.DATE,
      R_M: safeParseFloat(r.R_M ?? r.rm ?? r.RM),
      R_A: safeParseFloat(r.R_A ?? r.ra ?? r.RA),
      Lambda: safeParseFloat(r.Lambda ?? r.lambda ?? r.Λ ?? r.L),
      Omega: safeParseFloat(r.Omega ?? r.omega ?? r.Ω ?? r.O),
      Lambda_chained: safeParseFloat(r.Lambda_chained ?? r.lambda_chained ?? r.Lambda),
      method_version: r.method_version || r.methodVersion || '0.1',
    })).filter((r) => r.date);

    if (normalizedRows.length === 0) {
      throw new Error('No valid data rows found in fetched CSV');
    }

    // Generate latest.json from the most recent row
    const latestJson = convertToLatest(normalizedRows);

    // Generate history.csv with standardized columns
    const historyCSV = rowsToCSV(normalizedRows);

    writeData(latestJson, historyCSV);
    console.log('[fetch_data] ✅ Successfully updated data from token-parity repo.');
  } catch (err) {
    console.warn(`[fetch_data] ⚠️  Fetch failed: ${err.message}`);

    if (hasExisting) {
      console.warn('[fetch_data] ⚠️  Preserving existing latest.json and history.csv.');
      console.warn('[fetch_data] ⚠️  DATA IS STALE — please check token-parity repo.');
    } else {
      console.warn('[fetch_data] ⚠️  No existing data found. Generating MOCK data...');
      const mockRows = generateMockHistory(120);
      const mockLatest = convertToLatest(mockRows);
      mockLatest.mock = true;
      const mockCSV = rowsToCSV(mockRows);
      writeData(mockLatest, mockCSV);
      console.warn('[fetch_data] ⚠️  MOCK data generated. Replace before launch!');
    }
  }
}

main().catch((err) => {
  console.error('[fetch_data] Fatal error:', err);
  process.exit(0); // Don't fail the build
});
