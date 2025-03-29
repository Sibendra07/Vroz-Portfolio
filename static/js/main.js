// Mobile menu toggle
$(document).ready(function() {
   $('.mobile-menu-button').click(function() {
       $('.mobile-menu').toggleClass('hidden');
   });

   // Close mobile menu when clicking outside
   $(document).click(function(event) {
       if (!$(event.target).closest('.mobile-menu-button, .mobile-menu').length) {
           $('.mobile-menu').addClass('hidden');
       }
   });
});