const codeEl = document.getElementById('code');
const stdinEl = document.getElementById('stdin');
const runBtn = document.getElementById('runBtn');
const sampleBtn = document.getElementById('sampleBtn');
const scanOut = document.getElementById('scanOut');
const compileOut = document.getElementById('compileOut');
const runOut = document.getElementById('runOut');
const compileOptionsEl = document.getElementById('compileOptions');
const runToggleEl = document.getElementById('runToggle');

const sample = `#include <bits/stdc++.h>
using namespace std;

int main(){
  ios::sync_with_stdio(false);
  cin.tie(nullptr);
  int n; if(!(cin>>n)) return 0;
  long long sum=0; for(int i=0;i<n;i++){ long long x; cin>>x; sum+=x; }
  cout<<sum<<"\n";
  // system("ls");
  return 0;
}`;

sampleBtn.addEventListener('click', () => {
  codeEl.value = sample;
  stdinEl.value = '5\n1 2 3 4 5\n';
});

runBtn.addEventListener('click', async () => {
  scanOut.textContent = compileOut.textContent = runOut.textContent = '';
  runBtn.disabled = true; runBtn.textContent = 'Running...';
  try {
    const compileOptions = compileOptionsEl.value.trim() ? compileOptionsEl.value.trim().split(/\s+/) : [];
    const body = {
      code: codeEl.value,
      stdin: stdinEl.value,
      compileOptions,
      run: runToggleEl.checked,
    };
    const res = await fetch('/api/compile-run', {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body)
    });
    const data = await res.json();
    if (data.scan) {
      scanOut.textContent = formatResult(data.scan);
    }
    if (data.compile) {
      compileOut.textContent = formatResult(data.compile);
    }
    if (data.run) {
      runOut.textContent = formatResult(data.run);
    } else if (!runToggleEl.checked) {
      runOut.textContent = 'Run skipped';
    }
  } catch (e) {
    compileOut.textContent = 'Request failed: ' + e;
  } finally {
    runBtn.disabled = false; runBtn.textContent = 'Compile & Run';
  }
});

function formatResult(r) {
  const parts = [];
  if (r.durationMs != null) parts.push(`[${r.durationMs} ms]`);
  if (r.exitCode != null) parts.push(`exit=${r.exitCode}`);
  if (r.wasKilledByTimeout) parts.push(`timeout`);
  const header = parts.length ? parts.join(' ') + '\n' : '';
  let out = '';
  if (r.stdout) out += r.stdout + (r.stdout.endsWith('\n') ? '' : '\n');
  if (r.stderr) out += (out ? '' : '') + r.stderr;
  return header + out;
}

// Load defaults
if (!codeEl.value.trim()) sampleBtn.click();
