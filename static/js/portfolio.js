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
       container: $('#portfolio-container'),
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
       
       // Check if initialPortfolio exists and is valid
       if (window.initialPortfolio && Array.isArray(initialPortfolio) && initialPortfolio.length > 0) {
           setTimeout(() => {
               renderPortfolioItems(initialPortfolio);
               setupPagination(initialPortfolio.length);
               hideLoading();
               config.isInitialLoad = false;
           }, 300);
       } else {
           loadPortfolioItems();
       }
   }

   function loadPortfolioItems() {
       if (config.isLoading) return;
       
       config.isLoading = true;
       if (!config.isInitialLoad) {
           showLoading();
       }

       $.ajax({
           url: `/api/portfolio?page=${config.currentPage}&limit=${config.itemsPerPage}`,
           method: 'GET',
           dataType: 'json',
           success: function(data) {
               if (data && data.items) {
                   renderPortfolioItems(data.items);
                   setupPagination(data.total || data.items.length);
               } else {
                   showEmptyState();
               }
           },
           error: function(xhr, status, error) {
               console.error("Error loading portfolio:", status, error);
               showError("Failed to load portfolio items. Please try again later.");
           },
           complete: function() {
               config.isLoading = false;
               config.isInitialLoad = false;
               hideLoading();
           }
       });
   }

   function renderPortfolioItems(items) {
        elements.container.empty();

        if (!items || items.length === 0) {
            showEmptyState();
            return;
        }

        hideEmptyState();
        
        const portfolioElements = items.map(item => {
            return `
                <div class="group relative portfolio-item bg-black rounded-md p-4">
                    <div class="w-full min-h-80 bg-gray-200 aspect-w-1 aspect-h-1 rounded-md overflow-hidden lg:h-80 lg:aspect-none relative">
                        <!-- Original image (hidden by default) -->
                        <img src="${item.photo_image || '/static/images/placeholder.jpg'}" 
                            alt="Original photo for ${item.description || 'artwork'}"
                            class="w-full h-full object-center object-cover absolute inset-0 transition-opacity duration-300 original-image opacity-0"
                            loading="lazy"
                            onerror="this.src='/static/images/placeholder.jpg'">
                        
                        <!-- Sketch image (visible by default) -->
                        <img src="${item.sketch_image || '/static/images/placeholder.jpg'}" 
                            alt="Sketch of ${item.description || 'artwork'}"
                            class="w-full h-full object-center object-cover absolute inset-0 transition-opacity duration-300 sketch-image opacity-100"
                            loading="lazy"
                            onerror="this.src='/static/images/placeholder.jpg'">
                        
                        <!-- Toggle button with photo icon (since sketch is shown first) -->
                        <button class="absolute bottom-2 right-2 bg-white bg-opacity-80 rounded-full p-2 shadow-md toggle-sketch-btn"
                                aria-label="Show original photo"
                                data-showing="sketch">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                            </svg>
                        </button>
                    </div>
                    <div class="mt-4">
                        <h3 class="text-sm text-white">${item.description || 'Untitled artwork'}</h3>
                    </div>
                </div>
            `;
        });

        elements.container.append(portfolioElements.join('')).show();
        
        // Click handler for toggle buttons
        $('.toggle-sketch-btn').click(function(e) {
            e.stopPropagation();
            
            const button = $(this);
            const item = button.closest('.portfolio-item');
            const originalImg = item.find('.original-image');
            const sketchImg = item.find('.sketch-image');
            
            // Toggle visibility
            if (button.attr('data-showing') === 'sketch') {
                // Switch to showing photo
                originalImg.css('opacity', '1');
                sketchImg.css('opacity', '0');
                button.attr('data-showing', 'photo');
                button.attr('aria-label', 'Show sketch');
                button.html(`<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01" />
                </svg>`);
            } else {
                // Switch to showing sketch
                originalImg.css('opacity', '0');
                sketchImg.css('opacity', '1');
                button.attr('data-showing', 'sketch');
                button.attr('aria-label', 'Show original photo');
                button.html(`<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>`);
            }
        });
        
        // Click handler for document to reset when clicking outside
        $(document).click(function() {
            $('.portfolio-item').each(function() {
                const button = $(this).find('.toggle-sketch-btn');
                if (button.attr('data-showing') === 'photo') {
                    $(this).find('.original-image').css('opacity', '0');
                    $(this).find('.sketch-image').css('opacity', '1');
                    button.attr('data-showing', 'sketch');
                    button.attr('aria-label', 'Show original photo');
                    button.html(`<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>`);
                }
            });
        });
        
        // Prevent document click when clicking inside portfolio items
        $('.portfolio-item').click(function(e) {
            e.stopPropagation();
        });
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
           loadPortfolioItems();
           window.scrollTo({ top: 0, behavior: 'smooth' });
       }
   }

   function handleNextPage() {
       const totalPages = Math.ceil(config.totalItems / config.itemsPerPage);
       if (config.currentPage < totalPages) {
           config.currentPage++;
           loadPortfolioItems();
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

   function showEmptyState(message = "No portfolio items available at the moment.") {
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