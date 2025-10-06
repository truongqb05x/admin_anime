        // DOM Elements
        const animeTableBody = document.getElementById('animeTableBody');
        const animeModal = document.getElementById('animeModal');
        const modalTitle = document.getElementById('modalTitle');
        const animeForm = document.getElementById('animeForm');
        const addAnimeBtn = document.getElementById('addAnimeBtn');
        const closeModal = document.getElementById('closeModal');
        const cancelBtn = document.getElementById('cancelBtn');
        const saveAnimeBtn = document.getElementById('saveAnimeBtn');
        const searchInput = document.getElementById('searchInput');
        const statusFilter = document.getElementById('statusFilter');
        const yearFilter = document.getElementById('yearFilter');
        const featuredFilter = document.getElementById('featuredFilter');
        const sortBy = document.getElementById('sortBy');
        const applyFiltersBtn = document.getElementById('applyFiltersBtn');
        const resetFiltersBtn = document.getElementById('resetFiltersBtn');
        const pagination = document.getElementById('pagination');
        const totalRecords = document.getElementById('totalRecords');
        const posterImageInput = document.getElementById('poster_image');
        const coverImageInput = document.getElementById('cover_image');
        const posterPreview = document.getElementById('poster_preview');
        const coverPreview = document.getElementById('cover_preview');
        const loadingIndicator = document.getElementById('loadingIndicator');

        // Current state
        let currentPage = 1;
        const itemsPerPage = 5;
        let animeData = [];
        let categoriesData = [];
        let filteredData = [];
        let totalRecordsCount = 0;

        // Initialize
        document.addEventListener('DOMContentLoaded', function() {
            loadCategories();
            loadAnimeData();
            setupEventListeners();
            initializeYearFilter();
        });

        // Load categories from database
        async function loadCategories() {
            try {
                const response = await fetch('/api/categories');
                if (!response.ok) throw new Error('Failed to load categories');
                categoriesData = await response.json();
                initializeCategoriesMultiSelect();
            } catch (error) {
                console.error('Lỗi khi tải danh mục:', error);
                showError('Không thể tải danh sách thể loại');
            }
        }

        // Load anime data from database
        async function loadAnimeData() {
            showLoading(true);
            try {
                const params = new URLSearchParams({
                    page: currentPage,
                    per_page: itemsPerPage,
                    search: searchInput.value,
                    status: statusFilter.value,
                    year: yearFilter.value,
                    featured: featuredFilter.value,
                    sort_by: getSortField(),
                    sort_order: getSortOrder()
                });

                const response = await fetch(`/api/anime?${params}`);
                if (!response.ok) throw new Error('Failed to load anime data');
                
                const data = await response.json();
                animeData = data.anime || [];
                totalRecordsCount = data.total || 0;
                
                renderAnimeTable();
            } catch (error) {
                console.error('Lỗi khi tải dữ liệu anime:', error);
                showError('Không thể tải dữ liệu anime');
                animeData = [];
                totalRecordsCount = 0;
                renderAnimeTable();
            } finally {
                showLoading(false);
            }
        }

        // Get sort field from select value
        function getSortField() {
            const value = sortBy.value;
            return value.startsWith('-') ? value.substring(1) : value;
        }

        // Get sort order from select value
        function getSortOrder() {
            const value = sortBy.value;
            return value.startsWith('-') ? 'desc' : 'asc';
        }

        // Initialize year filter with dynamic years
        function initializeYearFilter() {
            const currentYear = new Date().getFullYear();
            const startYear = 2000;
            
            for (let year = currentYear; year >= startYear; year--) {
                const option = document.createElement('option');
                option.value = year;
                option.textContent = year;
                yearFilter.appendChild(option);
            }
        }

        // Setup event listeners
        function setupEventListeners() {
            addAnimeBtn.addEventListener('click', openAddModal);
            closeModal.addEventListener('click', closeAnimeModal);
            cancelBtn.addEventListener('click', closeAnimeModal);
            saveAnimeBtn.addEventListener('click', saveAnime);
            searchInput.addEventListener('input', debounce(applyFilters, 300));
            applyFiltersBtn.addEventListener('click', applyFilters);
            resetFiltersBtn.addEventListener('click', resetFilters);
            
            // File input handlers
            posterImageInput.addEventListener('change', function(e) {
                handleFileSelect(e, posterPreview, 'poster');
            });
            
            coverImageInput.addEventListener('change', function(e) {
                handleFileSelect(e, coverPreview, 'cover');
            });
            
            // Close modal when clicking outside
            window.addEventListener('click', function(event) {
                if (event.target === animeModal) {
                    closeAnimeModal();
                }
            });
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

        // Initialize categories multi-select
        function initializeCategoriesMultiSelect() {
            const container = document.getElementById('categoriesContainer');
            const input = document.getElementById('categoriesInput');
            const dropdown = document.getElementById('categoriesDropdown');
            
            // Clear existing options
            dropdown.innerHTML = '';
            
            // Populate dropdown with categories
            categoriesData.forEach(category => {
                const optionElement = document.createElement('div');
                optionElement.className = 'multi-select-option';
                optionElement.dataset.id = category.id;
                optionElement.textContent = category.name;
                optionElement.addEventListener('click', function() {
                    addSelectedCategory(category.id, category.name);
                    dropdown.style.display = 'none';
                });
                dropdown.appendChild(optionElement);
            });
            
            // Show dropdown when input is clicked
            input.addEventListener('click', function(e) {
                e.stopPropagation();
                dropdown.style.display = dropdown.style.display === 'block' ? 'none' : 'block';
            });
            
            // Hide dropdown when clicking outside
            document.addEventListener('click', function() {
                dropdown.style.display = 'none';
            });
        }

        // Add category to multi-select
        function addSelectedCategory(id, name) {
            const input = document.getElementById('categoriesInput');
            
            // Check if category is already selected
            const existingItems = input.querySelectorAll('.selected-item');
            for (let item of existingItems) {
                if (item.dataset.id === id.toString()) {
                    return; // Category already selected
                }
            }
            
            // Create selected item
            const selectedItem = document.createElement('div');
            selectedItem.className = 'selected-item';
            selectedItem.dataset.id = id;
            selectedItem.innerHTML = `
                ${name}
                <span class="remove-item" onclick="removeSelectedCategory(this)">&times;</span>
            `;
            input.appendChild(selectedItem);
        }

        // Remove category from multi-select
        function removeSelectedCategory(element) {
            element.parentElement.remove();
        }

        // Get selected category IDs
        function getSelectedCategoryIds() {
            const input = document.getElementById('categoriesInput');
            const selectedItems = input.querySelectorAll('.selected-item');
            const ids = [];
            
            selectedItems.forEach(item => {
                ids.push(parseInt(item.dataset.id));
            });
            
            return ids;
        }

        // Set selected categories
        function setSelectedCategories(categoryIds) {
            const input = document.getElementById('categoriesInput');
            input.innerHTML = '';
            
            if (categoryIds && categoryIds.length > 0) {
                categoryIds.forEach(categoryId => {
                    const category = categoriesData.find(c => c.id === categoryId);
                    if (category) {
                        addSelectedCategory(category.id, category.name);
                    }
                });
            }
        }

        // Handle file selection and preview
        async function handleFileSelect(event, previewElement, type) {
            const file = event.target.files[0];
            if (!file) return;

            // Validate file type
            const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif'];
            if (!allowedTypes.includes(file.type)) {
                alert('Chỉ chấp nhận file ảnh (JPEG, PNG, GIF)');
                event.target.value = '';
                return;
            }

            // Validate file size (max 5MB)
            if (file.size > 5 * 1024 * 1024) {
                alert('Kích thước file không được vượt quá 5MB');
                event.target.value = '';
                return;
            }

            // Show preview
            const reader = new FileReader();
            reader.onload = function(e) {
                previewElement.src = e.target.result;
                previewElement.style.display = 'block';
            };
            reader.readAsDataURL(file);

            // Upload file to server
            try {
                const formData = new FormData();
                formData.append('file', file);

                const response = await fetch('/api/upload', {
                    method: 'POST',
                    body: formData
                });

                if (response.ok) {
                    const result = await response.json();
                    // Store the URL for later use when saving
                    if (type === 'poster') {
                        posterImageInput.dataset.uploadedUrl = result.url;
                    } else {
                        coverImageInput.dataset.uploadedUrl = result.url;
                    }
                } else {
                    throw new Error('Upload failed');
                }
            } catch (error) {
                console.error('Lỗi khi upload file:', error);
                alert('Lỗi khi upload file');
                event.target.value = '';
                previewElement.style.display = 'none';
            }
        }

        // Generate slug from title
        function generateSlug() {
            const title = document.getElementById('title').value;
            const slugField = document.getElementById('slug');
            
            if (title && slugField) {
                // Convert to lowercase, remove accents, replace spaces with hyphens
                const slug = title
                    .toLowerCase()
                    .normalize('NFD').replace(/[\u0300-\u036f]/g, '') // Remove accents
                    .replace(/[^a-z0-9\s-]/g, '') // Remove special characters
                    .replace(/\s+/g, '-') // Replace spaces with hyphens
                    .replace(/-+/g, '-') // Replace multiple hyphens with single
                    .trim();
                
                slugField.value = slug;
            }
        }

        // Render anime table
        function renderAnimeTable() {
            animeTableBody.innerHTML = '';
            
            if (animeData.length === 0) {
                animeTableBody.innerHTML = `
                    <tr>
                        <td colspan="9" style="text-align: center; padding: 20px;">
                            <i class="fas fa-film" style="font-size: 48px; color: #ccc; margin-bottom: 10px;"></i>
                            <div>Không có dữ liệu</div>
                        </td>
                    </tr>
                `;
                updatePagination();
                updateTotalRecords();
                return;
            }
            
            animeData.forEach(anime => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>
                        <img src="${anime.poster_image || 'https://via.placeholder.com/60x80?text=No+Image'}" 
                             alt="${anime.title}" class="thumbnail">
                    </td>
                    <td>
                        <div class="anime-title">${anime.title}</div>
                        <div class="anime-slug">${anime.slug}</div>
                    </td>
                    <td>${anime.release_year || 'N/A'}</td>
                    <td><span class="status ${anime.status}">${getStatusText(anime.status)}</span></td>
                    <td>${anime.total_episodes || 0}</td>
                    <td>
                        <div class="rating">${anime.rating || 0} ⭐</div>
                        <div class="rating-count">${anime.total_ratings || 0} đánh giá</div>
                    </td>
                    <td>${formatNumber(anime.total_views || 0)}</td>
                    <td>${anime.featured ? '<i class="fas fa-star featured" title="Nổi bật"></i>' : ''}</td>
                    <td>
                        <div class="action-buttons">
                            <button class="action-btn view" onclick="viewEpisodes(${anime.id})" title="Xem tập phim">
    <i class="fas fa-list"></i>
</button>
                            <button class="action-btn edit" onclick="editAnime(${anime.id})" title="Sửa">
                                <i class="fas fa-edit"></i>
                            </button>
                            <button class="action-btn delete" onclick="deleteAnime(${anime.id})" title="Xóa">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </td>
                `;
                animeTableBody.appendChild(row);
            });
            
            updatePagination();
            updateTotalRecords();
        }

        // Get status text in Vietnamese
        function getStatusText(status) {
            switch(status) {
                case 'ongoing': return 'Đang chiếu';
                case 'completed': return 'Hoàn thành';
                case 'upcoming': return 'Sắp chiếu';
                default: return status;
            }
        }

        // Format number with commas
        function formatNumber(num) {
            return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
        }

        // Update pagination
        function updatePagination() {
            const totalPages = Math.ceil(totalRecordsCount / itemsPerPage);
            
            pagination.innerHTML = '';
            
            if (totalPages <= 1) return;
            
            // Previous button
            const prevBtn = document.createElement('button');
            prevBtn.innerHTML = '<i class="fas fa-chevron-left"></i>';
            prevBtn.disabled = currentPage === 1;
            prevBtn.addEventListener('click', () => {
                if (currentPage > 1) {
                    currentPage--;
                    loadAnimeData();
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
                    loadAnimeData();
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
                    loadAnimeData();
                }
            });
            pagination.appendChild(nextBtn);
        }

        // Update total records text
        function updateTotalRecords() {
            const startIndex = (currentPage - 1) * itemsPerPage + 1;
            const endIndex = Math.min(currentPage * itemsPerPage, totalRecordsCount);
            totalRecords.textContent = `Hiển thị ${startIndex}-${endIndex} của ${totalRecordsCount} bản ghi`;
        }

        // Apply filters
        function applyFilters() {
            currentPage = 1;
            loadAnimeData();
        }

        // Reset filters
        function resetFilters() {
            searchInput.value = '';
            statusFilter.value = '';
            yearFilter.value = '';
            featuredFilter.value = '';
            sortBy.value = 'title';
            currentPage = 1;
            loadAnimeData();
        }

        // Show loading indicator
        function showLoading(show) {
            loadingIndicator.style.display = show ? 'block' : 'none';
        }

        // Show error message
        function showError(message) {
            // You can implement a toast notification system here
            alert(message);
        }

        // Open add modal
        function openAddModal() {
            modalTitle.textContent = 'Thêm phim mới';
            animeForm.reset();
            document.getElementById('animeId').value = '';
            document.getElementById('country').value = 'Nhật Bản';
            document.getElementById('status').value = 'ongoing';
            document.getElementById('featured').checked = false;
            
            // Clear multi-selects
            setSelectedCategories([]);
            
            // Clear file previews and uploaded URLs
            posterPreview.style.display = 'none';
            coverPreview.style.display = 'none';
            posterImageInput.value = '';
            coverImageInput.value = '';
            delete posterImageInput.dataset.uploadedUrl;
            delete coverImageInput.dataset.uploadedUrl;
            
            animeModal.style.display = 'flex';
        }

        // Close modal
        function closeAnimeModal() {
            animeModal.style.display = 'none';
        }

        // Edit anime
        async function editAnime(id) {
            try {
                const response = await fetch(`/api/anime/${id}`);
                if (!response.ok) throw new Error('Failed to load anime');
                
                const anime = await response.json();
                
                if (!anime) return;
                
                modalTitle.textContent = 'Chỉnh sửa phim';
                document.getElementById('animeId').value = anime.id;
                document.getElementById('title').value = anime.title || '';
                document.getElementById('slug').value = anime.slug || '';
                document.getElementById('description').value = anime.description || '';
                document.getElementById('release_year').value = anime.release_year || '';
                document.getElementById('status').value = anime.status || 'ongoing';
                document.getElementById('total_episodes').value = anime.total_episodes || 0;
                document.getElementById('duration_per_episode').value = anime.duration_per_episode || '';
                document.getElementById('studio').value = anime.studio || '';
                document.getElementById('director').value = anime.director || '';
                document.getElementById('author').value = anime.author || '';
                document.getElementById('country').value = anime.country || 'Nhật Bản';
                document.getElementById('featured').checked = anime.featured || false;
                document.getElementById('meta_title').value = anime.meta_title || '';
                document.getElementById('meta_description').value = anime.meta_description || '';
                document.getElementById('meta_keywords').value = anime.meta_keywords || '';
                
                // Load and set categories
                const categoriesResponse = await fetch(`/api/anime/${id}/categories`);
                if (categoriesResponse.ok) {
                    const animeCategories = await categoriesResponse.json();
                    setSelectedCategories(animeCategories.map(c => c.id));
                }
                
                // Set file previews if available
                if (anime.poster_image) {
                    posterPreview.src = anime.poster_image;
                    posterPreview.style.display = 'block';
                }
                
                if (anime.cover_image) {
                    coverPreview.src = anime.cover_image;
                    coverPreview.style.display = 'block';
                }
                
                animeModal.style.display = 'flex';
            } catch (error) {
                console.error('Lỗi khi tải thông tin anime:', error);
                showError('Lỗi khi tải thông tin anime');
            }
        }

        // Save anime
        async function saveAnime() {
            const id = document.getElementById('animeId').value;
            const title = document.getElementById('title').value.trim();
            const slug = document.getElementById('slug').value.trim();
            
            if (!title || !slug) {
                alert('Vui lòng nhập tiêu đề và slug');
                return;
            }
            // Prepare anime data
            const animeData = {
                title: title,
                slug: slug,
                description: document.getElementById('description').value.trim(),
                release_year: document.getElementById('release_year').value ? parseInt(document.getElementById('release_year').value) : null,
                status: document.getElementById('status').value,
                total_episodes: parseInt(document.getElementById('total_episodes').value) || 0,
                duration_per_episode: document.getElementById('duration_per_episode').value ? parseInt(document.getElementById('duration_per_episode').value) : null,
                studio: document.getElementById('studio').value.trim(),
                director: document.getElementById('director').value.trim(),
                author: document.getElementById('author').value.trim(),
                country: document.getElementById('country').value.trim(),
                featured: document.getElementById('featured').checked,
                meta_title: document.getElementById('meta_title').value.trim(),
                meta_description: document.getElementById('meta_description').value.trim(),
                meta_keywords: document.getElementById('meta_keywords').value.trim(),
                poster_image: posterImageInput.dataset.uploadedUrl || '',
                cover_image: coverImageInput.dataset.uploadedUrl || ''
            };
            
            // Get selected category IDs
            const categoryIds = getSelectedCategoryIds();
            
            try {
                let response;
                if (id) {
                    // Update existing anime
                    response = await fetch(`/api/anime/${id}`, {
                        method: 'PUT',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify(animeData)
                    });
                } else {
                    // Add new anime
                    response = await fetch('/api/anime', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify(animeData)
                    });
                }
                
                if (response.ok) {
                    // Update categories
                    const animeId = id || (await response.json()).id;
                    const categoriesResponse = await fetch(`/api/anime/${animeId}/categories`, {
                        method: 'PUT',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ category_ids: categoryIds })
                    });
                    
                    if (categoriesResponse.ok) {
                        closeAnimeModal();
                        await loadAnimeData();
                        showSuccess(id ? 'Cập nhật phim thành công!' : 'Thêm phim mới thành công!');
                    } else {
                        throw new Error('Failed to update categories');
                    }
                } else {
                    const errorData = await response.json();
                    throw new Error(errorData.error || 'Failed to save anime');
                }
            } catch (error) {
                console.error('Lỗi khi lưu anime:', error);
                showError('Lỗi khi lưu phim: ' + error.message);
            }
        }

        // Delete anime
        async function deleteAnime(id) {
            if (!confirm('Bạn có chắc chắn muốn xóa phim này?')) {
                return;
            }
            
            try {
                const response = await fetch(`/api/anime/${id}`, {
                    method: 'DELETE'
                });
                
                if (response.ok) {
                    await loadAnimeData();
                    showSuccess('Xóa phim thành công!');
                } else {
                    const errorData = await response.json();
                    throw new Error(errorData.error || 'Failed to delete anime');
                }
            } catch (error) {
                console.error('Lỗi khi xóa anime:', error);
                showError('Lỗi khi xóa phim: ' + error.message);
            }
        }
            // Thay thế hàm viewEpisodes
function viewEpisodes(id) {
    window.location.href = `/tapphim?anime_id=${id}`;
}

        // Show success message
        function showSuccess(message) {
            // You can implement a toast notification system here
            alert(message);
        }
