$(document).ready(function() {
   // Tab switching
   $('#sketch-sales-tab').click(function() {
       $(this).addClass('border-blue-500 text-blue-600').removeClass('border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300');
       $('#image-sketches-tab').removeClass('border-blue-500 text-blue-600').addClass('border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300');
       $('#sketch-sales-section').removeClass('hidden');
       $('#image-sketches-section').addClass('hidden');
   });

   $('#image-sketches-tab').click(function() {
       $(this).addClass('border-blue-500 text-blue-600').removeClass('border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300');
       $('#sketch-sales-tab').removeClass('border-blue-500 text-blue-600').addClass('border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300');
       $('#image-sketches-section').removeClass('hidden');
       $('#sketch-sales-section').addClass('hidden');
   });

   // Handle delete confirmation
   $('form[method="post"]').submit(function(e) {
       if ($(this).find('input[name="method"]').val() === 'delete') {
           if (!confirm('Are you sure you want to delete this item?')) {
               e.preventDefault();
           }
       }
   });
});

// Modal functions
function openSketchSaleModal() {
   document.getElementById('sketch-sale-modal').classList.remove('hidden');
}

function openImageSketchModal() {
   document.getElementById('image-sketch-modal').classList.remove('hidden');
}

function closeModal(modalId) {
   document.getElementById(modalId).classList.add('hidden');
}

function submitSketchSale() {
   const form = document.getElementById('sketch-sale-form');
   const formData = new FormData(form);
   
   fetch('/admin/sketch_sales', {
       method: 'POST',
       body: formData
   })
   .then(response => {
       if (response.redirected) {
           window.location.href = response.url;
       }
   })
   .catch(error => {
       console.error('Error:', error);
   });
}

function submitImageSketch() {
   const form = document.getElementById('image-sketch-form');
   const formData = new FormData(form);
   
   fetch('/admin/image_sketches', {
       method: 'POST',
       body: formData
   })
   .then(response => {
       if (response.redirected) {
           window.location.href = response.url;
       }
   })
   .catch(error => {
       console.error('Error:', error);
   });
}