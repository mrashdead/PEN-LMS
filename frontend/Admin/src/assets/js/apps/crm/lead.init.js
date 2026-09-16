import { icons, createIcons } from "lucide";

VirtualSelect.init({
  ele: '#statusSelect2',
  options: [
    { label: 'New', value: '1' },
    { label: 'Host', value: '2' },
    { label: 'Pending', value: '3' },
    { label: 'Host', value: '4' },
  ],
  selectedValue: 0
});
/**
 * LeadManager - A class to manage leads with drag-and-drop functionality
 */
class LeadManager {
  constructor() {
    this.leads = {
      new: [],
      hot: [],
      pending: [],
      lost: []
    };
    this.currentLeadId = null;
    this.drake = null;
    this.nextId = 1;
    this.imagePreview = null;

    // Initialize with sample data
    this.loadSampleData();
    this.initDragAndDrop();
    this.initEventListeners();
    this.renderAllContainers();
  }

  /**
   * Initialize drag and drop functionality using Dragula
   */
  initDragAndDrop() {
    const containers = Array.from(document.querySelectorAll('.lead-container'));

    this.drake = dragula(containers, {
      moves: (el, source, handle) => {
        return true; // Allow all elements to be moved
      }
    });

    // Handle drop events to update the lead status
    this.drake.on('drop', (el, target, source) => {
      const leadId = el.getAttribute('data-id');
      const newStatus = target.closest('[data-status]').getAttribute('data-status');
      const oldStatus = source.closest('[data-status]').getAttribute('data-status');

      if (oldStatus !== newStatus) {
        this.updateLeadStatus(parseInt(leadId), oldStatus, newStatus);
      }
    });
  }

  /**
   * Set up event listeners for UI interactions
   */
  initEventListeners() {
    // Lead form submission (create/edit)
    document.getElementById('leadForm').addEventListener('submit', (e) => {
      e.preventDefault();
      this.saveLeadFromForm();
    });

    // Delete confirmation
    document.getElementById('confirmDelete').addEventListener('click', () => {
      if (this.currentLeadId) {
        this.deleteLead(this.currentLeadId);
      }
    });

    // Image upload handling
    const imageInput = document.getElementById('imageInput');
    const uploadIcon = document.getElementById('uploadIcon');
    const avatarLabel = document.querySelector('label.avatar');

    imageInput.addEventListener('change', (e) => {
      if (e.target.files && e.target.files[0]) {
        const reader = new FileReader();

        reader.onload = (event) => {
          // Store the image data for saving with the lead
          this.imagePreview = event.target.result;

          // Update the avatar preview
          if (avatarLabel) {
            // Remove upload icon and show the image
            uploadIcon.style.display = 'none';

            // Check if there's already a preview image
            let previewImg = avatarLabel.querySelector('img.preview-image');

            if (!previewImg) {
              previewImg = document.createElement('img');
              previewImg.className = 'preview-image size-24 rounded-circle';
              avatarLabel.appendChild(previewImg);
            }

            previewImg.src = this.imagePreview;
          }
        };

        reader.readAsDataURL(e.target.files[0]);
      }
    });

    // Listen for edit and delete buttons (using event delegation)
    document.addEventListener('click', (e) => {
      if (e.target.closest('.link-custom-primary')) {
        // Edit button clicked
        const leadCard = e.target.closest('.p-3.bg-body.rounded');
        if (leadCard) {
          const leadId = parseInt(leadCard.getAttribute('data-id'));
          this.editLead(leadId);

          // Prevent the default action to avoid double modal trigger
          e.preventDefault();
        }
      } else if (e.target.closest('.link-custom-danger')) {
        // Delete button clicked
        const leadCard = e.target.closest('.p-3.bg-body.rounded');
        if (leadCard) {
          this.currentLeadId = parseInt(leadCard.getAttribute('data-id'));
        }
      }
    });
  }

  /**
   * Update a lead's status when it's dragged between containers
   */
  updateLeadStatus(leadId, oldStatus, newStatus) {
    // Find lead in old status array
    const leadIndex = this.leads[oldStatus].findIndex(lead => lead.id === leadId);
    if (leadIndex !== -1) {
      const lead = this.leads[oldStatus][leadIndex];

      // Remove from old status
      this.leads[oldStatus].splice(leadIndex, 1);

      // Add to new status
      lead.status = newStatus;
      this.leads[newStatus].push(lead);

      // Update the counters
      this.updateStatusCounters();
    }
  }

