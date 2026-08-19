import fs from 'node:fs';
import path from 'node:path';

export interface IndexData {
  schema_version: string;
  method_version: string;
  date: string;
  generated_at: string;
  indices: {
    R_M: { value: number | null; unit: string; change_1d: number | null };
    R_A: { value: number | null; unit: string; change_1d: number | null };
    Lambda: { value: number | null; unit: string; change_1d: number | null };
    Omega: { value: number | null; unit: string; change_1d: number | null };
  };
  sources: string[];
  license: string;
  mock?: boolean;
}

export interface HistoryRow {
  date: string;
  R_M: number | null;
  R_A: number | null;
  Lambda: number | null;
  Omega: number | null;
  Lambda_chained: number | null;
  method_version: string;
}

function parseCSV(csv: string): Record<string, string>[] {
  const lines = csv.trim().split('\n').filter(l => l.trim());
  if (lines.length === 0) return [];
  const headers = lines[0].split(',').map((h) => h.trim());
  return lines.slice(1).map((line) => {
    const values = line.split(',').map((v) => v.trim());
    const obj: Record<string, string> = {};
    headers.forEach((h, i) => {
      obj[h] = values[i] ?? '';
    });
    return obj;
  });
}

function safeParseFloat(v: string | undefined): number | null {
  if (!v || v === '' || v === 'null' || v === 'NaN') return null;
  const n = parseFloat(v);
  return isNaN(n) ? null : n;
}

export function loadIndexData(): IndexData {
  const jsonPath = path.resolve(process.cwd(), 'public/api/parity/latest.json');
  const raw = fs.readFileSync(jsonPath, 'utf-8');
  return JSON.parse(raw);
}

export function loadSparklineData(days: number = 90): { date: string; value: number }[] {
  const csvPath = path.resolve(process.cwd(), 'public/api/parity/history.csv');
  const raw = fs.readFileSync(csvPath, 'utf-8');
  const rows = parseCSV(raw);
  rows.sort((a, b) => a.date.localeCompare(b.date));
  const recent = rows.slice(-days);
  return recent
    .map((r) => ({
      date: r.date,
      value: safeParseFloat(r.Lambda),
    }))
    .filter((r) => r.value !== null) as { date: string; value: number }[];
}

export function loadHistoryData(): HistoryRow[] {
  const csvPath = path.resolve(process.cwd(), 'public/api/parity/history.csv');
  const raw = fs.readFileSync(csvPath, 'utf-8');
  const rows = parseCSV(raw);
  rows.sort((a, b) => a.date.localeCompare(b.date));
  return rows.map((r) => ({
    date: r.date,
    R_M: safeParseFloat(r.R_M),
    R_A: safeParseFloat(r.R_A),
    Lambda: safeParseFloat(r.Lambda),
    Omega: safeParseFloat(r.Omega),
    Lambda_chained: safeParseFloat(r.Lambda_chained),
    method_version: r.method_version || '0.1',
  }));
}

export function loadLambdaHistory(): { date: string; value: number }[] {
  return loadHistoryData()
    .filter((r) => r.Lambda !== null)
    .map((r) => ({ date: r.date, value: r.Lambda! }));
}
