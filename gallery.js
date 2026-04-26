async function loadFleetGallery(folder, count, prefix) {
    const container = document.getElementById('gallery-target');
    for (let i = 1; i <= count; i++) {
        const id = i.toString().padStart(2, '0');
        const filename = `${id}_${prefix}.jpg`;
        try {
            const response = await fetch(`./fleet_assets/${folder}/${filename}.meta.json`);
            const meta = await response.json();
            container.innerHTML += `
                <div class="photo-card">
                    <img src="./fleet_assets/${folder}/${filename}" alt="${meta.title}">
                    <div class="caption">
                        <h4>${meta.title}</h4>
                        <p><strong>${meta.subtitle}</strong></p>
                        <p>${meta.caption_high}</p>
                    </div>
                </div>`;
        } catch (e) { console.warn(`Missing meta for ${filename}`); }
    }
}
