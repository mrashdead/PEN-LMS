# راهنمای Docker و استقرار پروژه پن

## ۱. چه چیزهایی آماده شده است؟

این استقرار برای یک سرور یا سیستم شخصی است، نه کلاستر Swarm/Kubernetes. تمام سرویس‌ها با `compose.yaml` مدیریت می‌شوند:

| بخش | اجرا و نگه‌داری |
| --- | --- |
| Linux | کاربران فضای کانتینر Debian Bookworm؛ مستقل از توزیع میزبان |
| Python | شاخه 3.11 در ایمیج رسمی؛ محیط مجازی جدید در `/opt/venv` |
| وابستگی‌های Python | `requirements.txt` و Gunicorn در `requirements-docker.txt` |
| Node و npm | Node 22 و npm همراه آن در مرحله ساخت فرانت‌اند |
| فرانت‌اند | `npm ci`، بازسازی کتابخانه‌های قالب و bundle اختصاصی Pen با Vite |
| Django | Gunicorn، کاربر غیر root با UID/GID برابر 10001 |
| PostgreSQL | شاخه 18؛ داده روی volume، بدون پورت عمومی |
| Redis | شاخه 8؛ AOF، broker، result backend و cache مشترک |
| کارهای پس‌زمینه | یک Celery worker و دقیقاً یک Celery beat |
| وب و TLS | Caddy، فایل‌های static و HTTPS خودکار برای دامنه واقعی |
| راه‌اندازی | سرویس یک‌باره `init` برای check، migrate و collectstatic |
| اطلاعات پایدار | volume جدا برای دیتابیس، media، Redis، beat و گواهی‌ها |

میزبان بررسی‌شده Ubuntu 26.04.1 و Python فعال محیط `venv` برابر 3.11.16 است؛ `venv310` قدیمی هم وجود دارد. محیط مجازی میزبان کپی نمی‌شود چون قابل انتقال بین سیستم‌ها نیست. ایمیج Python شاخه 3.11 انتخاب شده تا با محیط فعال سازگار باشد. سیستم‌عامل میزبان و kernel در Docker کپی نمی‌شوند؛ برای بازتولید دقیق کل Ubuntu به ماشین مجازی نیاز دارید، نه Docker. روی Windows/macOS از Docker Desktop با Linux containers استفاده کنید.

Node/npm در مرحله build وجود دارند و عمداً در runtime وب نصب نیستند؛ صفحات واقعی پروژه قالب Django هستند، نه یک SPA با سرور npm جدا. build دموهای قالب جایگزین قالب‌های Django نمی‌شود. برای اجرای دستی ابزارهای Node می‌توانید target فرانت‌اند را بسازید:

```bash
docker build --target frontend -t pen-frontend-tools .
docker run --rm --entrypoint node pen-frontend-tools --version
docker run --rm --entrypoint npm pen-frontend-tools --version
```

تگ‌های ایمیج شاخه‌ای هستند و patch جدید می‌گیرند؛ پس از یک build موفق، نسخه انتشار را با digest ثابت یا ایمیج ساخته‌شده نگه دارید. `reportlab` و ابزارهای RTL در requirements فعلی نیز بازه نسخه دارند؛ این فایل به‌تنهایی قفل کامل تمام نسخه‌ها نیست. برای بازتولید دقیق انتشار، خود ایمیج را انتقال دهید و خروجی `pip freeze` را در آرشیو انتشار ذخیره کنید.

## ۲. پیش‌نیاز سیستم مقصد

- Docker Engine/Desktop و Docker Compose v2 با پشتیبانی `service_completed_successfully`؛ نسخه 2.24 یا جدیدتر توصیه می‌شود.
- دسترسی به Docker daemon، اینترنت برای اولین build و فضای دیسک برای تصاویر و داده‌ها.
- روی Linux، Bash و Python 3 فقط برای اسکریپت‌های میزبان؛ اجرای مستقیم Compose به Python میزبان نیاز ندارد.
- برای شروع، ۲ هسته CPU و ۴ گیگابایت RAM پیشنهاد عملی است؛ نیاز واقعی به بار و حجم فایل‌ها بستگی دارد.
- دسترسی به کد کامل `frontend/Admin` و مجوز قانونی قالب تجاری آن.

