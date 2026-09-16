const quill = new Quill("#editor", {
  theme: "snow",
});

import EditorJS from '@editorjs/editorjs';
import Header from '@editorjs/header';
import List from '@editorjs/list';
import Image from '@editorjs/image';
import AttachesTool from '@editorjs/attaches';
import Marker from '@editorjs/marker';

// Provided JSON data
const defaultData = {
  time: 1742315418218,
  blocks: [
    {
      id: "mhTl6ghSkV",
      type: "paragraph",
      data: {
        text: "سلام. با ویرایشگر جدید آشنا شوید. در این تصویر می‌توانید آن را در عمل ببینید. سپس، یک نسخه آزمایشی را امتحان کنید 🤓",
      },
    },
    {
      id: "l98dyx3yjb",
      type: "header",
      data: {
        text: "ویژگی‌های کلیدی",
        level: 3,
      },
    },
    {
      id: "os_YI4eub4",
      type: "list",
      data: {
        style: "unordered",
        items: [
          "این یک ویرایشگر به سبک بلوک است",
          "خروجی داده‌های تمیز را در قالب JSON برمی‌گرداند.",
          "طراحی شده برای قابلیت توسعه و اتصال به <a href='https://editorjs.io/creating-a-block-tool'>ساده API</a>",
        ],
      },
    },
    {
      id: "1yKeXKxN7-",
      type: "header",
      data: {
        text: "منظور از «ویرایشگر به سبک بلوک» چیست؟",
        level: 3,
      },
    },
    {
      id: "TcUNySG15P",
      type: "paragraph",
      data: {
        text: "فضای کاری در ویرایشگرهای کلاسیک از یک عنصر قابل ویرایش محتوا تشکیل شده است که برای ایجاد نشانه‌گذاری‌های مختلف HTML استفاده می‌شود. فضای کاری Editor.js از بلوک‌های جداگانه‌ای تشکیل شده است: پاراگراف‌ها، عنوان‌ها، تصاویر، لیست‌ها، نقل قول‌ها و غیره. هر یک از آنها یک عنصر مستقل قابل ویرایش محتوا (یا ساختار پیچیده‌تر) <sup data-tune='footnotes'>1</sup> است که توسط افزونه ارائه شده و توسط هسته ویرایشگر متحد شده است.",
      },
      tunes: {
        footnotes: [
          "این ویرایشگر نسبت به سایر ویرایشگرهای WYSIWYG پایدارتر عمل می‌کند. در عین حال، مانند ویرایشگرهای کلاسیک، رفتار ناوبری فلشی روان و شناخته‌شده‌ای دارد.",
        ],
      },
    },
    {
      id: "M3UXyblhAo",
      type: "header",
      data: {
        text: "منظور از خروجی داده تمیز چیست؟",
        level: 3,
      },
    },
    {
      id: "KOcIofZ3Z1",
      type: "paragraph",
      data: {
        text: "ده‌ها بلوک آماده برای استفاده و یک API ساده <sup data-tune='footnotes'>2</sup> برای ایجاد هر بلوکی که نیاز دارید وجود دارد. به عنوان مثال، می‌توانید بلوک‌هایی را برای توییت‌ها، پست‌های اینستاگرام، نظرسنجی‌ها و رای‌گیری‌ها، دکمه‌های فراخوان عمل (کال تو اکشن) و حتی بازی‌ها پیاده‌سازی کنید.",
      },
      tunes: {
        footnotes: [
          "فقط نگاهی به راهنمای ابزار ایجاد بلوک ما بیندازید. شگفت‌زده خواهید شد.",
        ],
      },
    },
    {
      id: "ksCokKAhQw",
      type: "paragraph",
      data: {
        text: "ویرایشگرهای کلاسیک WYSIWYG، نشانه‌گذاری خام HTML را با داده‌های محتوا و ظاهر محتوا تولید می‌کنند. در مقابل, <mark class='cdx-marker'>Editor.js outputs JSON object</mark> با داده‌های هر بلوک خروجی می‌دهد.",
      },
    },
    {
      id: "XKNT99-qqS",
      type: "attaches",
      data: {
        file: {
          url: "https://drive.google.com/user/catalog/my-file.pdf",
          size: 12902,
          name: "file.pdf",
          extension: "pdf",
        },
        title: "فایل من",
      },
    },
    {
      id: "7RosVX2kcH",
      type: "paragraph",
      data: {
        text: "دیتاهای داده شده را می‌توان به دلخواه استفاده کرد: رندر با HTML برای کلاینت‌های وب، رندر بومی برای برنامه‌های تلفن همراه، ایجاد نشانه‌گذاری برای مقالات فوری فیس‌بوک یا Google AMP، تولید نسخه صوتی و غیره.",
      },
    },
    {
      id: "eq06PsNsab",
      type: "paragraph",
      data: {
        text: "داده‌های تمیز برای پاکسازی، اعتبارسنجی و پردازش در بک‌اند مفید هستند.",
      },
    },
  ],
};

// Initialize the editor
const editor = new EditorJS({
  holder: 'editorjs', // ID of the container element
  tools: {
    header: {
      class: Header,
      inlineToolbar: true,
    },
    list: {
      class: List,
      inlineToolbar: true,
    },
    image: {
      class: Image,
      config: {
        endpoints: {
          byFile: 'https://example.com/upload-image', // Your image upload endpoint
        },
      },
    },
    attaches: {
      class: AttachesTool,
    },
    marker: {
      class: Marker,
    },
  },
  data: defaultData, // Pass the default content here
});

// Save button logic
document.getElementById('save-button').addEventListener('click', () => {
  editor.save().then((output) => {
    console.log('Saved data: ', output);
  }).catch((error) => {
    console.log('Saving failed: ', error);
  });
});