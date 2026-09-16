import { createIcons, icons } from "lucide";
//Report Type Select
VirtualSelect.init({
  ele: "#reportTypeSelect",
  options: [
    { label: "ایکس ری", value: "X-Ray" },
    { label: "آزمایش خون", value: "Blood Test" },
    { label: "MRI", value: "MRI" },
    { label: "CT اسکن", value: "CT Scan" },
    { label: "سونوگرافی", value: "Ultrasound" },
  ],
  allowNewOption: true,
});

//Recommendations Select
VirtualSelect.init({
  ele: "#recommendationsSelect",
  options: [
    { label: "ناموجود", value: "N/A" },
    { label: "پیگیری لازم است", value: "Follow-up required" },
    { label: "مشورت با جراح", value: "Consult with surgeon" },
  ],
  allowNewOption: true,
});

//Status Select
VirtualSelect.init({
  ele: "#statusSelect",
  options: [
    { label: "تکمیل شده", value: "Completed" },
    { label: "در حال انجام", value: "In Progress" },
    { label: "در حال بررسی", value: "Pending" },
  ],
});

const reportData = [
  { type: "ایکس ری", date: "10 اردیبهشت 1403", doctor: "دکتر اسمیت", status: "در حال بررسی", statusClass: "bg-warning-subtle text-warning border-warning-subtle" },
  { type: "آزمایش خون", date: "17 فروردین 1403", doctor: "دکتر جانسون", status: "تکمیل شده", statusClass: "bg-success-subtle text-success border-success-subtle" },
  { type: "MRI", date: "16 بهمن 1402", doctor: "دکتر ویلیامز", status: "تکمیل شده", statusClass: "bg-success-subtle text-success border-success-subtle" },
  { type: "CT اسکن", date: "20 خرداد 1403", doctor: "دکتر براون", status: "در حال انجام", statusClass: "bg-secondary-subtle text-secondary border-secondary-subtle" },
  { type: "سونوگرافی", date: "29 دی 1402", doctor: "دکتر ویلسون", status: "تکمیل شده", statusClass: "bg-success-subtle text-success border-success-subtle" },
  { type: "اکوی قلب", date: "20 دی 1402", doctor: "دکتر لی", status: "در حال بررسی", statusClass: "bg-warning-subtle text-warning border-warning-subtle" },
  { type: "MRI", date: "12 دی 1402", doctor: "دکتر آدامز", status: "تکمیل شده", statusClass: "bg-success-subtle text-success border-success-subtle" },
  { type: "آندوسکوپی", date: "11 دی 1402", doctor: "دکتر وایت", status: "در حال انجام", statusClass: "bg-secondary-subtle text-secondary border-secondary-subtle" }
];

const pageSize = 4;
let currentPage = 1;

function renderTable() {
  const tbody = document.getElementById("report-table-body");
  tbody.innerHTML = "";

  const start = (currentPage - 1) * pageSize;
  const paginatedData = reportData.slice(start, start + pageSize);

  paginatedData.forEach(report => {
    tbody.innerHTML += `
        <tr>
          <td>${report.type}</td>
          <td>${report.date}</td>
          <td>${report.doctor}</td>
          <td><span class="badge ${report.statusClass}">${report.status}</span></td>
          <td>
            <div class="d-flex align-items-center gap-2">
              <button class="btn btn-sub-secondary rounded-circle size-8 btn-icon"><i class="ri-download-2-line"></i></button>
              <button class="btn btn-sub-danger rounded-circle size-8 btn-icon"><i class="ri-delete-bin-line"></i></button>
            </div>
          </td>
        </tr>
      `;
  });

  const info = document.getElementById("table-info");
  info.innerHTML = `نمایش <b>${start + 1}-${Math.min(start + pageSize, reportData.length)}</b> از <b>${reportData.length}</b> نتیجه`;

  renderPagination();
}

