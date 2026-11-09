// minimal permissive After Effects object-model mock: executes the generated JSX to catch JS/runtime errors
const fs = require('fs');
let calls = {};
function mk(name) {
  const f = function () {};
  return new Proxy(f, {
    get(t, p) {
      if (p === Symbol.toPrimitive) return () => 0;
      if (p === 'length') return 0;
      if (p === 'numKeys') return 0;
      if (p === 'exists') return true;
      if (p === 'fsName') return '/x';
      if (p === 'then') return undefined;
      if (!(p in t)) t[p] = mk(name + '.' + String(p));
      return t[p];
    },
    set(t, p, v) { t[p] = v; return true; },
    apply(t, th, args) {
      calls[name.split('.').pop()] = (calls[name.split('.').pop()] || 0) + 1;
      const last = name.split('.').pop();
      if (['setValueAtTime', 'setValue'].includes(last)) {
        for (const a of args) if (a === undefined || (typeof a === 'number' && !isFinite(a))) throw new Error('bad value in ' + name);
      }
      return mk(name + '()');
    },
    construct(t, args) { return mk(name + '#new'); }
  });
}
const g = global;
for (const n of ['app', 'File', 'ImportOptions', 'KeyframeEase', 'MarkerValue', 'ParagraphJustification', 'ParagraphDirection',
  'KeyframeInterpolationType', 'PropertyValueType', 'TrackMatteType', '$']) g[n] = mk(n);
g.Shape = function () { this.vertices = []; };
g.alert = (m) => console.log('ALERT:', m);
let src = fs.readFileSync(process.argv[2], 'utf8').replace(/^﻿/, '').replace(/^#target.*$/m, '');
eval(src);
console.log('calls:', JSON.stringify(Object.fromEntries(Object.entries(calls).filter(([k]) => /set|add|Mask|Text|Null|Camera/.test(k)))));
