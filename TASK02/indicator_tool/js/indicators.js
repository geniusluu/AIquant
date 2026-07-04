// indicators.js — 四指标计算引擎（从 Python 移植）
// RSI / MACD / 布林带 / KDJ

function calcRSI(prices, period) {
  period = period || 14;
  var rsi = new Array(prices.length).fill(null);
  if (prices.length <= period) return rsi;

  var deltas = [];
  for (var i = 1; i < prices.length; i++) {
    deltas.push(prices[i] - prices[i - 1]);
  }
  var gains = deltas.map(function (d) { return Math.max(d, 0); });
  var losses = deltas.map(function (d) { return Math.abs(Math.min(d, 0)); });

  var avgGain = 0, avgLoss = 0;
  for (var i = 0; i < period; i++) { avgGain += gains[i]; avgLoss += losses[i]; }
  avgGain /= period;
  avgLoss /= period;

  if (avgLoss === 0) { rsi[period] = 100; }
  else { rsi[period] = 100 - 100 / (1 + avgGain / avgLoss); }

  for (var i = period + 1; i < prices.length; i++) {
    avgGain = (avgGain * (period - 1) + gains[i - 1]) / period;
    avgLoss = (avgLoss * (period - 1) + losses[i - 1]) / period;
    if (avgLoss === 0) { rsi[i] = 100; }
    else { rsi[i] = 100 - 100 / (1 + avgGain / avgLoss); }
  }
  return rsi;
}

function calcEMA(values, period) {
  var ema = new Array(values.length).fill(null);
  if (values.length < period) return ema;
  var mult = 2 / (period + 1);
  var sma = 0;
  for (var i = 0; i < period; i++) sma += values[i];
  sma /= period;
  ema[period - 1] = sma;
  for (var i = period; i < values.length; i++) {
    ema[i] = values[i] * mult + ema[i - 1] * (1 - mult);
  }
  return ema;
}

function calcMACD(prices, fast, slow, signal) {
  fast = fast || 12; slow = slow || 26; signal = signal || 9;
  var emaFast = calcEMA(prices, fast);
  var emaSlow = calcEMA(prices, slow);

  var dif = new Array(prices.length).fill(null);
  for (var i = 0; i < prices.length; i++) {
    if (emaFast[i] !== null && emaSlow[i] !== null) dif[i] = emaFast[i] - emaSlow[i];
  }

  var difStart = -1;
  for (var i = 0; i < dif.length; i++) { if (dif[i] !== null) { difStart = i; break; } }

  var dea = new Array(prices.length).fill(null);
  if (difStart >= 0) {
    var difSlice = dif.slice(difStart);
    var deaSlice = calcEMA(difSlice, signal);
    for (var j = 0; j < deaSlice.length; j++) {
      if (deaSlice[j] !== null) dea[difStart + j] = deaSlice[j];
    }
  }

  var macd = new Array(prices.length).fill(null);
  for (var i = 0; i < prices.length; i++) {
    if (dif[i] !== null && dea[i] !== null) macd[i] = 2 * (dif[i] - dea[i]);
  }
  return { dif: dif, dea: dea, macd: macd };
}

function calcBOLL(prices, period, nbdev) {
  period = period || 20; nbdev = nbdev || 2;
  var mid = new Array(prices.length).fill(null);
  var up = new Array(prices.length).fill(null);
  var dn = new Array(prices.length).fill(null);

  for (var i = period - 1; i < prices.length; i++) {
    var window = prices.slice(i - period + 1, i + 1);
    var m = 0;
    for (var j = 0; j < window.length; j++) m += window[j];
    m /= period;
    var variance = 0;
    for (var j = 0; j < window.length; j++) variance += Math.pow(window[j] - m, 2);
    variance /= period;
    var std = Math.sqrt(variance);
    mid[i] = m;
    up[i] = m + nbdev * std;
    dn[i] = m - nbdev * std;
  }
  return { mid: mid, up: up, dn: dn };
}

