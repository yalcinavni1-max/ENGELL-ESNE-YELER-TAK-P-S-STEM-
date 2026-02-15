const profilesArea = document.getElementById('profiles-area');
const searchInput = document.getElementById('searchInput');

searchInput.addEventListener("keypress", (e) => { if (e.key === "Enter") performSearch(); });

async function performSearch() {
    const query = searchInput.value.trim();
    if (!query) return alert("Grup adı girin!");
    profilesArea.innerHTML = `<div class="loading">🔍 '${query}' taranıyor...</div>`;

    try {
        const response = await fetch(`/api/search?q=${query}`);
        const data = await response.json();
        profilesArea.innerHTML = '';
        if (data.error) return profilesArea.innerHTML = `<div class="loading">${data.error}</div>`;

        data.forEach(user => {
            if (user.error) return;
            const section = document.createElement('div');
            section.className = 'user-section';
            
            // Win Rate Renkleri
            const wr = user.win_rate;
            const wrCol = wr >= 50 ? '#2ecc71' : (wr <= 25 ? '#e74c3c' : '#f39c12');

            section.innerHTML = `
                <div class="profile-header">
                    <img src="${user.icon}" class="profile-icon">
                    <div class="profile-text">
                        <div class="name-row">
                            <span class="summoner-name-style">${user.summoner}</span>
                            <div class="wr-pie" style="background: conic-gradient(${wrCol} 0% ${wr}%, #444 ${wr}% 100%);">
                                <span class="wr-text">%${wr}</span>
                            </div>
                        </div>
                        <div class="rank-text">${user.rank}</div>
                    </div>
                </div>
                <div class="matches-container"></div>`;
            
            const container = section.querySelector('.matches-container');
            user.matches.forEach(match => {
                const card = document.createElement('div');
                card.className = `match-card ${match.result}`;
                card.onclick = () => card.classList.toggle('active');
                
                // İtemler (Boşluksuz)
                let itemsHtml = match.items.map(url => `<div class="item-slot"><img src="${url}" class="item-img"></div>`).join('');
                const csColor = match.cs.includes("VS") ? "#3498db" : "#aaa";

                // Puan Rengi (Grade Class) Kontrolü
                // Grade bazen S, A, B+ gelebilir. Sadece ilk harfi alıp class yapıyoruz (grade-S, grade-A)
                const gradeClass = `grade-${match.grade.charAt(0)}`; 

                card.innerHTML = `
                    <div class="card-content">
                        <div class="champ-info"><img src="${match.img}" class="champ-img">
                            <div>
                                <span class="champ-name">${match.champion}</span>
                                <div class="grade-badge ${gradeClass}">${match.grade}</div>
                            </div>
                        </div>
                        <div class="items-grid">${itemsHtml}</div>
                        <div class="stats"><div class="result-text">${match.result.toUpperCase()}</div><div class="kda-text">${match.kda}</div></div>
                    </div>
                    <div class="match-details">
                        <div class="detail-box"><span>KDA</span><b class="text-white">${match.kda_score}</b></div>
                        <div class="detail-box"><span>Durum</span><b style="color:${csColor}">${match.cs}</b></div>
                        <div class="detail-box"><span>Mod</span><b class="text-white">${match.queue_mode}</b></div>
                    </div>`;
                container.appendChild(card);
            });
            profilesArea.appendChild(section);
        });
    } catch (e) { profilesArea.innerHTML = "Sistem Hatası!"; }
}