function renderPagination() {
  const totalPages = Math.ceil(reportData.length / pageSize);
  const pagination = document.getElementById("pagination");
  pagination.innerHTML = "";

  pagination.innerHTML += `
      <li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
        <a class="page-link" href="#!" onclick="goToPage(${currentPage - 1})">
          <i data-lucide="chevron-right" class="size-4"></i>  قبلی
        </a>
      </li>
    `;

  for (let i = 1; i <= totalPages; i++) {
    pagination.innerHTML += `
        <li class="page-item ${i === currentPage ? 'active' : ''}">
          <a class="page-link" href="#!" onclick="goToPage(${i})">${i}</a>
        </li>
      `;
  }

  pagination.innerHTML += `
      <li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">
        <a class="page-link" href="#!" onclick="goToPage(${currentPage + 1})">
          بعدی <i data-lucide="chevron-left" class="size-4"></i>
        </a>
      </li>
    `;

  // Move createIcons call here, after the HTML is added to the DOM
  createIcons({ icons });
}
window.goToPage = function (page) {
  const totalPages = Math.ceil(reportData.length / pageSize);
  if (page < 1 || page > totalPages) return;
  currentPage = page;
  renderTable();
};
renderTable();

const medicineData = [
  { date: "1403-01-01", time: "08:00 صبح", name: "آسپرین", dosage: "mg 81", frequency: "روزانه", start: "1403-01-01", end: "-", doctor: "دکتر اسمیت", reason: "سلامت قلب", notes: "همراه با غذا" },
  { date: "1403-01-15", time: "09:30 صبح", name: "متفورمین", dosage: "mg 500", frequency: "روزی دو بار", start: "1403-01-01", end: "-", doctor: "دکتر جانسون", reason: "دیابت", notes: "بعد از غذا" },
  { date: "1403-02-01", time: "06:00 عصر", name: "آتورواستاتین", dosage: "mg 20", frequency: "روزانه", start: "1403-02-01", end: "-", doctor: "دکتر براون", reason: "کلسترول بالا", notes: "قبل از خواب" },
  { date: "1403-03-01", time: "12:00 عصر", name: "آنتی‌هیستامین", dosage: "mg 10", frequency: "به میزان نیاز", start: "1403-03-05", end: "-", doctor: "دکتر لی", reason: "آلرژی", notes: "برای راش پوستی" },
  { date: "1403-07-05", time: "08:00 صبح", name: "استنشاقی آلبوترول", dosage: "-", frequency: "به میزان نیاز", start: "1403-07-05", end: "1404-07-09", doctor: "دکتر پاتل", reason: "آسم", notes: "هنگام بروز علائم" },
  { date: "1403-08-12", time: "10:00 صبح", name: "امپرازول", dosage: "mg 40", frequency: "روزانه", start: "1403-08-12", end: "-", doctor: "دکتر میلر", reason: "رفلکس معده", notes: "با معده خالی" },
  { date: "1403-09-01", time: "08:00 صبح", name: "لیزینوپریل", dosage: "mg 10", frequency: "روزانه", start: "1403-09-01", end: "-", doctor: "دکتر تیلور", reason: "فشار خون بالا", notes: "مصرف در صبح" }
];

const medicinePageSize = 5;
let medicinePage = 1;