دسترسی Docker عملاً دسترسی مدیریتی میزبان است. در صورت خطای permission از راهکار مورد تأیید مدیر سیستم مثل `sudo docker ...` یا Docker rootless استفاده کنید؛ افزودن کاربر به گروه docker را بدون درک این دسترسی انجام ندهید. روی میزبان SELinux ممکن است برای bind mount فایل Caddyfile برچسب مناسب لازم باشد.

## ۳. اجرای محلی، بدون دست‌زدن به دیتابیس فعلی

Docker از `.env.docker` جدا از `.env` فعلی استفاده می‌کند. داده‌های PostgreSQL موجود میزبان خودکار منتقل نمی‌شوند و سرویس‌های میزبان متوقف نمی‌شوند.

```bash
test -f .env.docker || cp .env.docker.example .env.docker
chmod 600 .env.docker
python3 -c 'import secrets; print(secrets.token_urlsafe(64))'
python3 -c 'import secrets; print(secrets.token_urlsafe(32))'
```

دو خروجی را به‌ترتیب به‌جای `SECRET_KEY` و `DB_PASSWORD` بگذارید. این کلیدها را در Git یا پیام عمومی نگذارید. نام پروژه را پیش از نخستین اجرا تعیین کنید؛ تغییر `COMPOSE_PROJECT_NAME` volumeهای دیگری انتخاب می‌کند.

در آماده‌سازی فعلی، `.env.docker` محلی با secretهای تصادفی و دسترسی فایل 600 ساخته شده است. اگر این فایل از قبل وجود دارد آن را با نمونه جایگزین نکنید؛ مخصوصاً تغییر رمز فایل بدون تغییر role دیتابیس مقداردهی‌شده اتصال را خراب می‌کند. نمونه محیط برای سیستم مقصد تازه است.

```bash
docker compose --env-file .env.docker config --quiet
bash scripts/docker-deploy.sh
docker compose --env-file .env.docker exec web python manage.py createsuperuser
docker compose --env-file .env.docker exec web python manage.py seed_roles
```

سپس `http://localhost:8080/dashboard/login/` را باز کنید. حساب مدیر ساخته نمی‌شود و رمز پیش‌فرض وجود ندارد. سایر seedها، مثل schemaها و workflowها، باید بعد از بررسی نیاز کسب‌وکار دستی اجرا شوند؛ داده نمایشی خودکار وارد نمی‌شود.

اگر Python/Bash میزبان ندارید، بعد از تنظیم secretها از این دستورات استفاده کنید:

```bash
docker compose --env-file .env.docker build web
docker compose --env-file .env.docker up -d
docker compose --env-file .env.docker ps -a
docker compose --env-file .env.docker logs --tail=100 init web worker beat proxy
```

اجرای محلی با `DEBUG=False` است ولی فقط برای HTTP روی loopback، secure cookies و HSTS در مثال خاموش‌اند. این تنظیمات برای اینترنت مناسب نیستند. برای خطای healthcheck اولین ALLOWED_HOST باید دامنه مشخص و معتبر باشد، نه wildcard. تمام فرمان‌ها باید `--env-file .env.docker` داشته باشند؛ فرمان بدون آن ممکن است تنظیمات `.env` میزبان را برای interpolation بخواند.

برای فایل محیط دیگری، مقدار داخل همان فایل و متغیر پوسته را هماهنگ کنید:

```bash
PEN_ENV_FILE=.env.server bash scripts/docker-deploy.sh
```

## ۴. تنظیم سرور واقعی و HTTPS

در `.env.docker` مقادیر زیر را با دامنه خودتان تنظیم کنید:

```dotenv
SITE_ADDRESS=pen.example.com
BIND_ADDRESS=0.0.0.0
HTTP_PORT=80
HTTPS_PORT=443
ALLOWED_HOSTS=pen.example.com
CSRF_TRUSTED_ORIGINS=https://pen.example.com
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=3600
```