  /**
   * Create a new lead or update an existing one from form data
   */
  saveLeadFromForm() {
    const leadId = document.getElementById('leadId').value;
    const name = document.getElementById('fullName').value;
    const email = document.getElementById('email').value;
    const phone = document.getElementById('phone').value;
    const status = document.getElementById('statusSelect').value;
    const currentDate = new Date();

    const lead = {
      id: leadId ? parseInt(leadId) : this.nextId++,
      name: name,
      email: email,
      phone: phone,
      status: status,
      date: currentDate.toLocaleDateString('fa-IR', { day: 'numeric', month: 'long', year: 'numeric' }),
      time: currentDate.toLocaleTimeString('fa-IR', { hour: 'numeric', minute: '2-digit', hour12: true }),
      avatar: this.imagePreview || 'assets/images/avatar/user-1.png' // Use uploaded image or default
    };

    if (leadId) {
      // Update existing lead
      for (const status in this.leads) {
        const index = this.leads[status].findIndex(l => l.id === parseInt(leadId));
        if (index !== -1) {
          const oldStatus = this.leads[status][index].status;

          // If no new image was uploaded, keep existing avatar
          if (!this.imagePreview) {
            lead.avatar = this.leads[status][index].avatar;
          }

          this.leads[status].splice(index, 1);
          if (oldStatus !== lead.status) {
            this.leads[lead.status].push(lead);
          } else {
            this.leads[status].splice(index, 0, lead);
          }
          break;
        }
      }
    } else {
      // Add new lead
      this.leads[status].push(lead);
    }

    // Reset form and image preview
    document.getElementById('leadForm').reset();
    document.getElementById('leadId').value = '';
    document.getElementById('saveLeadBtn').textContent = 'افزودن رهبر';
    this.resetImagePreview();

    // Close modal
    const modalEl = document.getElementById('createLeadModal');
    const modal = window.bootstrap.Modal.getInstance(modalEl);
    modal.hide();

    // Re-render all containers
    this.renderAllContainers();
    this.updateStatusCounters();
  }

  /**
   * Reset the image preview to default state
   */
  resetImagePreview() {
    this.imagePreview = null;
    const avatarLabel = document.querySelector('label.avatar');
    const uploadIcon = document.getElementById('uploadIcon');

    if (avatarLabel) {
      // Show upload icon
      if (uploadIcon) {
        uploadIcon.style.display = 'inline-block';
      }

      // Remove preview image if it exists
      const previewImg = avatarLabel.querySelector('img.preview-image');
      if (previewImg) {
        previewImg.remove();
      }
    }
  }

  /**
   * Load lead for editing
   */
  editLead(leadId) {
    let lead = null;

    // Find lead in any status category
    for (const status in this.leads) {
      lead = this.leads[status].find(l => l.id === leadId);
      if (lead) break;
    }

    if (lead) {
      // Remove existing modal backdrops if any
      this.removeExtraModalBackdrops();

      // Populate form
      document.getElementById('leadId').value = lead.id;
      document.getElementById('fullName').value = lead.name;
      document.getElementById('email').value = lead.email;
      document.getElementById('phone').value = lead.phone;
      document.getElementById('statusSelect').value = lead.status;
      document.getElementById('saveLeadBtn').textContent = 'آپدیت رهبر';

      // Update avatar preview with the lead's current image
      this.updateAvatarPreview(lead.avatar);

      // Open modal
      const modalEl = document.getElementById('createLeadModal');
      const existingModal = window.bootstrap.Modal.getInstance(modalEl);

      if (existingModal) {
        existingModal.show();
      } else {
        const modal = new window.bootstrap.Modal(modalEl);
        modal.show();
      }
    }
  }

  /**
   * Update avatar preview with the specified image URL
   */
  updateAvatarPreview(imageUrl) {
    const avatarLabel = document.querySelector('label.avatar');
    const uploadIcon = document.getElementById('uploadIcon');

    if (avatarLabel) {
      // Hide upload icon
      if (uploadIcon) {
        uploadIcon.style.display = 'none';
      }

      // Check if there's already a preview image
      let previewImg = avatarLabel.querySelector('img.preview-image');

      if (!previewImg) {
        previewImg = document.createElement('img');
        previewImg.className = 'preview-image size-24 rounded-circle';
        avatarLabel.appendChild(previewImg);
      }

      previewImg.src = imageUrl;

      // Don't set imagePreview here as we don't want to force an update
      // unless the user actually changes the image
    }
  }

  /**
   * Remove extra modal backdrops that might accumulate
   */
  removeExtraModalBackdrops() {
    const backdrops = document.querySelectorAll('.modal-backdrop');
    if (backdrops.length > 0) {
      // Keep only one backdrop if multiple exist
      for (let i = 0; i < backdrops.length; i++) {
        backdrops[i].remove();
      }
    }
  }