function renderMedicineTable() {
  const tbody = document.getElementById("medicine-table-body");
  tbody.innerHTML = "";

  const start = (medicinePage - 1) * medicinePageSize;
  const paginated = medicineData.slice(start, start + medicinePageSize);

  paginated.forEach(row => {
    tbody.innerHTML += `
        <tr>
          <td>${row.date}</td>
          <td>${row.time}</td>
          <td>${row.name}</td>
          <td>${row.dosage}</td>
          <td>${row.frequency}</td>
          <td>${row.start}</td>
          <td>${row.end}</td>
          <td>${row.doctor}</td>
          <td>${row.reason}</td>
          <td>${row.notes}</td>
          <td>
            <div class="d-flex align-items-center gap-2">
              <button class="btn btn-sub-secondary size-8 rounded-circle btn-icon"><i class="ri-pencil-line"></i></button>
              <button class="btn btn-sub-danger size-8 rounded-circle btn-icon"><i class="ri-delete-bin-line"></i></button>
            </div>
          </td>
        </tr>
      `;
  });

  document.getElementById("medicineTableInfo").innerHTML = `نمایش <b>${start + 1}-${Math.min(start + medicinePageSize, medicineData.length)}</b> از <b>${medicineData.length}</b> نتیجه`;
  renderMedicinePagination();
}

function renderMedicinePagination() {
  const totalPages = Math.ceil(medicineData.length / medicinePageSize);
  const container = document.getElementById("medicinePagination");
  container.innerHTML = "";

  container.innerHTML += `
      <li class="page-item ${medicinePage === 1 ? 'disabled' : ''}">
        <a class="page-link" href="#!" onclick="goToMedicinePage(${medicinePage - 1})">
          <i data-lucide="chevron-right" class="size-4"></i> قبلی
        </a>
      </li>
    `;

  for (let i = 1; i <= totalPages; i++) {
    container.innerHTML += `
        <li class="page-item ${medicinePage === i ? 'active' : ''}">
          <a class="page-link" href="#!" onclick="goToMedicinePage(${i})">${i}</a>
        </li>
      `;
  }

  container.innerHTML += `
      <li class="page-item ${medicinePage === totalPages ? 'disabled' : ''}">
        <a class="page-link" href="#!" onclick="goToMedicinePage(${medicinePage + 1})">
          بعدی <i data-lucide="chevron-left" class="size-4"></i>
        </a>
      </li>
    `; 
    createIcons({ icons });
}

window.goToMedicinePage = function (page) {
  const totalPages = Math.ceil(medicineData.length / medicinePageSize);
  if (page < 1 || page > totalPages) return;
  medicinePage = page;
  renderMedicineTable();
};

renderMedicineTable();
const appointmentData = [
  {
    date: "18 خرداد 1403",
    title: "معاینه فیزیکی سالانه",
    time: "09:00 صبح",
    department: "پزشکی عمومی",
    purpose: "چکاپ روتین",
    doctor: "دکتر مایکل جانسون",
    status: "در حال بررسی"
  },
  {
    date: "19 خرداد 1403",
    title: "مشاوره پوست",
    time: "02:00 عصر",
    department: "پوست شناسی",
    purpose: "ارزیابی وضعیت پوست",
    doctor: "دکتر سارا ایونز",
    status: "در حال بررسی"
  },
  {
    date: "20 خرداد 1403",
    title: "جلسه فیزیوتراپی",
    time: "11:30 صبح",
    department: "فیزیوتراپی",
    purpose: "تمرینات توانبخشی",
    doctor: "دکتر جان ویلیامز",
    status: "تکمیل شده"
  },
  {
    date: "21 خرداد 1403",
    title: "معاینه چشم",
    time: "03:30 عصر",
    department: "چشم پزشکی",
    purpose: "معاینه بینایی",
    doctor: "دکتر امیلی مارتینز",
    status: "تکمیل شده"
  },
  {
    date: "22 خرداد 1403",
    title: "مشاوره روانپزشکی",
    time: "10:00 صبح",
    department: "روانپزشکی",
    purpose: "ارزیابی سلامت روان",
    doctor: "دکتر جیمز اندرسون",
    status: "تکمیل شده"
  },
  {
    date: "23 خرداد 1403",
    title: "بررسی گوش و حلق و بینی",
    time: "04:00 عصر",
    department: "حلق و گوش و بینی",
    purpose: "زنگ زدن گوش",
    doctor: "دکتر لوکاس مور",
    status: "در حال بررسی"
  },
  {
    date: "24 خرداد 1403",
    title: "ویزیت متخصص قلب و عروق",
    time: "01:00 عصر",
    department: "قلب و عروق",
    purpose: "درد قلب",
    doctor: "دکتر اولیویا کلارک",
    status: "تکمیل شده"
  },
  {
    date: "25 خرداد 1403",
    title: "جلسه متخصصین تغذیه",
    time: "10:30 صبح",
    department: "تغذیه",
    purpose: "برنامه غذایی",
    doctor: "دکتر آلا لوئیس",
    status: "تکمیل شده"
  },
  {
    date: "26 خرداد 1403",
    title: "بررسی ارتوپدی",
    time: "11:00 صبح",
    department: "ارتوپد",
    purpose: "درد زانو",
    doctor: "دکتر نوح دیویس",
    status: "در حال بررسی"
  }
];

