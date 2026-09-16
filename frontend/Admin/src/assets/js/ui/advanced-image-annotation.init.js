// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
  const commentInput = document.getElementById('comment-input');
  const listGroup = document.querySelector('.list-group');
  const dropdownMenu = document.querySelector('.dropdown-menu');
  const commentContent = document.querySelector('.comment-content');
  
  function toggleDropdown() {
      dropdownMenu.classList.toggle('show');
  }
  
  commentInput.addEventListener('keypress', function(event) {
      if (event.key === 'Enter' && this.value.trim() !== '') {
          const newComment = document.createElement('div');
          newComment.className = 'list-group-item';
          newComment.textContent = this.value.trim();
          
          const inputContainer = document.querySelector('.input-container');
          listGroup.insertBefore(newComment, inputContainer);
          
          this.value = '';
          commentContent.scrollTop = commentContent.scrollHeight;
      }
  });
  
  document.addEventListener('click', function(event) {
      if (!dropdownMenu.contains(event.target) && 
          !event.target.matches('.dropdown-toggle')) {
          dropdownMenu.classList.remove('show');
      }
  });
  
  if (typeof SimpleBar === 'function' && !commentContent.querySelector('.simplebar-content-wrapper')) {
      new SimpleBar(commentContent);
  }
});