رکورد DNS نوع A/AAAA را به سرور مقصد متصل کنید و ورودی TCP پورت‌های 80 و 443 را باز کنید. رکورد AAAA اشتباه را باقی نگذارید. Caddy برای دامنه قابل دسترس گواهی می‌گیرد؛ گواهی و اطلاعات تمدید در volume باقی می‌مانند. پورت‌های دیتابیس، Redis و Gunicorn عمداً publish نشده‌اند. در firewall کل دسترسی ورودی را فقط به خدمات ضروری محدود کنید؛ تنظیمات firewall میزبان ممکن است تحت تأثیر قوانین شبکه Docker باشد.

بعد از اطمینان از کارکرد HTTPS، HSTS را به `31536000` افزایش دهید. تنظیم فعلی Django شامل subdomain و preload است؛ فقط وقتی همه زیردامنه‌های مربوط HTTPS دارند این مدت بلند را اعمال کنید. header پروکسی فقط در شبکه خصوصی Compose مورد اعتماد است؛ Gunicorn را مستقیم به اینترنت publish نکنید. اگر CDN یا load balancer دیگری جلوی Caddy قرار دارد، trust آن را جداگانه و محدود به IPهای شناخته‌شده پیکربندی کنید.

برای ایمیل واقعی، `EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend` و اطلاعات SMTP را وارد کنید. SMS نیز به endpoint و token سرویس‌دهنده شما نیاز دارد. نمونه فعلی ایمیل را فقط در log می‌نویسد. CORS را خالی بگذارید مگر واقعاً frontend روی origin جدا اجرا شود.

## ۵. آزمون و مشاهده وضعیت

```bash
docker compose --env-file .env.docker ps -a
docker compose --env-file .env.docker logs -f --tail=100 web worker beat proxy
docker compose --env-file .env.docker exec web python manage.py check --deploy
docker compose --env-file .env.docker exec web python manage.py makemigrations --check --dry-run
curl --fail http://localhost:8080/healthz/
curl --fail http://localhost:8080/readyz/
```

روی سرور، curl را با URL دارای HTTPS اجرا کنید. `init` باید با کد 0 خارج شده باشد؛ خارج‌شدن آن طبیعی است. health وب دیتابیس را بررسی می‌کند. وضعیت healthy به‌تنهایی عملکرد تمام jobهای worker/beat یا سرویس ایمیل را تضمین نمی‌کند؛ log، dead-letter و heartbeat باید مانیتور شوند.

برای gate کامل، یک محیط آزمایش با دیتابیس/volume مجزا تهیه کنید و `scripts/test_ci.sh` را اجرا کنید؛ هرگز test suite را به production متصل نکنید. ابزارهای آزمون در requirements فعلی و بنابراین ایمیج هم موجودند، اما اسکریپت‌های CI در runtime کپی نشده‌اند. تست پس از استقرار آماده است:

```bash
SMOKE_BASE_URL=https://pen.example.com \
SMOKE_USERNAME=deployment-smoke \
SMOKE_PASSWORD='secret-from-your-secret-store' \
bash scripts/smoke_deploy.sh
```

حساب smoke باید از قبل با حداقل دسترسی لازم ایجاد شود. secret را در history یا log مشترک قرار ندهید. logهای هر سرویس با چرخش محدود نگه‌داری می‌شوند؛ log collector و alertهای بیرونی باید توسط شما تنظیم شوند.

## ۶. فایل‌های media و امنیت

کل media در volume مشترک وب و worker باقی می‌ماند. فایل‌های خصوصی فرم‌ها تنها از endpoint مجوزدار Django دانلود می‌شوند. Caddy هیچ `/media/` را عمومی سرو نمی‌کند؛ این تصمیم جلوی افشای فایل‌های فرم، مرخصی و آموزش را می‌گیرد. فیلدهای قدیمی که URL مستقیم `/media/...` می‌دهند، مثل عکس اشخاص، بدون endpoint مجوزدار نمایش/دانلود نمی‌شوند. برای عمومی‌کردن عکس‌ها باید مجوز و سیاست حریم خصوصی را جداگانه تأیید کنید؛ کل media را با یک alias عمومی باز نکنید.

