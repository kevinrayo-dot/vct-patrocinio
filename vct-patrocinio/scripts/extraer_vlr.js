// Cómo se obtuvo datos/series_vct_americas_crudo.csv (26/11/2026).
// Uso: abrir https://www.vlr.gg en el navegador, abrir la consola (F12) y pegar este script.
// Recorre las páginas de "Matches > Completed" de los 12 equipos de VCT Américas 2026,
// espera 0,9 s entre páginas para no cargar el sitio y descarga un CSV con los datos sin limpiar.
// Nota: la hora sale en la zona horaria del navegador (Bogotá, UTC-5).

const EQUIPOS = {
  "/team/1034/nrg": "NRG", "/team/11058/g2-esports": "G2 Esports", "/team/120/100-thieves": "100 Thieves",
  "/team/15072/2game-esports": "2Game Esports", "/team/188/cloud9": "Cloud9", "/team/2/sentinels": "Sentinels",
  "/team/2355/kr-esports": "KRÜ Esports", "/team/2359/leviat-n": "LEVIATÁN", "/team/2406/furia": "FURIA",
  "/team/427/envy": "ENVY", "/team/5248/evil-geniuses": "Evil Geniuses", "/team/6961/loud": "LOUD",
};
const esperar = (ms) => new Promise((r) => setTimeout(r, ms));
const limpio = (s) => (s || "").replace(/\s+/g, " ").trim();
const filas = [];

for (const [ruta, nombre] of Object.entries(EQUIPOS)) {
  const [, , id, slug] = ruta.split("/");
  for (let pagina = 1; pagina <= 30; pagina++) {
    const html = await fetch(`/team/matches/${id}/${slug}/?group=completed&page=${pagina}`).then((r) => r.text());
    const doc = new DOMParser().parseFromString(html, "text/html");
    const items = [...doc.querySelectorAll("a.m-item")];
    if (!items.length) break; // no hay más páginas
    for (const a of items) {
      const ev = a.querySelector(".m-item-event");
      const evento = limpio(ev?.querySelector("div")?.textContent);
      const equipos = a.querySelectorAll(".m-item-team");
      const res = a.querySelector(".m-item-result");
      const marcador = res ? [...res.querySelectorAll(":scope > span")].map((x) => limpio(x.textContent)) : [];
      const fecha = a.querySelector(".m-item-date");
      filas.push({
        equipo_id: id, equipo: nombre, match_id: (a.getAttribute("href") || "").split("/")[1],
        rival: limpio(equipos[1]?.querySelector(".m-item-team-name")?.textContent),
        rival_tag: limpio(equipos[1]?.querySelector(".m-item-team-tag")?.textContent),
        evento, fase: limpio(ev?.textContent).replace(evento, "").trim(),
        marcador_equipo: marcador[0] ?? "", marcador_rival: marcador[1] ?? "",
        resultado_vlr: (res?.className.match(/mod-(win|loss|tie|draw)/) || ["", ""])[1],
        fecha: limpio(fecha?.querySelector("div")?.textContent),
        hora: limpio(fecha?.textContent).replace(limpio(fecha?.querySelector("div")?.textContent), "").trim(),
      });
    }
    await esperar(900);
  }
}

const columnas = Object.keys(filas[0]);
const comillas = (v) => '"' + String(v).replace(/"/g, '""') + '"';
const csv = [columnas.join(",")].concat(filas.map((f) => columnas.map((c) => comillas(f[c])).join(","))).join("\n");
const enlace = document.createElement("a");
enlace.href = URL.createObjectURL(new Blob([csv + "\n"], { type: "text/csv" }));
enlace.download = "series_vct_americas_crudo.csv";
enlace.click();
console.log("Filas extraídas:", filas.length);
