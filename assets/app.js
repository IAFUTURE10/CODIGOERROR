(function () {
  'use strict';
  var search = document.querySelector('[data-search-input]');
  if (search) {
    search.closest('[data-search-root]').hidden = false;
    var cards = Array.from(document.querySelectorAll('[data-guide-card]'));
    var status = document.querySelector('[data-search-status]');
    function normalize(value) { return value.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, ''); }
    function filter() {
      var query = normalize(search.value).trim().split(/\s+/).filter(Boolean);
      var count = 0;
      cards.forEach(function (card) {
        var text = normalize(card.dataset.search);
        card.hidden = !query.every(function (word) { return text.includes(word); });
        if (!card.hidden) count++;
      });
      status.textContent = count + ' guías disponibles' + (count ? '.' : '. No hay una guía para esta búsqueda; consulta el soporte oficial del producto.');
    }
    search.value = new URLSearchParams(location.search).get('q') || '';
    search.addEventListener('input', filter);
    filter();
  }
  var form = document.getElementById('observation-form');
  if (!form) return;
  var observations = [];
  var list = document.getElementById('observations');
  var download = document.getElementById('download-report');
  var note = document.getElementById('notebook-status');
  form.hidden = false;
  download.hidden = false;
  function render() {
    list.replaceChildren();
    observations.forEach(function (entry, index) {
      var item = document.createElement('li');
      var text = document.createElement('p');
      text.textContent = entry.action + '\nResultado: ' + entry.result + '\nDecisión/reversión: ' + (entry.next || 'Pendiente');
      var remove = document.createElement('button');
      remove.type = 'button';
      remove.textContent = 'Eliminar comprobación ' + (index + 1);
      remove.addEventListener('click', function () { observations.splice(index, 1); render(); note.textContent = 'Comprobación eliminada.'; });
      item.append(text, remove);
      list.append(item);
    });
  }
  form.addEventListener('submit', function (event) {
    event.preventDefault();
    var action = document.getElementById('action').value.trim();
    var result = document.getElementById('result').value.trim();
    if (!action || !result) { note.textContent = 'Escribe la acción y el resultado observado.'; return; }
    observations.push({ action: action, result: result, next: document.getElementById('next').value.trim() });
    render();
    form.reset();
    note.textContent = 'Comprobación añadida. Descarga el informe antes de cerrar la página.';
    document.getElementById('action').focus();
  });
  download.addEventListener('click', function () {
    var device = document.getElementById('device').value.trim();
    var symptom = document.getElementById('symptom').value.trim();
    if (!device && !symptom && !observations.length) { note.textContent = 'Añade el equipo, el síntoma o una comprobación antes de descargar.'; return; }
    var text = 'CUADERNO DE DIAGNÓSTICO\nEquipo/sistema: ' + (device || 'Pendiente') + '\nSíntoma: ' + (symptom || 'Pendiente') + '\n\n' + observations.map(function (entry, i) { return (i + 1) + '. ' + entry.action + '\nResultado: ' + entry.result + '\nDecisión/reversión: ' + (entry.next || 'Pendiente'); }).join('\n\n');
    var url = URL.createObjectURL(new Blob([text], { type: 'text/plain;charset=utf-8' }));
    var link = document.createElement('a');
    link.href = url;
    link.download = 'diagnostico-codigo-error.txt';
    document.body.append(link);
    link.click();
    link.remove();
    setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
    note.textContent = 'Informe preparado para descargar. Revísalo antes de compartirlo.';
  });
})();
