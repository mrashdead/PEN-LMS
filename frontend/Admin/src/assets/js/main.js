/*
Template Name: Domiex - Admin & Dashboard Template
Author: Spring Code
Version: 1.0.0
File: main Js File
*/

// translation functionality
let translations = {};

// Load translations from JSON file
async function loadTranslations(lang) {
  if (lang) {
    try {
      lang = lang.replace(/"/g, '');
      const response = await fetch('assets/lang/' + lang + '.json');
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      const data = await response.json();
      translations = data;
    } catch (error) {
      console.error('Error loading translations:', error);
    }
  }
}

async function applyLanguage(lang) {
  await loadTranslations(lang);
  const elements = document.querySelectorAll('[data-translate]');
  elements.forEach(element => {
    const key = element.getAttribute('data-translate');
    if (translations[key]) {
      element.textContent = translations[key];
    }
  });

  // Update the dropdown button
  const dropdownButton = document.querySelector('#languageButton');
  const selectedFlag = document.querySelector(`.dropdown-item[data-lang="${lang}"] img`);
  if (selectedFlag) {
    dropdownButton.innerHTML = selectedFlag.outerHTML;
  }

  // Save selected language to sessionStorage
  sessionStorage.setItem('selectedLanguage', lang);
}

// Load saved language on page load
const savedLanguage = sessionStorage.getItem('selectedLanguage') || 'fa';
applyLanguage(savedLanguage);

// on language change
const languageDropdowns = document.querySelectorAll('a[data-lang]');
languageDropdowns.forEach(dropdown => {
  dropdown.addEventListener('click', () => {
    const lang = dropdown.getAttribute('data-lang');
    applyLanguage(lang);
  })
});

// Get the navbar and sidebar elements
const elements = [
  { id: 'main-topbar', stickyClass: 'nav-sticky' },
  { id: 'main-sidebar', stickyClass: 'sidebar-sticky' }
];

// Store the offset positions of the elements
const offsets = elements.map(element => {
  const el = document.getElementById(element.id);
  if(el)
    return { offsetTop: el.offsetTop, el, stickyClass: element.stickyClass };
  else
    return { offsetTop: 0, el: null, stickyClass: '' };
});

// Function to add/remove the sticky class for multiple elements
function toggleStickyElements() {
  offsets.forEach(({ offsetTop, el, stickyClass }) => {
    if (window.scrollY >= offsetTop && window.scrollY > 0) {
      el.classList.add(stickyClass);
    } else {
      el.classList.remove(stickyClass);
    }
  });
}

// Add scroll event listener
window.addEventListener('scroll', toggleStickyElements);

document.addEventListener("DOMContentLoaded", function () {
  // Settings to manage
  const settings = [
    "data-layout",
    "data-nav-type",
    "data-bs-theme",
    "data-sidebar",
    "data-sidebar-colors",
    "data-content-width",
    "data-colors",
    "data-profile-sidebar",
    "data-topbar-colors"
  ];

  const documentElement = document.documentElement;
  const settingsModal = document.getElementById('settingsModal');
  const navigationType = document.getElementById('navigationType');
  const profileSidebar = document.getElementById('profileSidebar');
  const sidebarSizes = document.getElementById('sidebarSizes');
  // set active menu
  let currentPath = window.location.pathname; // Get the current pathname
  if (currentPath === '/')
    currentPath = 'index.html';

  // if currentPath start with / then remove it
  if (currentPath.startsWith('/'))
    currentPath = currentPath.substring(1);
  // currentPath = currentPath.replace('domiex/bootstrap/light/', ''); // to activate the menu in subfolder folder

  // Apply stored values
  settings.forEach(setting => {
    const savedValue = sessionStorage.getItem(setting) || documentElement.getAttribute(setting);
    if (savedValue) {
      documentElement.setAttribute(setting, savedValue);

      if (setting === 'data-layout') {
        updateLayout(savedValue);
      }

      // Check the corresponding radio button
      const radio = document.querySelector(`input[name="${setting}"][value="${savedValue}"]`);
      if (radio) radio.checked = true;
    }
    if (sessionStorage.getItem('data-profile-sidebar') === 'true') {
      documentElement.setAttribute('data-profile-sidebar', 'true');
      sessionStorage.setItem('data-profile-sidebar', 'true');
    } else {
      documentElement.removeAttribute('data-profile-sidebar');
      sessionStorage.removeItem('data-profile-sidebar');
    }
  });

  function updateLayout(settingValue) {
    if (navigationType) {
      navigationType.style.display = settingValue === 'modern' ? 'block' : 'none';
    }
    if (profileSidebar) {
      profileSidebar.style.display = settingValue === 'horizontal' ? 'none' : 'block';
    }
    if (sidebarSizes) {
      sidebarSizes.style.display = settingValue === 'horizontal' ? 'none' : 'block';
    }
    if (settingValue === 'horizontal') {
      documentElement.setAttribute('data-sidebar', 'large');
      document.querySelector('input[name="data-sidebar"][value="large"]').checked = true;
      sessionStorage.setItem('data-sidebar', 'large');
    } else {
      setActiveMenu();
    }
  }

  // Event listeners for radio buttons
  if (settingsModal) {
    const radioButtons = settingsModal.querySelectorAll("input[type='radio']");
    radioButtons.forEach(input => {
      input.addEventListener("change", function () {
        const settingName = this.name;
        const settingValue = this.value;

        if (settingName === 'data-layout')
          updateLayout(settingValue);

        if (settingName === "data-bs-theme" && settingValue === 'auto') {
          checkDarkMode();
        } else {
          documentElement.setAttribute(settingName, settingValue);
          sessionStorage.setItem(settingName, settingValue);
        }
      });
    });

    const checkboxes = settingsModal.querySelectorAll("input[type='checkbox']");
    checkboxes.forEach(input => {
      input.addEventListener("change", function () {
        const settingName = this.name;
        const settingValue = this.checked ? 'true' : '';
        if (settingValue === 'true') {
          documentElement.setAttribute(settingName, settingValue);
          sessionStorage.setItem(settingName, settingValue);
        } else {
          documentElement.removeAttribute(settingName);
          sessionStorage.removeItem(settingName);
        }
      });
    });
  }

  // Auto Dark mode setting
  function checkDarkMode() {
    const colorSchemeMediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const mode = colorSchemeMediaQuery.matches ? 'dark' : 'light';
    documentElement.setAttribute('data-bs-theme', mode);
    sessionStorage.setItem('data-bs-theme', mode);
  }

  const resetButton = document.getElementById("resetLayout");
  if (resetButton) {
    resetButton.addEventListener("click", resetToDefault);
  }

  function resetToDefault() {
    sessionStorage.clear();
    location.reload();
  }

  // Function to add the active class to the matching menu item
  function setActiveMenu() {
    const navLinks = document.querySelectorAll('.navbar-nav-menu a.nav-link'); // Select all menu links
    let currentMenu = null;
    navLinks.forEach(link => {
      const linkPath = link.getAttribute('href'); // Normalize the href attribute

      // Check if the link's href matches the current path
      if (linkPath === currentPath) {
        link.classList.add('active'); // Add the active class to the matching link
        currentMenu = link; // Store the current menu item
        // Ensure the parent collapse element is expanded
        const parentCollapse = link.closest('.collapse');
        if (parentCollapse)
          parentActivate(parentCollapse, link);
      } else {
        link.classList.remove('active'); // Remove the active class from non-matching links
      }
    });
    // scroll to the active link
    const activeLink = document.querySelector('.navbar-nav-menu a.nav-link.active');
    if (activeLink) {
      // make sidebar scroll to active link
      setTimeout(() => {
        const sidebar = document.getElementById('main-sidebar').querySelector('.simplebar-content-wrapper');
        if (sidebar && currentMenu.offsetTop > window.innerHeight) {
          sidebar.scrollTop = currentMenu.offsetTop - (window.innerHeight / 2);
        }
      }, 0);
    }
  }

  function parentActivate(parentCollapse, link) {
    parentCollapse.classList.add('show'); // Add the 'show' class to expand the collapse
    // Ensure the parent nav-item is active
    if (!parentCollapse.closest('li').classList.contains('nav-item')) {
      const activeParent = parentCollapse.closest('li').firstElementChild;
      activeParent.classList.add('active')
      parentActivate(activeParent.closest('.collapse'), activeParent)
    } else {
      const parentNavItem = link.closest('.nav-item');
      if (parentNavItem) {
        parentNavItem.firstElementChild.classList.add('active'); // Add the active class to the parent nav-item
      }
    }
  }

  // Call the function to set the active menu
  setActiveMenu();

  // sidebar collapse functionality
  const toggleSidebarButton = document.getElementById('toggleSidebar');
  const mainSidebar = document.getElementById('main-sidebar');
  const sidebarBackdrop = document.getElementById('sidebar-backdrop');
  toggleSidebarButton?.addEventListener("click", toggleSidebar);
  window.addEventListener('resize', toggleSidebarResize);

  function toggleSidebarResize() {
    const windowWidth = window.innerWidth;
    if (windowWidth <= 997.98) {
      document.querySelector('input[name="data-sidebar"][value="large"]').checked = true;
      documentElement.setAttribute('data-sidebar', 'large');
      removeSidebarBackdrop();
    } else if (windowWidth <= 1199.98) {
      if (documentElement.getAttribute('data-layout') !== 'horizontal') {
        mainSidebar.classList.add('show');
        documentElement.setAttribute('data-sidebar', 'small');
        removeAndUpdateActive();
      } else {
        document.querySelector('input[name="data-sidebar"][value="large"]').checked = true;
      }
    } else {
      document.querySelector('input[name="data-sidebar"][value="large"]').checked = true;
    }
  }

  function toggleSidebar() {
    const windowWidth = window.innerWidth;
    if (windowWidth <= 997.98) {
      documentElement.setAttribute('data-sidebar', 'large');
      document.querySelector('input[name="data-sidebar"][value="large"]').checked = true;
      mainSidebar?.classList.toggle('show');
      sidebarBackdrop?.classList.toggle('d-block');
    } else if (windowWidth <= 1199.98) {
      if (documentElement.getAttribute('data-layout') !== 'horizontal') {
        document.body.classList.toggle('sidebar-hidden');
        documentElement.setAttribute('data-sidebar', 'small');
        removeAndUpdateActive();
        sessionStorage.setItem('data-sidebar', 'small');
      } else {
        documentElement.setAttribute('data-sidebar', 'large');
        document.querySelector('input[name="data-sidebar"][value="large"]').checked = true;
        mainSidebar?.classList.toggle('show');
      }
      removeSidebarBackdrop();
    } else {
      const sidebarSize = documentElement.getAttribute('data-sidebar') ?? 'large';
      const updatedSidebar = (sidebarSize === "large") ? 'small' : 'large';
      documentElement.setAttribute('data-sidebar', updatedSidebar);
      sessionStorage.setItem('data-sidebar', updatedSidebar);
      if (updatedSidebar === 'small')
        removeAndUpdateActive();
      removeSidebarBackdrop();
    }
  }

  if (window.innerWidth < 1199.98)
    toggleSidebarResize();

  function removeSidebarBackdrop() {
    mainSidebar?.classList.remove('show');
    sidebarBackdrop?.classList.remove('d-block');
  }
  sidebarBackdrop?.addEventListener("click", function () {
    removeSidebarBackdrop();
  });

  // Topbar dark mode button click functionality
  const darkModeButton = document.getElementById('darkModeButton');
  darkModeButton?.addEventListener("click", toggleDarkMode);

  function toggleDarkMode() {
    const currentMode = documentElement.getAttribute('data-bs-theme') ?? 'light';
    const setMode = currentMode === 'light' ? 'dark' : 'light';
    documentElement.setAttribute('data-bs-theme', setMode);
    sessionStorage.setItem('data-bs-theme', setMode);
  }

  function getRightTopPosition(element, isLtr) {
    const rect = element.getBoundingClientRect();
    const dropdown = element.querySelector('.nav-menu-sub').getBoundingClientRect();
    const windowHeight = window.innerHeight;
    const windowWidth = window.innerWidth;

    if ((rect.left + rect.width) + dropdown.width > windowWidth && documentElement.getAttribute('data-layout') === 'horizontal') {
      return {
        top: rect.top + 5,
        right: (rect.left - dropdown.width)
      }
    }
    if (rect.y + dropdown.height > windowHeight) {
      return {
        left: rect.left + rect.right,
        right: isLtr === 'ltr' ? rect.left : rect.width + 28,
        bottom: 0
      }
    }
    return {
      top: rect.y,
      left: rect.left < 20 ? rect.left * 2 + rect.width : rect.left + rect.width - 1,
      right: isLtr === 'ltr' ? rect.left : window.innerWidth - rect.left - 11
    }
  }

  function getBottomLeftPosition(element, isLtr) {
    const rect = element.getBoundingClientRect();
    const dropdown = element.querySelector('.nav-menu-sub').getBoundingClientRect();
    const windowWidth = window.innerWidth;
    if (rect.left + dropdown.width > windowWidth) {
      return {
        top: (rect.top + rect.height) + 3,
        right: isLtr === 'ltr' ? (rect.right - dropdown.width) : 0
      }
    }
    return {
      top: (rect.bottom + 3),
      left: rect.left
    }
  }

  function removeAndUpdateActive(item = null) {
    if (documentElement.getAttribute('data-sidebar') === 'small' || documentElement.getAttribute('data-layout') === 'horizontal') {
      const allLi = document.querySelectorAll('#navbar-menu-list .navbar-nav-menu > li.nav-item');
      allLi.forEach(li => {
        if (!li.contains(item)) {
          if (item) {
            const a = li.querySelector('a.nav-link');
            a.classList.remove('active');
          }
          const collapse = li.querySelectorAll('.collapse.show');
          collapse?.forEach(collapse => {
            collapse.classList.remove('show');
            collapse.previousElementSibling?.setAttribute("aria-expanded", "false");
          });
        } else {
          if (item.parentElement.closest(".collapse.show")) {
            const collapse = item.parentElement.closest(".collapse.show");
            const allCollapse = collapse.querySelectorAll('.collapse.show');
            allCollapse.forEach(collapse => {
              collapse.classList.remove('show');
              collapse.previousElementSibling?.setAttribute("aria-expanded", "false");
            });
          }
          li.querySelector('a.nav-link').classList.add('active');
        }
      });
    }
  }

  // small sidebar dropdown custom position
  const menuList = document.getElementById('navbar-menu-list');
  const menus = menuList?.querySelectorAll('a.nav-link');
  (menus || []).forEach(item => {
    item.addEventListener('click', (e) => {
      if (documentElement.getAttribute('data-sidebar') === 'small' || documentElement.getAttribute('data-layout') === 'horizontal') {
        removeAndUpdateActive(item);
        const dropdown = item.nextElementSibling?.firstElementChild;
        const alignTo = item.getAttribute("data-position") || 'left';
        const isLtr = document.documentElement.getAttribute('dir');
        let position = '';
        const isSubDropdown = item.closest('li').classList.contains('nav-item');
        if (documentElement.getAttribute('data-layout') === 'horizontal' && isSubDropdown) {
          position = getBottomLeftPosition(item.parentElement, isLtr);
        } else if (alignTo === 'right-top')
          position = getRightTopPosition(item.parentElement, isLtr);
        if (dropdown && position) {
          if (position.top) {
            dropdown.style.top = position.top + 'px';
            dropdown.style.bottom = 'auto';
          } else {
            dropdown.style.bottom = position.bottom + 'px';
            dropdown.style.top = 'auto';
          }
          if (isLtr === 'ltr')
            dropdown.style.left = (position.left ?? position.right) + 1 + 'px';
          else
            dropdown.style.right = (position.right) + 1 + 'px';
        }
      }
    });
  })
  removeAndUpdateActive();
});

window.addEventListener('click', function (e) {
  if (document.documentElement.getAttribute('data-sidebar') === 'small' || document.documentElement.getAttribute('data-layout') === 'horizontal') {
    const target = e.target.closest('#navbar-menu-list');
    if (!target) {
      const dropdowns = document.querySelectorAll('.collapse.show');
      dropdowns.forEach(dropdown => {
        dropdown.classList.remove('show');
        dropdown.previousElementSibling?.setAttribute("aria-expanded", "false");
      });
    }
  }
});