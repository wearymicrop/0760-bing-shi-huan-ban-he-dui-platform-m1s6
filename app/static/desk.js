const feedback = document.querySelector('#run-feedback');
const filter = document.querySelector('#filter');
const sample = document.querySelector('#sample');
const module = document.body.dataset.module;
const runId = document.body.dataset.run;
const file = document.querySelector('#source-file');
const runSample = document.querySelector('#run-sample');
const rerun = document.querySelector('#rerun');

function filterLedger() {
    const query = filter.value.trim().toLocaleLowerCase();
    let found = false;
    document.querySelectorAll('#ledger tbody tr').forEach(row => {
        const match = row.textContent.toLocaleLowerCase().includes(query);
        row.hidden = !match;
        found ||= match;
    });
    document.querySelector('#no-match').hidden = found;
}

async function submit(path, options, open) {
    feedback.textContent = '正在计算…';
    runSample.disabled = true;
    file.disabled = true;
    if (rerun) rerun.disabled = true;
    try {
        const response = await fetch(path, {method: 'POST', ...options});
        const result = await response.json();
        if (!response.ok) throw new Error(result.message || '无法读取，请检查文件后重试。');
        if (open) {
            location.assign(`/desk/${module}?run=${encodeURIComponent(result.id)}`);
        } else {
            feedback.textContent = '复算一致，已复用原批次。';
        }
    } catch (error) {
        feedback.textContent = error.message;
    } finally {
        runSample.disabled = false;
        file.disabled = false;
        if (rerun) rerun.disabled = false;
    }
}

filter.addEventListener('input', filterLedger);
document.querySelectorAll('[data-booking]').forEach(button => button.addEventListener('click', () => {
    filter.value = button.dataset.booking;
    filterLedger();
    document.querySelectorAll('[data-booking]').forEach(item => item.toggleAttribute('data-selected', item === button));
}));
if (sessionStorage.getItem('rink-sample')) sample.value = sessionStorage.getItem('rink-sample');
runSample.addEventListener('click', () => {
    sessionStorage.setItem('rink-sample', sample.value);
    submit('/api/runs', {headers: {'Content-Type': 'application/json'}, body: JSON.stringify({sample: sample.value})}, true);
});
file.addEventListener('change', () => {
    if (!file.files.length) return;
    const data = new FormData();
    data.append('source', file.files[0]);
    submit('/api/runs', {body: data}, true);
    file.value = '';
});
rerun?.addEventListener('click', () => submit(`/api/runs/${runId}/rerun`, {}, false));
document.querySelector('#print')?.addEventListener('click', () => print());
