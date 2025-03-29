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
               <div class="group relative">
                   <div class="w-full min-h-80 bg-gray-200 aspect-w-1 aspect-h-1 rounded-md overflow-hidden group-hover:opacity-75 lg:h-80 lg:aspect-none">
                       <div class="relative h-full">
                           <img src="${item.photo_image || '/static/images/placeholder.jpg'}" 
                                alt="Original photo for ${item.description || 'artwork'}"
                                class="w-full h-full object-center object-cover absolute inset-0"
                                loading="lazy"
                                onerror="this.src='/static/images/placeholder.jpg'">
                           <img src="${item.sketch_image || '/static/images/placeholder.jpg'}" 
                                alt="Sketch of ${item.description || 'artwork'}"
                                class="w-full h-full object-center object-cover absolute inset-0 opacity-0 hover:opacity-100 transition-opacity duration-300"
                                loading="lazy"
                                onerror="this.src='/static/images/placeholder.jpg'">
                       </div>
                   </div>
                   <div class="mt-4">
                       <h3 class="text-sm text-gray-700">${item.description || 'Untitled artwork'}</h3>
                   </div>
               </div>
           `;
       });

       elements.container.append(portfolioElements.join('')).show();
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