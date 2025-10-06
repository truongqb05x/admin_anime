    // DOM Elements
    const episodesTableBody = document.getElementById('episodesTableBody');
    const episodeModal = document.getElementById('episodeModal');
    const modalTitle = document.getElementById('modalTitle');
    const episodeForm = document.getElementById('episodeForm');
    const addEpisodeBtn = document.getElementById('addEpisodeBtn');
    const closeModal = document.getElementById('closeModal');
    const cancelBtn = document.getElementById('cancelBtn');
    const saveEpisodeBtn = document.getElementById('saveEpisodeBtn');
    const searchInput = document.getElementById('searchInput');
    const episodeFilter = document.getElementById('episodeFilter');
    const viewsFilter = document.getElementById('viewsFilter');
    const sortBy = document.getElementById('sortBy');
    const applyFiltersBtn = document.getElementById('applyFiltersBtn');
    const resetFiltersBtn = document.getElementById('resetFiltersBtn');
    const pagination = document.getElementById('pagination');
    const totalRecords = document.getElementById('totalRecords');
    const seasonSelect = document.getElementById('seasonSelect');
    const videoPreview = document.getElementById('videoPreview');
    const videoUrlInput = document.getElementById('video_url');

    // Import Elements
    const excelFileInput = document.getElementById('excelFile');
    const fileInputLabel = document.getElementById('fileInputLabel');
    const fileName = document.getElementById('fileName');
    const previewImportBtn = document.getElementById('previewImportBtn');
    const importBtn = document.getElementById('importBtn');
    const clearImportBtn = document.getElementById('clearImportBtn');
    const downloadTemplateBtn = document.getElementById('downloadTemplateBtn');
    const importProgress = document.getElementById('importProgress');
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');
    const previewContainer = document.getElementById('previewContainer');
    const previewTable = document.getElementById('previewTable');
    const validationErrors = document.getElementById('validationErrors');
    const importAction = document.getElementById('importAction');
    const seasonImport = document.getElementById('seasonImport');

    // Current state
    let currentPage = 1;
    const itemsPerPage = 10;
    let episodesData = [];
    let filteredData = [];
    let totalRecordsCount = 0;
    let currentAnimeId = null;
    let currentAnime = null;
    let seasonsData = [];
    let currentExcelData = null;
    let validationResults = null;

    // Initialize
    document.addEventListener('DOMContentLoaded', function() {
        // Get anime ID from URL parameters
        const urlParams = new URLSearchParams(window.location.search);
        currentAnimeId = urlParams.get('anime_id');
        
        if (currentAnimeId) {
            loadAnimeDetails(currentAnimeId);
            loadSeasons(currentAnimeId);
            loadEpisodes();
        } else {
            showError('Không tìm thấy ID anime');
        }
        
        setupEventListeners();
        setupImportListeners();
    });

    // Load anime details
    async function loadAnimeDetails(animeId) {
        try {
            const response = await fetch(`/api/anime/${animeId}`);
            if (!response.ok) throw new Error('Failed to load anime details');
            
            currentAnime = await response.json();
            updateAnimeInfo();
        } catch (error) {
            console.error('Lỗi khi tải thông tin anime:', error);
            showError('Không thể tải thông tin anime');
        }
    }

    // Load seasons
    async function loadSeasons(animeId) {
        try {
            const response = await fetch(`/api/anime/${animeId}/seasons`);
            if (!response.ok) throw new Error('Failed to load seasons');
            
            seasonsData = await response.json();
            updateSeasonSelectors();
        } catch (error) {
            console.error('Lỗi khi tải danh sách mùa:', error);
            showError('Không thể tải danh sách mùa phim');
        }
    }

    // Load episodes
    async function loadEpisodes() {
        try {
            const seasonId = seasonSelect.value;
            const params = new URLSearchParams({
                season_id: seasonId,
                page: currentPage,
                per_page: itemsPerPage,
                search: searchInput.value
            });

            const response = await fetch(`/api/episodes?${params}`);
            if (!response.ok) throw new Error('Failed to load episodes');
            
            const data = await response.json();
            episodesData = data.episodes || [];
            totalRecordsCount = data.total || 0;
            
            applyFilters(); // Apply local filters after loading
        } catch (error) {
            console.error('Lỗi khi tải danh sách tập phim:', error);
            showError('Không thể tải danh sách tập phim');
            episodesData = [];
            totalRecordsCount = 0;
            renderEpisodesTable();
        }
    }

    // Update anime info in UI
    function updateAnimeInfo() {
        if (!currentAnime) return;
        
        const animePoster = document.querySelector('.anime-poster');
        const animeTitle = document.querySelector('.anime-details h3');
        const animeYear = document.querySelector('.anime-meta .meta-item:nth-child(1) span');
        const animeEpisodes = document.querySelector('.anime-meta .meta-item:nth-child(2) span');
        const animeRating = document.querySelector('.anime-meta .meta-item:nth-child(3) span');
        const animeViews = document.querySelector('.anime-meta .meta-item:nth-child(4) span');
        
        if (animePoster) animePoster.src = currentAnime.poster_image || 'https://via.placeholder.com/120x160?text=No+Image';
        if (animeTitle) animeTitle.textContent = currentAnime.title;
        if (animeYear) animeYear.textContent = currentAnime.release_year || 'N/A';
        if (animeEpisodes) animeEpisodes.textContent = `${currentAnime.total_episodes || 0} tập`;
        if (animeRating) animeRating.textContent = `${currentAnime.rating || 0}/5`;
        if (animeViews) animeViews.textContent = `${formatNumber(currentAnime.total_views || 0)} lượt xem`;
    }

    // Update season selectors
    function updateSeasonSelectors() {
        // Clear existing options
        seasonSelect.innerHTML = '';
        seasonImport.innerHTML = '';
        
        if (seasonsData.length === 0) {
            const option = document.createElement('option');
            option.value = '';
            option.textContent = 'Chưa có mùa nào';
            seasonSelect.appendChild(option);
            seasonImport.appendChild(option.cloneNode(true));
            return;
        }
        
        seasonsData.forEach(season => {
            const option1 = document.createElement('option');
            option1.value = season.id;
            option1.textContent = season.name || `Mùa ${season.season_number}`;
            seasonSelect.appendChild(option1);
            
            const option2 = option1.cloneNode(true);
            seasonImport.appendChild(option2);
        });
    }

    // Setup event listeners
    function setupEventListeners() {
        addEpisodeBtn.addEventListener('click', openAddModal);
        closeModal.addEventListener('click', closeEpisodeModal);
        cancelBtn.addEventListener('click', closeEpisodeModal);
        saveEpisodeBtn.addEventListener('click', saveEpisode);
        searchInput.addEventListener('input', debounce(applyFilters, 300));
        applyFiltersBtn.addEventListener('click', applyFilters);
        resetFiltersBtn.addEventListener('click', resetFilters);
        seasonSelect.addEventListener('change', changeSeason);
        videoUrlInput.addEventListener('input', updateVideoPreview);
        
        // Close modal when clicking outside
        window.addEventListener('click', function(event) {
            if (event.target === episodeModal) {
                closeEpisodeModal();
            }
        });
    }

    // Setup import listeners
    function setupImportListeners() {
        excelFileInput.addEventListener('change', handleFileSelect);
        previewImportBtn.addEventListener('click', previewImport);
        importBtn.addEventListener('click', processImport);
        clearImportBtn.addEventListener('click', clearImport);
        downloadTemplateBtn.addEventListener('click', downloadTemplate);
    }

    // Debounce function for search
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    // Handle file selection
    function handleFileSelect(event) {
        const file = event.target.files[0];
        if (file) {
            fileName.textContent = file.name;
            fileInputLabel.classList.add('has-file');
            previewImportBtn.disabled = false;
            importBtn.disabled = false;
            currentExcelData = null;
            previewContainer.style.display = 'none';
        } else {
            fileName.textContent = 'Chưa chọn file';
            fileInputLabel.classList.remove('has-file');
            previewImportBtn.disabled = true;
            importBtn.disabled = true;
        }
    }

    // Preview import data
    function previewImport() {
        const file = excelFileInput.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = function(e) {
            const data = new Uint8Array(e.target.result);
            const workbook = XLSX.read(data, { type: 'array' });
            
            // Get first worksheet
            const worksheet = workbook.Sheets[workbook.SheetNames[0]];
            const jsonData = XLSX.utils.sheet_to_json(worksheet, { header: 1 });
            
            if (jsonData.length < 2) {
                alert('File Excel không có dữ liệu hoặc định dạng không đúng!');
                return;
            }
            
            // Validate header
            const headers = jsonData[0];
            const expectedHeaders = ['Số tập', 'Tiêu đề', 'Mô tả', 'URL Video', 'Thời lượng (phút)', 'Ngày phát hành (YYYY-MM-DD)'];
            
            if (!arraysEqual(headers, expectedHeaders)) {
                alert(`Định dạng file không đúng. Các cột cần có: ${expectedHeaders.join(', ')}`);
                return;
            }
            
            // Process data
            const episodes = [];
            const errors = [];
            
            for (let i = 1; i < jsonData.length; i++) {
                const row = jsonData[i];
                if (row.length === 0) continue;
                
                const episode = {
                    episode_number: parseInt(row[0]),
                    title: row[1] || '',
                    description: row[2] || '',
                    video_url: row[3] || '',
                    duration: parseInt(row[4]) || 0,
                    release_date: row[5] || ''
                };
                
                // Validate episode
                const validation = validateEpisode(episode, i);
                if (validation.isValid) {
                    episodes.push(episode);
                } else {
                    errors.push({
                        row: i + 1,
                        errors: validation.errors
                    });
                }
            }
            
            currentExcelData = episodes;
            validationResults = {
                episodes: episodes,
                errors: errors
            };
            
            displayPreview(episodes, errors);
        };
        
        reader.readAsArrayBuffer(file);
    }

    // Validate episode data
    function validateEpisode(episode, rowIndex) {
        const errors = [];
        
        if (!episode.episode_number || isNaN(episode.episode_number) || episode.episode_number < 1) {
            errors.push('Số tập không hợp lệ');
        }
        
        if (!episode.video_url) {
            errors.push('URL Video là bắt buộc');
        }
        
        if (episode.duration && (isNaN(episode.duration) || episode.duration < 1)) {
            errors.push('Thời lượng không hợp lệ');
        }
        
        if (episode.release_date && !isValidDate(episode.release_date)) {
            errors.push('Ngày phát hành không hợp lệ (định dạng YYYY-MM-DD)');
        }
        
        return {
            isValid: errors.length === 0,
            errors: errors
        };
    }

    // Check if date is valid
    function isValidDate(dateString) {
        const regex = /^\d{4}-\d{2}-\d{2}$/;
        if (!dateString.match(regex)) return false;
        
        const date = new Date(dateString);
        const timestamp = date.getTime();
        
        if (typeof timestamp !== 'number' || isNaN(timestamp)) return false;
        
        return date.toISOString().slice(0, 10) === dateString;
    }

    // Check if two arrays are equal
    function arraysEqual(a, b) {
        if (a.length !== b.length) return false;
        for (let i = 0; i < a.length; i++) {
            if (a[i] !== b[i]) return false;
        }
        return true;
    }

    // Display preview of import data
    function displayPreview(episodes, errors) {
        previewContainer.style.display = 'block';
        
        // Create preview table
        let tableHTML = `
            <table>
                <thead>
                    <tr>
                        <th>Số tập</th>
                        <th>Tiêu đề</th>
                        <th>Mô tả</th>
                        <th>URL Video</th>
                        <th>Thời lượng</th>
                        <th>Ngày phát hành</th>
                        <th>Trạng thái</th>
                    </tr>
                </thead>
                <tbody>
        `;
        
        episodes.forEach((episode, index) => {
            const error = errors.find(e => e.row === index + 2);
            const rowClass = error ? 'error-row' : '';
            
            tableHTML += `
                <tr class="${rowClass}">
                    <td>${episode.episode_number}</td>
                    <td>${episode.title || '-'}</td>
                    <td>${episode.description ? truncateText(episode.description, 30) : '-'}</td>
                    <td>${truncateText(episode.video_url, 30)}</td>
                    <td>${episode.duration || '-'}</td>
                    <td>${episode.release_date || '-'}</td>
                    <td>${error ? '<span style="color: red;">Lỗi</span>' : '<span style="color: green;">OK</span>'}</td>
                </tr>
            `;
        });
        
        tableHTML += '</tbody></table>';
        previewTable.innerHTML = tableHTML;
        
        // Display validation errors
        if (errors.length > 0) {
            let errorsHTML = '<h4>Lỗi kiểm tra:</h4><ul>';
            errors.forEach(error => {
                errorsHTML += `<li>Dòng ${error.row}: ${error.errors.join(', ')}</li>`;
            });
            errorsHTML += '</ul>';
            validationErrors.innerHTML = errorsHTML;
        } else {
            validationErrors.innerHTML = '<p style="color: green;">Tất cả dữ liệu đều hợp lệ!</p>';
        }
    }

    // Process import
    async function processImport() {
        if (!currentExcelData || currentExcelData.length === 0) {
            alert('Không có dữ liệu để import!');
            return;
        }
        
        const action = importAction.value;
        const seasonId = parseInt(seasonImport.value);
        
        if (!seasonId) {
            alert('Vui lòng chọn mùa phim!');
            return;
        }
        
        importProgress.style.display = 'block';
        progressFill.style.width = '0%';
        progressText.textContent = 'Đang xử lý...';
        
        try {
            const response = await fetch('/api/episodes/import', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    episodes: currentExcelData,
                    season_id: seasonId,
                    action: action
                })
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Import failed');
            }
            
            const result = await response.json();
            
            progressFill.style.width = '100%';
            progressText.textContent = 'Import hoàn tất!';
            
            setTimeout(() => {
                importProgress.style.display = 'none';
                clearImport();
                loadEpisodes(); // Reload episodes
                showSuccess(result.message);
            }, 1000);
            
        } catch (error) {
            console.error('Lỗi khi import:', error);
            importProgress.style.display = 'none';
            showError('Lỗi khi import: ' + error.message);
        }
    }

    // Clear import
    function clearImport() {
        excelFileInput.value = '';
        fileName.textContent = 'Chưa chọn file';
        fileInputLabel.classList.remove('has-file');
        previewImportBtn.disabled = true;
        importBtn.disabled = true;
        previewContainer.style.display = 'none';
        currentExcelData = null;
        validationResults = null;
    }

    // Download template
    function downloadTemplate() {
        // Create template data
        const templateData = [
            ['Số tập', 'Tiêu đề', 'Mô tả', 'URL Video', 'Thời lượng (phút)', 'Ngày phát hành (YYYY-MM-DD)'],
            [1, 'Tập 1: Tiêu đề tập phim', 'Mô tả tập phim', 'https://example.com/video1.mp4', 24, '2023-10-15'],
            [2, 'Tập 2: Tiêu đề tập phim', 'Mô tả tập phim', 'https://example.com/video2.mp4', 24, '2023-10-22']
        ];
        
        // Create worksheet
        const worksheet = XLSX.utils.aoa_to_sheet(templateData);
        
        // Create workbook
        const workbook = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(workbook, worksheet, 'Template');
        
        // Generate and download file
        XLSX.writeFile(workbook, 'template_tap_phim.xlsx');
    }

    // Render episodes table
    function renderEpisodesTable() {
        const startIndex = (currentPage - 1) * itemsPerPage;
        const endIndex = startIndex + itemsPerPage;
        const currentData = filteredData.slice(startIndex, endIndex);
        
        episodesTableBody.innerHTML = '';
        
        if (currentData.length === 0) {
            episodesTableBody.innerHTML = `
                <tr>
                    <td colspan="7" style="text-align: center; padding: 20px;">
                        <i class="fas fa-film" style="font-size: 48px; color: #ccc; margin-bottom: 10px;"></i>
                        <div>Không có dữ liệu</div>
                    </td>
                </tr>
            `;
            updatePagination();
            updateTotalRecords();
            return;
        }
        
        currentData.forEach(episode => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>
                    <img src="${episode.thumbnail_url || 'https://via.placeholder.com/80x45?text=No+Thumb'}" 
                         alt="${episode.title}" class="thumbnail">
                </td>
                <td><strong>Tập ${episode.episode_number}</strong></td>
                <td>
                    <div class="episode-title">${episode.title || 'Không có tiêu đề'}</div>
                    ${episode.description ? `<div class="episode-description">${truncateText(episode.description, 50)}</div>` : ''}
                </td>
                <td class="duration">${episode.duration || 0} phút</td>
                <td class="views">${formatNumber(episode.views || 0)}</td>
                <td>${formatDate(episode.release_date)}</td>
                <td>
                    <div class="action-buttons">
                        <button class="action-btn preview" onclick="previewVideo('${episode.video_url}')" title="Xem video">
                            <i class="fas fa-play"></i>
                        </button>
                        <button class="action-btn edit" onclick="editEpisode(${episode.id})" title="Sửa">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="action-btn delete" onclick="deleteEpisode(${episode.id})" title="Xóa">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>
            `;
            episodesTableBody.appendChild(row);
        });
        
        updatePagination();
        updateTotalRecords();
    }

    // Truncate text
    function truncateText(text, maxLength) {
        if (!text) return '';
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    }

    // Format number with commas
    function formatNumber(num) {
        return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    }

    // Format date
    function formatDate(dateString) {
        if (!dateString) return 'Chưa xác định';
        const date = new Date(dateString);
        return date.toLocaleDateString('vi-VN');
    }

    // Update pagination
    function updatePagination() {
        const totalPages = Math.ceil(filteredData.length / itemsPerPage);
        
        pagination.innerHTML = '';
        
        if (totalPages <= 1) return;
        
        // Previous button
        const prevBtn = document.createElement('button');
        prevBtn.innerHTML = '<i class="fas fa-chevron-left"></i>';
        prevBtn.disabled = currentPage === 1;
        prevBtn.addEventListener('click', () => {
            if (currentPage > 1) {
                currentPage--;
                renderEpisodesTable();
            }
        });
        pagination.appendChild(prevBtn);
        
        // Page buttons
        const startPage = Math.max(1, currentPage - 2);
        const endPage = Math.min(totalPages, currentPage + 2);
        
        for (let i = startPage; i <= endPage; i++) {
            const pageBtn = document.createElement('button');
            pageBtn.textContent = i;
            pageBtn.classList.toggle('active', i === currentPage);
            pageBtn.addEventListener('click', () => {
                currentPage = i;
                renderEpisodesTable();
            });
            pagination.appendChild(pageBtn);
        }
        
        // Next button
        const nextBtn = document.createElement('button');
        nextBtn.innerHTML = '<i class="fas fa-chevron-right"></i>';
        nextBtn.disabled = currentPage === totalPages;
        nextBtn.addEventListener('click', () => {
            if (currentPage < totalPages) {
                currentPage++;
                renderEpisodesTable();
            }
        });
        pagination.appendChild(nextBtn);
    }

    // Update total records text
    function updateTotalRecords() {
        const startIndex = (currentPage - 1) * itemsPerPage + 1;
        const endIndex = Math.min(currentPage * itemsPerPage, filteredData.length);
        totalRecords.textContent = `Hiển thị ${startIndex}-${endIndex} của ${filteredData.length} bản ghi`;
    }

    // Apply filters
    function applyFilters() {
        const searchTerm = searchInput.value.toLowerCase();
        const episodeValue = episodeFilter.value;
        const viewsValue = viewsFilter.value;
        const sortValue = sortBy.value;
        
        filteredData = episodesData.filter(episode => {
            const matchesSearch = episode.title?.toLowerCase().includes(searchTerm) || 
                                episode.description?.toLowerCase().includes(searchTerm);
            
            let matchesEpisode = true;
            if (episodeValue) {
                const episodeNum = episode.episode_number;
                if (episodeValue === '1-10') {
                    matchesEpisode = episodeNum >= 1 && episodeNum <= 10;
                } else if (episodeValue === '11-20') {
                    matchesEpisode = episodeNum >= 11 && episodeNum <= 20;
                } else if (episodeValue === '21-30') {
                    matchesEpisode = episodeNum >= 21 && episodeNum <= 30;
                } else if (episodeValue === '31+') {
                    matchesEpisode = episodeNum >= 31;
                }
            }
            
            let matchesViews = true;
            if (viewsValue) {
                const views = episode.views || 0;
                if (viewsValue === '0-1000') {
                    matchesViews = views >= 0 && views <= 1000;
                } else if (viewsValue === '1001-5000') {
                    matchesViews = views >= 1001 && views <= 5000;
                } else if (viewsValue === '5001-10000') {
                    matchesViews = views >= 5001 && views <= 10000;
                } else if (viewsValue === '10000+') {
                    matchesViews = views >= 10000;
                }
            }
            
            return matchesSearch && matchesEpisode && matchesViews;
        });
        
        // Sort data
        if (sortValue) {
            const [field, direction] = sortValue.startsWith('-') ? 
                [sortValue.substring(1), 'desc'] : [sortValue, 'asc'];
            
            filteredData.sort((a, b) => {
                let aVal = a[field];
                let bVal = b[field];
                
                if (typeof aVal === 'string') {
                    aVal = aVal.toLowerCase();
                    bVal = bVal.toLowerCase();
                }
                
                if (aVal < bVal) return direction === 'asc' ? -1 : 1;
                if (aVal > bVal) return direction === 'asc' ? 1 : -1;
                return 0;
            });
        }
        
        currentPage = 1;
        renderEpisodesTable();
    }

    // Reset filters
    function resetFilters() {
        searchInput.value = '';
        episodeFilter.value = '';
        viewsFilter.value = '';
        sortBy.value = 'episode_number';
        applyFilters();
    }

    // Change season
    function changeSeason() {
        currentPage = 1;
        loadEpisodes();
    }

    // Open add modal
    function openAddModal() {
        modalTitle.textContent = 'Thêm tập mới';
        episodeForm.reset();
        document.getElementById('episodeId').value = '';
        document.getElementById('seasonId').value = seasonSelect.value;
        videoPreview.innerHTML = '<i class="fas fa-video" style="font-size: 2rem; color: #ccc;"></i>';
        episodeModal.style.display = 'flex';
    }

    // Close modal
    function closeEpisodeModal() {
        episodeModal.style.display = 'none';
    }

    // Update video preview
    function updateVideoPreview() {
        const videoUrl = videoUrlInput.value;
        
        if (videoUrl) {
            videoPreview.innerHTML = `
                <div class="video-container">
                    <video controls style="max-width: 100%; max-height: 200px;">
                        <source src="${videoUrl}" type="video/mp4">
                        Trình duyệt của bạn không hỗ trợ video.
                    </video>
                    <div class="video-url">${truncateText(videoUrl, 50)}</div>
                </div>
            `;
        } else {
            videoPreview.innerHTML = '<i class="fas fa-video" style="font-size: 2rem; color: #ccc;"></i>';
        }
    }

    // Edit episode
    async function editEpisode(id) {
        try {
            const response = await fetch(`/api/episodes/${id}`);
            if (!response.ok) throw new Error('Failed to load episode');
            
            const episode = await response.json();
            
            modalTitle.textContent = 'Chỉnh sửa tập phim';
            document.getElementById('episodeId').value = episode.id;
            document.getElementById('seasonId').value = episode.season_id;
            document.getElementById('episode_number').value = episode.episode_number;
            document.getElementById('duration').value = episode.duration || '';
            document.getElementById('title').value = episode.title || '';
            document.getElementById('description').value = episode.description || '';
            document.getElementById('video_url').value = episode.video_url;
            document.getElementById('release_date').value = episode.release_date || '';
            
            updateVideoPreview();
            episodeModal.style.display = 'flex';
        } catch (error) {
            console.error('Lỗi khi tải thông tin tập phim:', error);
            showError('Lỗi khi tải thông tin tập phim');
        }
    }

    // Save episode
    async function saveEpisode() {
        const id = document.getElementById('episodeId').value;
        const episodeNumber = document.getElementById('episode_number').value;
        const videoUrl = document.getElementById('video_url').value;
        const seasonId = document.getElementById('seasonId').value;
        
        if (!episodeNumber || !videoUrl || !seasonId) {
            alert('Vui lòng nhập số tập, URL video và chọn mùa phim');
            return;
        }
        
        const episodeData = {
            season_id: parseInt(seasonId),
            episode_number: parseInt(episodeNumber),
            duration: parseInt(document.getElementById('duration').value) || null,
            title: document.getElementById('title').value.trim(),
            description: document.getElementById('description').value.trim(),
            video_url: videoUrl.trim(),
            release_date: document.getElementById('release_date').value || null
        };
        
        try {
            let response;
            if (id) {
                // Update existing episode
                response = await fetch(`/api/episodes/${id}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(episodeData)
                });
            } else {
                // Add new episode
                response = await fetch('/api/episodes', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(episodeData)
                });
            }
            
            if (response.ok) {
                closeEpisodeModal();
                await loadEpisodes();
                showSuccess(id ? 'Cập nhật tập phim thành công!' : 'Thêm tập phim mới thành công!');
            } else {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to save episode');
            }
        } catch (error) {
            console.error('Lỗi khi lưu tập phim:', error);
            showError('Lỗi khi lưu tập phim: ' + error.message);
        }
    }

    // Delete episode
    async function deleteEpisode(id) {
        if (!confirm('Bạn có chắc chắn muốn xóa tập phim này không?')) {
            return;
        }
        
        try {
            const response = await fetch(`/api/episodes/${id}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                await loadEpisodes();
                showSuccess('Xóa tập phim thành công!');
            } else {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to delete episode');
            }
        } catch (error) {
            console.error('Lỗi khi xóa tập phim:', error);
            showError('Lỗi khi xóa tập phim: ' + error.message);
        }
    }

    // Preview video
    function previewVideo(videoUrl) {
        window.open(videoUrl, '_blank');
    }

    // Go back to anime list
    function goBackToAnime() {
        window.location.href = 'bophim.html';
    }

    // Show error message
    function showError(message) {
        // You can implement a toast notification system here
        alert('Lỗi: ' + message);
    }

    // Show success message
    function showSuccess(message) {
        // You can implement a toast notification system here
        alert(message);
    }