const $ = id => document.getElementById(id);
const number = value => value.toLocaleString('ru-RU');
let scope = 'world', airports = [], shown = 20, requestId = 0, controller, timer;
let types = {};
const colors = {large_airport: '#c3f37b', medium_airport: '#67b9ce'};
const map = L.map('map', {minZoom: 1, maxZoom: 12, maxBounds: [[-90, -220], [90, 220]], preferCanvas: true}).setView([30, 20], 2);
map.attributionControl.setPrefix('Leaflet');
map.attributionControl.addAttribution('Границы: Natural Earth');
const layer = L.layerGroup().addTo(map);

function element(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  return node;
}
function showAirport(airport) {
  const panel = $('detail');
  panel.replaceChildren();
  const close = element('button', '×', 'close');
  close.setAttribute('aria-label', 'Закрыть карточку');
  close.onclick = () => { panel.hidden = true; };
  panel.append(close, element('p', `${airport.iata || '—'} / ${airport.icao || airport.id}`, 'detail-code'), element('h2', airport.name), element('p', `${airport.city || 'Город не указан'} · ${airport.country_name}`), element('p', `${types[airport.type] || airport.type}. Регулярное сообщение в справочнике: ${airport.scheduled ? 'да' : 'нет'}.`), element('p', `${airport.lat.toFixed(4)}°, ${airport.lon.toFixed(4)}°`));
  const source = element('a', 'Запись в OurAirports ↗');
  source.href = `https://ourairports.com/airports/${encodeURIComponent(airport.id)}/`;
  source.target = '_blank'; source.rel = 'noopener';
  source.style.color = '#c3f37b'; source.style.fontSize = '12px';
  panel.append(source); panel.hidden = false;
}
function list() {
  $('results').replaceChildren();
  for (const airport of airports.slice(0, shown)) {
    const button = element('button', undefined, 'airport-row');
    const info = element('span', undefined, 'airport-info');
    info.append(element('strong', airport.name), element('small', `${airport.city || airport.country_name} · ${airport.country}`));
    button.append(element('span', airport.iata || airport.icao || airport.id, 'code'), info);
    button.onclick = () => { map.setView([airport.lat, airport.lon], 7); showAirport(airport); };
    $('results').append(button);
  }
  $('more').hidden = shown >= airports.length;
}
function fit() {
  if (!airports.length) return;
  map.fitBounds(L.latLngBounds(airports.map(a => [a.lat, a.lon])), {padding: [35, 35], maxZoom: 7});
}
function ranking(rows) {
  $('ranking').replaceChildren();
  const max = Math.max(1, ...rows.map(row => row.count));
  if (!rows.length) $('ranking').textContent = 'Нет данных для сравнения.';
  for (const row of rows) {
    const line = element('div', undefined, 'ranking-row');
    const track = element('div', undefined, 'track');
    const bar = element('div', undefined, 'bar');
    bar.style.width = `${row.count / max * 100}%`; track.append(bar);
    const label = element('span', row.name); label.title = row.name;
    line.append(label, track, element('span', number(row.count)));
    $('ranking').append(line);
  }
}
async function update(move = true) {
  const current = ++requestId;
  controller?.abort(); controller = new AbortController();
  $('status').textContent = 'Обновляем выборку…';
  const params = new URLSearchParams({scope, country: $('country').value, type: $('type').value, service: $('service').value, q: $('search').value});
  try {
    const response = await fetch(`/api/airports?${params}`, {signal: controller.signal});
    if (!response.ok) throw new Error('API error');
    const data = await response.json();
    if (current !== requestId) return;
    airports = data.airports; shown = 20;
    $('total').textContent = number(data.total);
    $('countries-count').textContent = number(data.countries_count);
    $('scheduled-count').textContent = number(data.scheduled_count);
    $('large-count').textContent = number(data.large_count);
    $('result-count').textContent = number(data.total);
    $('map-count').textContent = `${number(data.mapped)} ТОЧЕК`;
    $('status').textContent = !data.total ? 'Ничего не найдено. Попробуй другой запрос или сбрось фильтры.' : data.total > data.mapped ? `На карте и в списке первые ${number(data.mapped)} из ${number(data.total)} записей: сначала крупные аэропорты. Уточни страну или поиск. Статистика учитывает все результаты.` : `Найдено ${number(data.total)}. Поиск по названиям из источника: попробуй код SVO или Moscow.`;
    $('detail').hidden = true;
    layer.clearLayers();
    // Small points first; large airports stay visible on top.
    for (const airport of [...airports].reverse()) {
      const marker = L.circleMarker([airport.lat, airport.lon], {radius: airport.type === 'large_airport' ? 4 : 2.5, color: colors[airport.type] || '#8090ad', weight: 0.6, fillOpacity: 0.85}).addTo(layer);
      const tip = element('span', `${airport.iata || airport.id} · ${airport.name}`);
      marker.bindTooltip(tip);
      marker.on('click', () => showAirport(airport));
    }
    list(); ranking(data.top_countries);
    if (move) fit();
  } catch (error) {
    if (error.name !== 'AbortError' && current === requestId) {
      $('status').textContent = 'Не удалось обновить данные. Ниже остаётся предыдущая выборка. Проверь соединение и повтори попытку.';
    }
  }
}
async function init() {
  const [metaResponse, worldResponse] = await Promise.all([fetch('/api/meta'), fetch('/world.geojson')]);
  if (!metaResponse.ok || !worldResponse.ok) throw new Error('Не удалось загрузить карту');
  const [meta, world] = await Promise.all([metaResponse.json(), worldResponse.json()]);
  types = meta.types;
  for (const country of meta.countries) $('country').add(new Option(`${country.name} (${country.code})`, country.code));
  for (const [value, label] of Object.entries(types)) $('type').add(new Option(label, value));
  $('source-date').textContent = `Снимок загружен ${new Date(meta.retrieved_at).toLocaleDateString('ru-RU')}. В исходнике ${number(meta.source_rows)} записей; исключено из карты из-за координат: ${meta.invalid_coordinates}. Это дата загрузки, а не проверки каждого аэропорта.`;
  L.geoJSON(world, {interactive: false, style: {color: '#354456', weight: 0.6, fillColor: '#192838', fillOpacity: 1}}).addTo(map).bringToBack();
  await update();
}
document.querySelectorAll('[data-scope]').forEach(button => {
  button.onclick = () => {
    scope = button.dataset.scope; $('country').value = '';
    document.querySelectorAll('[data-scope]').forEach(item => { item.classList.toggle('active', item === button); item.setAttribute('aria-pressed', String(item === button)); });
    update();
  };
});
['country', 'type', 'service'].forEach(id => $(id).addEventListener('change', () => update()));
$('search').addEventListener('input', () => { clearTimeout(timer); timer = setTimeout(() => update(), 300); });
$('reset').onclick = () => {
  $('search').value = ''; $('country').value = ''; $('type').value = ''; $('service').value = 'scheduled';
  document.querySelector('[data-scope="world"]').click();
};
$('more').onclick = () => { shown += 20; list(); };
$('fit').onclick = fit;
map.on('resize', fit);
init().catch(() => { $('status').textContent = 'Не удалось загрузить карту и справочник. Обнови страницу, чтобы повторить попытку.'; });
