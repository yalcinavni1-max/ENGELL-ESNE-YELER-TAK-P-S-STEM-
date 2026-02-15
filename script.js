const profilesArea = document.getElementById('profiles-area');
const searchInput = document.getElementById('searchInput');

// Enter tuşu desteği
searchInput.addEventListener("keypress", function(event) {
    if (event.key === "Enter") performSearch();
});

async function performSearch() {
    const query = searchInput.value.trim();
    
    if (!query) {
        alert("Lütfen bir grup adı girin!");
        return;
    }

    // Yükleniyor animasyonu
    profilesArea.innerHTML = `<div class="loading">
        🔍 <b>'${query}'</b> grubu taranıyor...<br>
        <small style="font-size:0.8rem; color:#aaa;">Veriler güncel olarak çekiliyor, lütfen bekleyin.</small>
    </div>`;

    try {
        // Yeni API'ye istek at
        const response = await fetch(`/api/search?q=${query}`);
        if (!response.ok) throw new Error("Sunucu ile bağlantı kurulamadı.");
        
        const data = await response.json();
        profilesArea.innerHTML = ''; // Temizle

        // Hata kontrolü (Grup bulunamadı vb.)
        if (data.error) {
            profilesArea.innerHTML = `<div style="text-align:center; color:#ff6b6b; font-size:1.1rem; margin-top:20px;">
                ⚠️ ${data.error}
            </div>`;
            return;
        }
        
        const list = Array.isArray(data) ? data : [data];
        
        if (list.length === 0) {
            profilesArea.innerHTML = '<div style="color:white;text-align:center;">Bu grupta kayıtlı hesap yok veya veri çekilemedi.</div>';
            return;
        }

        list.forEach(user => {
            if (user.error) {
                // Tekil kullanıcı hatası (Link bozuk vb.)
                const errDiv = document.createElement('div');
                errDiv.style.color = "#ff6b6b";
                errDiv.style.textAlign = "center";
                errDiv.style.padding = "10px";
                errDiv.innerHTML = `<p>⚠️ Hesap Hatası: ${user.error}</p>`;
                profilesArea.appendChild(errDiv);
            } else {
                createProfileCard(user);
            }
        });

    } catch (error) {
        console.error("JS Hatası:", error);
        profilesArea.innerHTML = `<div style="text-align:center; color:#ff6b6b;">Sistem Hatası: ${error.message}</div>`;
    }
}

function createProfileCard(user) {
    const section = document.createElement('div');
    section.className = 'user-section';
    
    const icon = user.icon || "https://ddragon.leagueoflegends.com/cdn/14.3.1/img/profileicon/29.png";
    const name = user.summoner || "Bilinmeyen";
    const rank = user.rank || "Unranked";

    section.innerHTML = `
        <div class="profile-header">
            <img src="${icon}" class="profile-icon">
            <div class="profile-text">
                <div class="summoner-name-style">${name}</div>
                <div class="rank-text">${rank}</div>
            </div>
        </div>
        <div class="matches-container"></div>
    `;
    
    const container = section.querySelector('.matches-container');

    if (user.matches && user.matches.length > 0) {
        user.matches.forEach(match => {
            const card = document.createElement('div');
            const resClass = match.result ? match.result : 'lose';
            card.classList.add('match-card', resClass);
            card.onclick = () => card.classList.toggle('active');

            // İtemler
            let itemsHtml = '';
            const items = match.items || [];
            if (items.length > 0) {
                items.forEach(url => {
                    itemsHtml += `<div class="item-slot"><img src="${url}" class="item-img" onerror="this.parentElement.style.display='none'"></div>`;
                });
            } else {
                itemsHtml = '<span style="font-size:0.7rem; color:#666;">İtem Yok</span>';
            }

            const champImg = match.img || "";
            const lpText = match.lp_change || "";
            let lpStyle = "color:#aaa;";
            if(lpText.includes('+')) lpStyle = "color:#4cd137;";
            if(lpText.includes('-')) lpStyle = "color:#e84118;";

            // CS veya GÖRÜŞ SKORU Rengi
            const csText = match.cs || "";
            // Eğer içinde "VS" geçiyorsa (Support) Mavi yap, yoksa Gri
            const csColor = csText.includes("VS") ? "#3498db" : "#aaa"; 
            const csLabel = csText.includes("VS") ? "Görüş Skoru" : "Minyon";

            card.innerHTML = `
                <div class="card-content">
                    <div class="champ-info">
                        <img src="${champImg}" class="champ-img">
                        <div>
                            <span class="champ-name">${match.champion}</span>
                            <div class="grade-badge grade-${match.grade}">${match.grade}</div>
                        </div>
                    </div>
                    
                    <div class="items-grid">${itemsHtml}</div>

                    <div class="stats">
                        <div class="result-text">${resClass.toUpperCase()}</div>
                        <div class="kda-text">${match.kda}</div>
                        <div style="font-size:0.7rem; color:#666;">▼ Detay</div>
                    </div>
                </div>

                <div class="match-details">
                    <div class="detail-box">
                        <span>KDA Skor</span>
                        <b class="text-white">${match.kda_score}</b>
                    </div>
                    <div class="detail-box">
                        <span>${csLabel}</span>
                        <b style="color:${csColor};">${csText}</b>
                    </div>
                    
                    <div class="detail-box" style="flex-direction:column;">
                        <span style="font-size:0.75rem; color:#ddd; font-weight:bold;">${match.queue_mode}</span>
                        <span style="font-size:0.7rem; font-weight:bold; ${lpStyle} margin-top:2px;">${lpText}</span>
                    </div>
                </div>
            `;
            container.appendChild(card);
        });
    } else {
        container.innerHTML = '<div style="padding:20px; text-align:center; color:#666;">Maç bulunamadı.</div>';
    }
    profilesArea.appendChild(section);
}