function calcKDJ(highs, lows, closes, n, m1) {
  n = n || 9; m1 = m1 || 3;
  var m2 = m1;
  var len = closes.length;
  var k = new Array(len).fill(50);
  var d = new Array(len).fill(50);
  var j = new Array(len).fill(50);

  for (var i = 0; i < len; i++) { k[i] = null; d[i] = null; j[i] = null; }

  for (var i = n - 1; i < len; i++) {
    var hhv = -Infinity, llv = Infinity;
    for (var x = i - n + 1; x <= i; x++) {
      if (highs[x] > hhv) hhv = highs[x];
      if (lows[x] < llv) llv = lows[x];
    }
    var rsv;
    if (hhv === llv) { rsv = 50; }
    else { rsv = (closes[i] - llv) / (hhv - llv) * 100; }

    if (i === n - 1) {
      k[i] = (2 / 3) * 50 + (1 / 3) * rsv;
      d[i] = (2 / 3) * 50 + (1 / 3) * k[i];
    } else {
      k[i] = (2 / 3) * k[i - 1] + (1 / 3) * rsv;
      d[i] = (2 / 3) * d[i - 1] + (1 / 3) * k[i];
    }
    j[i] = 3 * k[i] - 2 * d[i];
  }
  return { k: k, d: d, j: j };
}

// 信号判定
function getSignals(rsi, macd, boll, kdj, closes) {
  var n = closes.length;
  // 找最后一个非 null
  function lastVal(arr) {
    for (var i = arr.length - 1; i >= 0; i--) { if (arr[i] !== null) return arr[i]; }
    return null;
  }
  function lastIdx(arr) {
    for (var i = arr.length - 1; i >= 0; i--) { if (arr[i] !== null) return i; }
    return -1;
  }

  var signals = { rsi: "neutral", macd: "neutral", boll: "neutral", kdj: "neutral" };
  var summary = { buy: 0, sell: 0, neutral: 0, verdict: "中性" };

  // RSI
  var rsiVal = lastVal(rsi);
  if (rsiVal !== null) {
    if (rsiVal < 30) signals.rsi = "buy";
    else if (rsiVal > 70) signals.rsi = "sell";
    else signals.rsi = "neutral";
  }

  // MACD: 最后一天 DIF vs DEA
  var macdIdx = lastIdx(macd.dif);
  if (macdIdx > 0 && macd.dif[macdIdx] !== null && macd.dea[macdIdx] !== null) {
    if (macd.dif[macdIdx] > macd.dea[macdIdx]) signals.macd = "buy";
    else signals.macd = "sell";
  }

  // BOLL: 收盘价 vs 上下轨
  var bollIdx = lastIdx(boll.up);
  if (bollIdx >= 0 && closes[bollIdx] !== null && boll.up[bollIdx] !== null) {
    if (closes[bollIdx] <= boll.dn[bollIdx] * 1.01) signals.boll = "buy";
    else if (closes[bollIdx] >= boll.up[bollIdx] * 0.99) signals.boll = "sell";
    else signals.boll = "neutral";
  }

  // KDJ: K vs D
  var kdjIdx = lastIdx(kdj.k);
  if (kdjIdx > 0 && kdj.k[kdjIdx] !== null && kdj.d[kdjIdx] !== null) {
    if (kdj.k[kdjIdx] > kdj.d[kdjIdx] && kdj.k[kdjIdx] < 20) signals.kdj = "buy";
    else if (kdj.k[kdjIdx] < kdj.d[kdjIdx] && kdj.k[kdjIdx] > 80) signals.kdj = "sell";
    else if (kdj.k[kdjIdx] > kdj.d[kdjIdx]) signals.kdj = "buy";
    else signals.kdj = "sell";
  }

  // 共振评分
  ["rsi", "macd", "boll", "kdj"].forEach(function (key) {
    if (signals[key] === "buy") summary.buy++;
    else if (signals[key] === "sell") summary.sell++;
    else summary.neutral++;
  });

  if (summary.buy >= 3) summary.verdict = "强买入";
  else if (summary.buy === 2) summary.verdict = "偏多";
  else if (summary.sell >= 3) summary.verdict = "强卖出";
  else if (summary.sell === 2) summary.verdict = "偏空";
  else summary.verdict = "中性震荡";

  return { signals: signals, summary: summary };
}
