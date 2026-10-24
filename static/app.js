const fields = ['origin', 'carrier', 'month'];
let requestId = 0;
const format = value => value === null ? 'нет данных' : value.toLocaleString('ru-RU');

function bars(id, rows, key, suffix) {
  const target = document.getElementById(id);
  target.replaceChildren();
  const max = Math.max(1, ...rows.map(row => Math.abs(row[key])));
  if (!rows.length) target.textContent = 'Нет данных для выбранных фильтров.';
  for (const row of rows) {
    const line = document.createElement('div');
    line.className = 'bar-row';
    const label = document.createElement('span');
    label.textContent = row.name;
    const track = document.createElement('div');
    track.className = 'track';
    const bar = document.createElement('div');
    bar.className = row[key] < 0 ? 'bar early' : 'bar';
    bar.style.width = `${Math.abs(row[key]) / max * 100}%`;
    track.append(bar);
    const value = document.createElement('span');
    value.textContent = `${format(row[key])}${suffix}${key === 'delay' ? ` · n=${row.count}` : ''}`;
    line.append(label, track, value);
    target.append(line);
  }
}

async function update() {
  const current = ++requestId;
  const status = document.getElementById('status');
  status.textContent = 'Обновляем…';
  const params = new URLSearchParams(fields.map(field => [field, document.getElementById(field).value]));
  try {
    const response = await fetch(`/api/flights?${params}`);
    if (!response.ok) throw new Error('Ошибка сервера');
    const data = await response.json();
    if (current !== requestId) return;
    for (const field of fields) {
      const select = document.getElementById(field);
      if (select.options.length === 1) {
        for (const value of data.options[field]) select.add(new Option(value, value));
      }
    }
    document.getElementById('total').textContent = format(data.total);
    document.getElementById('delay').textContent = format(data.mean_delay) + (data.mean_delay === null ? '' : ' мин');
    document.getElementById('percent').textContent = format(data.delayed_percent) + (data.delayed_percent === null ? '' : ' %');
    status.textContent = `Измерений задержки: ${format(data.measured)}. Пропусков: ${format(data.missing)}.`;
    bars('carriers', data.carriers, 'delay', ' мин');
    bars('destinations', data.destinations, 'count', '');
  } catch (error) {
    if (current === requestId) status.textContent = 'Не удалось загрузить данные. Проверь, что Python-сервер запущен, и обнови страницу.';
  }
}
fields.forEach(field => document.getElementById(field).addEventListener('change', update));
document.getElementById('reset').addEventListener('click', () => {
  fields.forEach(field => { document.getElementById(field).value = ''; });
  update();
});
update();