  /**
   * Delete a lead
   */
  deleteLead(leadId) {
    for (const status in this.leads) {
      const index = this.leads[status].findIndex(lead => lead.id === leadId);
      if (index !== -1) {
        this.leads[status].splice(index, 1);
        break;
      }
    }

    this.renderAllContainers();
    this.updateStatusCounters();
    this.currentLeadId = null;
  }

  /**
   * Update the badge counters for each status
   */
  updateStatusCounters() {
    const statuses = ['new', 'hot', 'pending', 'lost'];

    statuses.forEach(status => {
      const count = this.leads[status].length;
      const badge = document.querySelector(`h6:has(+ .lead-simplebar[data-status="${status}"]) .badge`);
      if (badge) {
        badge.textContent = count;
      }
    });
  }

  /**
   * Render all lead containers
   */
  renderAllContainers() {
    const statuses = ['new', 'hot', 'pending', 'lost'];

    statuses.forEach(status => {
      const container = document.getElementById(`${status}-leads`);
      container.innerHTML = '';

      this.leads[status].forEach(lead => {
        container.appendChild(this.createLeadCard(lead));
      });
    });
  }

  /**
   * Create a lead card element
   */
  createLeadCard(lead) {
    const card = document.createElement('div');
    card.className = 'p-3 bg-body rounded';
    card.setAttribute('data-id', lead.id);

    card.innerHTML = `
          <div class="d-flex align-items-center gap-3 mb-2">
              <img src="${lead.avatar}" loading="lazy" alt="User Image" class="rounded-circle size-12">
              <div class="flex-grow-1">
                  <h6 class="mb-1">${lead.name}</h6>
                  <p class="fs-sm text-muted d-inline-flex align-items-center gap-1">
                      <i class="ri-time-line"></i>
                      ${lead.date} در
                      <span>${lead.time}</span>
                  </p>
              </div>
          </div>
          <div class="mb-2">
              <span class="text-muted">${lead.email}</span> <i class="ri-mail-line me-1"></i> 
          </div>
          <div>
              <i class="ri-phone-line me-1"></i> <span class="text-muted">${lead.phone}</span>
          </div>
          <div class="d-flex gap-3 mt-3">
              <a href="#!" class="link link-custom-primary">ویرایش</a>
              <a href="#!" class="link link-custom-danger" data-bs-toggle="modal" data-bs-target="#deleteModal">حذف</a>
          </div>
      `;

    return card;
  }

