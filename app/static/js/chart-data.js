const RAW_POINT_LIMIT = 600;
const BUCKET_COUNT = 300;

export function buildSeries(results, fromMs, toMs) {
  if (results.length <= RAW_POINT_LIMIT) {
    return rawSeries(results);
  }
  return bucketedSeries(results, fromMs, toMs);
}

function rawSeries(results) {
  const line = [];
  const down = [];
  for (const result of results) {
    const x = new Date(result.checked_at).getTime();
    if (result.is_up) {
      line.push({ x, y: result.response_time_ms, checks: 1, failed: 0 });
    } else {
      line.push({ x, y: null });
      down.push({ x, y: 0, checks: 1, failed: 1, responseTime: result.response_time_ms });
    }
  }
  return { line, down, bucketed: false };
}

function bucketedSeries(results, fromMs, toMs) {
  const width = Math.max(1, (toMs - fromMs) / BUCKET_COUNT);
  const buckets = new Map();
  for (const result of results) {
    const x = new Date(result.checked_at).getTime();
    const index = Math.min(BUCKET_COUNT - 1, Math.max(0, Math.floor((x - fromMs) / width)));
    let bucket = buckets.get(index);
    if (!bucket) {
      bucket = { checks: 0, failed: 0, upTimeSum: 0, upCount: 0 };
      buckets.set(index, bucket);
    }
    bucket.checks += 1;
    if (result.is_up) {
      if (result.response_time_ms !== null) {
        bucket.upTimeSum += result.response_time_ms;
        bucket.upCount += 1;
      }
    } else {
      bucket.failed += 1;
    }
  }

  const line = [];
  const down = [];
  for (const index of [...buckets.keys()].sort((a, b) => a - b)) {
    const bucket = buckets.get(index);
    const x = fromMs + (index + 0.5) * width;
    const y = bucket.upCount ? Math.round(bucket.upTimeSum / bucket.upCount) : null;
    line.push({ x, y, checks: bucket.checks, failed: bucket.failed });
    if (bucket.failed) {
      down.push({ x, y: 0, checks: bucket.checks, failed: bucket.failed });
    }
  }
  return { line, down, bucketed: true };
}
