async function loadFleetGallery(folder, count, prefix) {
    const container = document.getElementById('gallery-target');
    const isSubDir = window.location.pathname.includes('/combos/');
    const basePath = isSubDir ? '../fleet_assets' : './fleet_assets';
    const extensions = ['jpg', 'webp', 'avif'];

    for (let i = 1; i <= count; i++) {
        const id = i.toString().padStart(2, '0');
        let found = false;
        for (const ext of extensions) {
            const filename = `${id}_${prefix}.${ext}`;
            try {
                const response = await fetch(`${basePath}/${folder}/${filename}.meta.json`);
                if (!response.ok) continue;
                const meta = await response.json();
                const title = meta.title || meta.upper_caption || "Asset Detail";
                const high = meta.upper_caption || meta.caption_high || "";
                const low = meta.caption_low || meta.lower_caption || "";

                container.innerHTML += `
                    <div class="photo-card" onclick="openLightbox(this)">
                        <img src="${basePath}/${folder}/${filename}" alt="${title}">
                        <div class="caption">
                            <h4>${title}</h4>
                            <p>${high}</p>
                            <small>${low}</small>
                        </div>
                    </div>`;
                found = true; break;
            } catch (e) { continue; }
        }
    }
}
