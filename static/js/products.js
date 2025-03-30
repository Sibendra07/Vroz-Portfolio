$(document).ready(function() {
    // Configuration
    const config = {
        itemsPerPage: 30,
        currentPage: 1,
        totalItems: 0,
        isLoading: false,
        isInitialLoad: true
    };

    // DOM Elements
    const elements = {
        // Main containers
        availableSection: $('#available-section'),
        soldSection: $('#sold-section'),
        availableProducts: $('#available-products'),
        soldProducts: $('#sold-products'),
        
        // Status elements
        loading: $('#loading-indicator'),
        empty: $('#empty-state'),
        availableEmpty: $('#available-empty'),
        soldEmpty: $('#sold-empty'),
        
        // Pagination
        pagination: $('#pagination-container'),
        prevBtn: $('#prev-page'),
        nextBtn: $('#next-page'),
        pageInfo: $('#page-info')
    };

    // Initialize the page
    init();

    // Event Handlers
    elements.prevBtn.click(handlePreviousPage);
    elements.nextBtn.click(handleNextPage);

    function init() {
        showLoading();
        
        // Check if initialProducts exists and is valid
        if (window.initialProducts && Array.isArray(initialProducts) && initialProducts.length > 0) {
            setTimeout(() => {
                renderProducts(initialProducts);
                setupPagination(initialProducts.length);
                hideLoading();
                config.isInitialLoad = false;
            }, 300);
        } else {
            loadProducts();
        }
    }

    function loadProducts() {
        if (config.isLoading) return;
        
        config.isLoading = true;
        if (!config.isInitialLoad) {
            showLoading();
        }

        $.ajax({
            url: `/api/products?page=${config.currentPage}&limit=${config.itemsPerPage}`,
            method: 'GET',
            dataType: 'json',
            success: function(data) {
                if (data && data.items) {
                    renderProducts(data.items);
                    setupPagination(data.total || data.items.length);
                } else {
                    showEmptyState();
                }
            },
            error: function(xhr, status, error) {
                console.error("Error loading products:", status, error);
                showError("Failed to load products. Please try again later.");
            },
            complete: function() {
                config.isLoading = false;
                config.isInitialLoad = false;
                hideLoading();
            }
        });
    }

    function renderProducts(products) {
        // Clear both containers
        elements.availableProducts.empty();
        elements.soldProducts.empty();
        
        if (!products || products.length === 0) {
            showEmptyState();
            return;
        }

        hideEmptyState();
        
        // Separate available and sold products
        const availableProducts = products.filter(product => !product.is_sold);
        const soldProducts = products.filter(product => product.is_sold);
        
        // Render available products
        if (availableProducts.length > 0) {
            const availableElements = availableProducts.map(product => createProductCard(product, false));
            elements.availableProducts.append(availableElements.join(''));
            elements.availableSection.fadeIn(300);
            elements.availableEmpty.hide();
        } else {
            elements.availableSection.fadeIn(300);
            elements.availableEmpty.fadeIn(300);
        }
        
        // Render sold products
        if (soldProducts.length > 0) {
            const soldElements = soldProducts.map(product => createProductCard(product, true));
            elements.soldProducts.append(soldElements.join(''));
            elements.soldSection.fadeIn(300);
            elements.soldEmpty.hide();
        } else {
            elements.soldSection.fadeIn(300);
            elements.soldEmpty.fadeIn(300);
        }
        
        // Add animation to cards with slight delay for each
        $(".product-card").each(function(index) {
            const $this = $(this);
            setTimeout(function() {
                $this.addClass("opacity-100 translate-y-0");
            }, 50 * index);
        });
    }
    
    function createProductCard(product, isSold) {
        const name = product.name || 'Untitled';
        const price = product.price || '$0.00';
        const imageUrl = product.imageUrl || '/static/images/placeholder.jpg';
        
        if (isSold) {
            // Template for sold products
            return `
            <div class="product-card opacity-0 translate-y-4 transition duration-500 transform group bg-black rounded-md p-4">
                <div class="relative">
                    <div class="w-full aspect-w-1 aspect-h-1 bg-gray-900 rounded-lg overflow-hidden">
                        <div class="absolute inset-0 bg-black bg-opacity-40 flex items-center justify-center">
                            <span class="bg-red-600 text-white px-3 py-1 rounded-full text-xs font-semibold">
                                SOLD
                            </span>
                        </div>
                        <img src="${imageUrl}" 
                             alt="${name}"
                             class="w-full h-full object-center object-cover grayscale opacity-80"
                             loading="lazy"
                             onerror="this.src='/static/images/placeholder.jpg'">
                    </div>
                    <div class="mt-4">
                        <h3 class="text-sm font-medium text-white group-hover:text-gray-300 transition">${name}</h3>
                    </div>
                </div>
            </div>
            `;
        } else {
            // Template for available products
            return `
            <div class="product-card opacity-0 translate-y-4 transition duration-500 transform group bg-black rounded-md p-4">
                <div class="relative">
                    <div class="w-full aspect-w-1 aspect-h-1 bg-gray-900 rounded-lg overflow-hidden">
                        <img src="${imageUrl}" 
                             alt="${name}"
                             class="w-full h-full object-center object-cover group-hover:scale-105 transition-transform duration-300"
                             loading="lazy"
                             onerror="this.src='/static/images/placeholder.jpg'">
                    </div>
                    <div class="mt-4 flex justify-between items-center">
                        <h3 class="text-sm font-medium text-white group-hover:text-gray-300 transition">${name}</h3>
                        <div class="bg-white text-black px-3 py-1 rounded-full font-bold text-sm">
                            ${price}
                        </div>
                    </div>
                </div>
            </div>
            `;
        }
    }

    function setupPagination(totalItems) {
        config.totalItems = totalItems;
        const totalPages = Math.ceil(totalItems / config.itemsPerPage);
        
        elements.pageInfo.text(`Page ${config.currentPage} of ${totalPages}`);
        elements.prevBtn.prop('disabled', config.currentPage <= 1);
        elements.nextBtn.prop('disabled', config.currentPage >= totalPages);
        
        if (totalPages > 1) {
            elements.pagination.fadeIn(300);
        } else {
            elements.pagination.hide();
        }
    }

    function handlePreviousPage() {
        if (config.currentPage > 1) {
            config.currentPage--;
            loadProducts();
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
    }

    function handleNextPage() {
        const totalPages = Math.ceil(config.totalItems / config.itemsPerPage);
        if (config.currentPage < totalPages) {
            config.currentPage++;
            loadProducts();
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
    }

    // UI State Helpers
    function showLoading() {
        elements.loading.fadeIn(200);
        elements.availableSection.hide();
        elements.soldSection.hide();
        elements.empty.hide();
        elements.pagination.hide();
    }

    function hideLoading() {
        elements.loading.fadeOut(300);
    }

    function showEmptyState(message = "No artworks available at the moment.") {
        elements.empty.html(`
            <svg class="mx-auto h-16 w-16 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1" 
                    d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p class="mt-6 text-gray-400 text-lg">${message}</p>
            <p class="text-gray-500 mt-2">Please check back soon for new additions.</p>
        `).fadeIn(300);
        
        elements.availableSection.hide();
        elements.soldSection.hide();
        elements.pagination.hide();
    }

    function hideEmptyState() {
        elements.empty.hide();
    }

    function showError(message) {
        showEmptyState(`
            <div class="text-red-500">
                <svg class="mx-auto h-16 w-16" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1" 
                        d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <p class="mt-4 text-lg">${message}</p>
            </div>
        `);
    }
});