  /**
   * Load sample data for initial display
   */
  loadSampleData() {
    // Sample data based on the provided HTML
    const sampleLeads = [
      // New leads
      {
        id: this.nextId++,
        name: 'چارلز کارتر',
        email: 'charles@gmail.com',
        phone: '+(145) 0128 2303',
        status: 'new',
        date: '10 خرداد 1403',
        time: '1:30 بعد از ظهر',
        avatar: 'assets/images/avatar/user-1.png'
      },
      {
        id: this.nextId++,
        name: 'دایانا داوسون',
        email: 'diana@gmail.com',
        phone: '+(145) 0128 2308',
        status: 'new',
        date: '11 خرداد 1403',
        time: '9:00 بعد از ظهر',
        avatar: 'assets/images/avatar/user-2.png'
      },
      {
        id: this.nextId++,
        name: 'لیام لی',
        email: 'liam@gmail.com',
        phone: '+(145) 0128 2310',
        status: 'new',
        date: '12 خرداد 1403',
        time: '11:00 صبح',
        avatar: 'assets/images/avatar/user-3.png'
      },
      {
        id: this.nextId++,
        name: 'اما ادوارز',
        email: 'emma@gmail.com',
        phone: '+(145) 0128 2311',
        status: 'new',
        date: '13 خرداد 1403',
        time: '10:45 صبح',
        avatar: 'assets/images/avatar/user-4.png'
      },
      {
        id: this.nextId++,
        name: 'نوح نلسون',
        email: 'noah@gmail.com',
        phone: '+(145) 0128 2312',
        status: 'new',
        date: '14 خرداد 1403',
        time: '1:15 بعد از ظهر',
        avatar: 'assets/images/avatar/user-5.png'
      },

      // Hot leads
      {
        id: this.nextId++,
        name: 'اَشتون اَبیگل',
        email: 'ashton@gmail.com',
        phone: '+(145) 0128 2301',
        status: 'hot',
        date: '8 خرداد 1403',
        time: '3:45 بعد از ظهر',
        avatar: 'assets/images/avatar/user-6.png'
      },
      {
        id: this.nextId++,
        name: 'گریس گریفن',
        email: 'grace@gmail.com',
        phone: '+(145) 0128 2313',
        status: 'hot',
        date: '10 خرداد 1403',
        time: '2:00 بعد از ظهر',
        avatar: 'assets/images/avatar/user-7.png'
      },
      {
        id: this.nextId++,
        name: 'هنری هیوز',
        email: 'henry@gmail.com',
        phone: '+(145) 0128 2314',
        status: 'hot',
        date: '12 خرداد 1403',
        time: '4:30 بعد از ظهر',
        avatar: 'assets/images/avatar/user-8.png'
      },
      {
        id: this.nextId++,
        name: 'ایوی اینگرام',
        email: 'ivy@gmail.com',
        phone: '+(145) 0128 2315',
        status: 'hot',
        date: '13 خرداد 1403',
        time: '5:00 بعد از ظهر',
        avatar: 'assets/images/avatar/user-9.png'
      },
      {
        id: this.nextId++,
        name: 'جکی جانسون',
        email: 'jackie@gmail.com',
        phone: '+(145) 0128 2316',
        status: 'hot',
        date: '14 خرداد 1403',
        time: '6:15 بعد از ظهر',
        avatar: 'assets/images/avatar/user-10.png'
      },

      // Pending leads
      {
        id: this.nextId++,
        name: 'بتانی بِنت',
        email: 'bethany@gmail.com',
        phone: '+(145) 0128 2302',
        status: 'pending',
        date: '9 خرداد 1403',
        time: '10:00 بعد از ظهر',
        avatar: 'assets/images/avatar/user-11.png'
      },
      {
        id: this.nextId++,
        name: 'کوین کینگ',
        email: 'kevin@gmail.com',
        phone: '+(145) 0128 2317',
        status: 'pending',
        date: '10 خرداد 1403',
        time: '8:45 بعد از ظهر',
        avatar: 'assets/images/avatar/user-12.png'
      },
      {
        id: this.nextId++,
        name: 'لونا لِین',
        email: 'luna@gmail.com',
        phone: '+(145) 0128 2318',
        status: 'pending',
        date: '11 خرداد 1403',
        time: '2:30 بعد از ظهر',
        avatar: 'assets/images/avatar/user-13.png'
      },
      {
        id: this.nextId++,
        name: 'میسون میلر',
        email: 'mason@gmail.com',
        phone: '+(145) 0128 2319',
        status: 'pending',
        date: '12 خرداد 1403',
        time: '4:00 بعد از ظهر',
        avatar: 'assets/images/avatar/user-14.png'
      },
      {
        id: this.nextId++,
        name: 'نورا نیکلاس',
        email: 'nora@gmail.com',
        phone: '+(145) 0128 2320',
        status: 'pending',
        date: '13 خرداد 1403',
        time: '12:15 بعد از ظهر',
        avatar: 'assets/images/avatar/user-15.png'
      },

      // Lost leads
      {
        id: this.nextId++,
        name: 'ایتان ایوانس',
        email: 'ethan@gmail.com',
        phone: '+(145) 0128 2305',
        status: 'lost',
        date: '12 خرداد 1403',
        time: '11:15 بعد از ظهر',
        avatar: 'assets/images/avatar/user-16.png'
      },
      {
        id: this.nextId++,
        name: 'اولیویا اوِنز',
        email: 'olivia@gmail.com',
        phone: '+(145) 0128 2321',
        status: 'lost',
        date: '13 خرداد 1403',
        time: '7:45 بعد از ظهر',
        avatar: 'assets/images/avatar/user-17.png'
      },
      {
        id: this.nextId++,
        name: 'پیتر پارکر',
        email: 'peter@gmail.com',
        phone: '+(145) 0128 2322',
        status: 'lost',
        date: '14 خرداد 1403',
        time: '9:30 بعد از ظهر',
        avatar: 'assets/images/avatar/user-18.png'
      },
      {
        id: this.nextId++,
        name: 'ملکه کوئین',
        email: 'quinn@gmail.com',
        phone: '+(145) 0128 2323',
        status: 'lost',
        date: '15 خرداد 1403',
        time: '3:00 بعد از ظهر',
        avatar: 'assets/images/avatar/user-19.png'
      },
      {
        id: this.nextId++,
        name: 'رایان راجرز',
        email: 'ryan@gmail.com',
        phone: '+(145) 0128 2324',
        status: 'lost',
        date: '16 خرداد 1403',
        time: '5:45 بعد از ظهر',
        avatar: 'assets/images/avatar/user-20.png'
      }
    ];


    // Distribute sample leads into their respective status categories
    sampleLeads.forEach(lead => {
      this.leads[lead.status].push(lead);
    });
  }
}

// Initialize the lead manager when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  createIcons({ icons });

  // Add an event listener to clear modal backdrops when a modal is hidden
  document.addEventListener('hidden.bs.modal', function () {
    const backdrops = document.querySelectorAll('.modal-backdrop');
    if (backdrops.length > 0) {
      backdrops.forEach(backdrop => backdrop.remove());
    }
  });

  window.leadManager = new LeadManager();
});