حد بدنه درخواست Caddy برابر 30MB است؛ آن را با محدودیت‌های upload برنامه هماهنگ کنید. دیتابیس با کاربر bootstrap ایمیج PostgreSQL ایجاد می‌شود که superuser است؛ برای محیط حساس، پس از بررسی migrationها یک role محدود برای runtime و role جدا برای migration/backup در نظر بگیرید. این ترکیب خودکار role محدود ایجاد نمی‌کند.

## ۷. به‌روزرسانی

ابتدا بکاپ بگیرید، کد و migrationها را بازبینی کنید و همان نسخه ایمیج را در staging آزمایش کنید:

```bash
bash scripts/docker-backup.sh
bash scripts/docker-deploy.sh
```

اسکریپت استقرار قبل از توقف برنامه build را انجام می‌دهد و drift migration را بررسی می‌کند؛ سپس وب و jobها را متوقف کرده و migrate/collectstatic را پیش از شروع نسخه جدید اجرا می‌کند. این روش downtime کوتاه دارد و zero-downtime نیست. اگر migration شکست بخورد، worker و وب جدید نباید شروع شوند؛ log سرویس init را بررسی کنید. rollback دیتابیس صرفاً با تعویض image تضمین نمی‌شود؛ قبل از مهاجرت ناسازگار برنامه بازیابی داشته باشید.

تغییر رمز `DB_PASSWORD` در فایل محیط، رمز یک PostgreSQL از قبل مقداردهی‌شده را عوض نمی‌کند؛ role دیتابیس نیز باید با روش امن به‌روزرسانی شود. تغییر major PostgreSQL روی volume موجود ممنوع است؛ از dump/restore یا pg_upgrade برنامه‌ریزی‌شده استفاده کنید. مسیر volume این Compose مخصوص layout نسخه 18 است.

`docker compose down` داده‌های named volume را نگه می‌دارد. `down -v` و prune کردن volumeها می‌تواند اطلاعات را غیرقابل بازیابی حذف کند؛ از آن برای توقف معمول استفاده نکنید. beat را scale نکنید و jobهایش را هم‌زمان در cron اجرا نکنید.

## ۸. بکاپ و بازیابی

```bash
bash scripts/docker-backup.sh
bash scripts/docker-restore.sh backups/pen-TIMESTAMP
```

بکاپ شامل PostgreSQL با فرمت custom، کل media، checksum و فهرست ایمیج‌ها است. برای هماهنگی DB/media، سرویس‌های نویسنده همین Compose موقتاً متوقف می‌شوند و بعد از موفقیت یا خطا دوباره شروع می‌شوند. اگر نویسنده بیرونی به DB/media متصل است، خودتان آن را هم متوقف کنید. بکاپ روی همین دیسک کافی نیست؛ روزانه رمزگذاری و به مقصد بیرونی منتقل کنید. اسکریپت secretهای محیط را آرشیو نمی‌کند؛ `.env.docker`، نسخه کد/ایمیج و کلیدهای لازم را جداگانه در secret store امن نگه دارید. گواهی Caddy پس از خرابی کامل می‌تواند دوباره صادر شود؛ در صورت نیاز از volume آن هم با روش امن بکاپ بگیرید.

بازیابی destructive است و تأیید تایپی `RESTORE` می‌خواهد. پس از تأیید، دیتابیس حذف و از نو ایجاد می‌شود، تمام media جایگزین می‌شود و صف‌های broker، resultها و cache در Redis اختصاصی این Compose پاک می‌شوند تا job قدیمی روی داده بازیابی‌شده اجرا نشود. اتصال‌های بیرونی دیتابیس نیز با drop اجباری قطع می‌شوند. در شکست restore سرویس‌های برنامه متوقف باقی می‌مانند تا اطلاعات نیمه‌بازیابی‌شده منتشر نشود. فقط بکاپ مورد اعتماد خودتان را باز کنید و ابتدا در محیط ایزوله تمرین کنید. Redis و beat schedule در این بکاپ نیستند؛ jobهای حذف‌شده و اعلان‌های نیازمند تکرار را بر اساس داده‌های outbox بازبینی کنید.

## ۹. انتقال پروژه به سیستم دیگر

