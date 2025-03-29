$(document).ready(function() {
    // Configuration
    const config = {
        itemsPerPage: 12,
        currentPage: 1,
        totalItems: 0,
        isLoading: false,
        isInitialLoad: true
    };

    // DOM Elements
    const elements = {
        container: $('#products-container'),
        loading: $('#loading-indicator'),
        empty: $('#empty-state'),
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
        elements.container.empty();

        if (!products || products.length === 0) {
            showEmptyState();
            return;
        }

        hideEmptyState();
        
        const productElements = products.map(product => {
            return `
                <div class="group relative">
                    <div class="w-full min-h-80 bg-gray-200 aspect-w-1 aspect-h-1 rounded-md overflow-hidden group-hover:opacity-75 lg:h-80 lg:aspect-none">
                        <img src="${product.imageUrl || '/static/images/placeholder.jpg'}" 
                             alt="${product.name || 'Artwork'}"
                             class="w-full h-full object-center object-cover lg:w-full lg:h-full"
                             loading="lazy"
                             onerror="this.src='/static/images/placeholder.jpg'">
                    </div>
                    <div class="mt-4 flex justify-between">
                        <div>
                            <h3 class="text-sm text-gray-700">${product.name || 'Untitled'}</h3>
                            <p class="mt-1 text-sm ${product.is_sold ? 'text-red-500' : 'text-green-500'}">
                                ${product.is_sold ? 'Sold' : 'Available'}
                            </p>
                        </div>
                        <p class="text-sm font-medium text-gray-900">
                            ${product.price || '$0.00'}
                        </p>
                    </div>
                </div>
            `;
        });

        elements.container.append(productElements.join('')).show();
    }

    function setupPagination(totalItems) {
        config.totalItems = totalItems;
        const totalPages = Math.ceil(totalItems / config.itemsPerPage);
        
        elements.pageInfo.text(`Page ${config.currentPage} of ${totalPages}`);
        elements.prevBtn.prop('disabled', config.currentPage <= 1);
        elements.nextBtn.prop('disabled', config.currentPage >= totalPages);
        
        elements.pagination.show();
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
        elements.loading.show();
        elements.container.hide();
        elements.empty.hide();
        elements.pagination.hide();
    }

    function hideLoading() {
        elements.loading.fadeOut(200);
    }

    function showEmptyState(message = "No products available at the moment.") {
        elements.empty.html(`<p class="text-gray-500">${message}</p>`).show();
        elements.container.hide();
        elements.pagination.hide();
    }

    function hideEmptyState() {
        elements.empty.hide();
    }

    function showError(message) {
        elements.empty.html(`<p class="text-red-500">${message}</p>`);
        showEmptyState();
    }
});