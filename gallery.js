async function loadFleetGallery(folder, count, basePath, targetId) {
    if (basePath === undefined) basePath = '.';
    if (targetId === undefined) targetId = 'gallery-target';
    const container = document.getElementById(targetId);
    if (!container) { console.warn(`gallery-target #${targetId} not found`); return; }

    let manifest;
    try {
        const mr = await fetch(`${basePath}/fleet_assets/${folder}/meta.json`);
        manifest = await mr.json();
    } catch(e) {
        console.warn(`Missing manifest for ${folder}`);
        return;
    }

    const files = (manifest.files || []).slice(0, count);
    for (const filename of files) {
        try {
            const response = await fetch(`${basePath}/fleet_assets/${folder}/${filename}.meta.json`);
            const meta = await response.json();
            container.innerHTML += `
                <div class="photo-card">
                    <img src="${basePath}/fleet_assets/${folder}/${filename}" alt="${meta.title}">
                    <div class="caption">
                        <h4>${meta.title}</h4>
                        <p><strong>${meta.subtitle}</strong></p>
                        <p>${meta.upper_caption}</p>
                    </div>
                </div>`;
        } catch (e) { console.warn(`Missing meta for ${filename}`); }
    }
}