راه آنلاین: کد را انتقال دهید، `.env.docker` مقصد را تنظیم کنید، build کنید و در صورت نیاز DB/media را بازیابی کنید. مراقب باشید کتابخانه‌های `src/assets/libs` در Git نیستند و مرحله build باید آن‌ها را از npm دوباره بسازد؛ `node_modules` یا venv را کپی نکنید.

راه انتقال ایمیج آماده روی معماری CPU یکسان:

```bash
docker compose --env-file .env.docker pull db redis proxy
docker image save pen-app:local postgres:18-bookworm redis:8-bookworm caddy:2-alpine | gzip > pen-images.tar.gz
```

روی مقصد:

```bash
gzip -dc pen-images.tar.gz | docker image load
docker compose --env-file .env.docker up -d --pull never --no-build
```

نام ایمیج‌ها باید با مقادیر واقعی فایل محیط مطابقت داشته باشد. `compose.yaml`، پوشه docker، فایل محیط محرمانه و آرشیو داده‌ها هم جدا لازم‌اند؛ image به‌تنهایی شامل داده نیست. اگر مقصد ARM64 و مبدا AMD64 است، روی مقصد build کنید یا با Buildx ایمیج multi-platform بسازید؛ این پروژه هیچ `platform` اجباری تنظیم نکرده است.

## ۱۰. Git و موارد نیازمند اقدام شما

`.dockerignore` فقط کد و asset موردنیاز build را می‌فرستد؛ `.env`، دیتابیس، media، cache، venv، node_modules و artifact محلی وارد image نمی‌شوند. `.gitignore` secretها، بکاپ‌ها و فایل‌های محلی Docker را کنار می‌گذارد ولی Dockerfile، Compose، نمونه محیط، راهنما و اسکریپت‌های جدید قابل commit هستند. قانون عمومی قدیمیِ ignore کردن Markdown و shellهای دیگر عمداً تغییر نکرده است. ignore کردن، فایل قبلاً tracked را از تاریخچه Git حذف نمی‌کند؛ اگر secret قبلاً commit شده، آن را rotate کنید.

موارد نیازمند دسترسی شما: نصب/دسترسی Docker روی مقصد، انتخاب دامنه و DNS/firewall، secretهای واقعی، ورود و ساخت مدیر، SMTP/SMS، انتقال امن داده فعلی، مقصد بکاپ و زمان‌بندی/مانیتورینگ بیرونی. هیچ commit/push، تغییر DNS، دستکاری دیتابیس فعلی یا استقرار روی سرور خارجی به‌صورت خودکار انجام نمی‌شود.

## ۱۱. اعتبارسنجی انجام‌شده در این سیستم

در ۳ اکتبر ۲۰۲۶ ایمیج `pen-app:local` با موفقیت ساخته شد؛ Python واقعی ایمیج 3.11.17 است و libmagic نیز بررسی شد. فایل lock فرانت‌اند که با package.json ناسازگار بود همگام شد و `npm ci` در build تمیز اجرا شد؛ هیچ ارجاع static ثابتِ مفقودی در قالب‌های Django یافت نشد.

تمام migrationها روی PostgreSQL جدید کانتینری اعمال شدند و `makemigrations --check --dry-run` تغییر معوق نشان نداد. ۸ تست تنظیمات استقرار و endpointهای عملیاتی روی دیتابیس تست جداگانه گذشتند. liveness، readiness، صفحه ورود و bundle فرانت‌اند HTTP 200 و مسیر media خصوصی HTTP 404 دادند. worker به ping پاسخ داد و beat با schedule پایدار شروع شد.

بکاپ `backups/docker-validation` ساخته شد، checksum و فهرست dump بررسی شدند و در پروژه جداگانه `pen-restore-validation` بازیابی شد؛ readiness و صفحه ورود محیط بازیابی‌شده نیز سالم بودند. این آزمون از دیتابیس جدید و media خالی استفاده کرد، نه از اطلاعات فعلی میزبان؛ بازیابی داده واقعی و دانلود نمونه پیوست خصوصی همچنان باید با دسترسی مالک داده تمرین شود. صدور گواهی واقعی دامنه و smoke احرازهویت‌شده به دامنه و حساب مجاز شما نیاز دارد.