const appointmentPageSize = 5;
let appointmentPage = 1;

function renderAppointmentTable() {
  const tbody = document.querySelector("#appointmentTable tbody");
  tbody.innerHTML = "";

  const start = (appointmentPage - 1) * appointmentPageSize;
  const paginated = appointmentData.slice(start, start + appointmentPageSize);

  paginated.forEach(row => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
        <td>${row.date}</td>
        <td>${row.title}</td>
        <td>${row.time}</td>
        <td>${row.department}</td>
        <td>${row.purpose}</td>
        <td>${row.doctor}</td>
        <td>
          <span class="badge ${row.status === "تکمیل شده"
        ? "bg-success-subtle text-success border border-success-subtle"
        : "bg-warning-subtle text-warning border border-warning-subtle"}">${row.status}</span>
        </td>
        <td>
          <div class="d-flex align-items-center gap-2">
            <button class="btn btn-light text-dark size-8 btn-icon"><i class="ri-eye-line"></i></button>
            <button class="btn btn-light text-dark size-8 btn-icon"><i class="ri-pencil-line"></i></button>
            <button class="btn btn-sub-danger size-8 btn-icon"><i class="ri-delete-bin-line"></i></button>
          </div>
        </td>
        `;
    tbody.appendChild(tr);
  });

  // Update result text
  const resultText = document.getElementById("resultText");
  resultText.innerHTML = `نمایش <b>${start + 1}-${Math.min(start + appointmentPageSize, appointmentData.length)}</b> از <b>${appointmentData.length}</b> نتیجه`;

  renderAppointmentPagination();
}

function renderAppointmentPagination() {
  const totalPages = Math.ceil(appointmentData.length / appointmentPageSize);
  const pagination = document.getElementById("paginationmandical");
  pagination.innerHTML = "";

  pagination.innerHTML += `
        <li class="page-item ${appointmentPage === 1 ? 'disabled' : ''}">
            <a class="page-link" href="#!" onclick="goToAppointmentPage(${appointmentPage - 1})">
                <i data-lucide="chevron-right" class="size-4"></i> قبلی
            </a>
        </li>
    `;

  for (let i = 1; i <= totalPages; i++) {
    pagination.innerHTML += `
            <li class="page-item ${appointmentPage === i ? "active" : ""}">
                <a class="page-link" href="#!" onclick="goToAppointmentPage(${i})">${i}</a>
            </li>
        `;
  }

  pagination.innerHTML += `
        <li class="page-item ${appointmentPage === totalPages ? 'disabled' : ''}">
            <a class="page-link" href="#!" onclick="goToAppointmentPage(${appointmentPage + 1})">
                بعدی <i data-lucide="chevron-left" class="size-4"></i>
            </a>
        </li>
    `;
  createIcons({ icons });
}

window.goToAppointmentPage = function (page) {
  const totalPages = Math.ceil(appointmentData.length / appointmentPageSize);
  if (page < 1 || page > totalPages) return;
  appointmentPage = page;
  renderAppointmentTable();
};

renderAppointmentTable();
