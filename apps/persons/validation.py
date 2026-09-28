"""Shared Iranian national-id and mobile-number validation helpers."""
from __future__ import annotations

from apps.core.utils import english_numbers


# Known three-digit birth-place prefixes. The checksum is authoritative;
# unknown non-zero prefixes remain acceptable and are returned as metadata so
# an incomplete local catalog can never reject a structurally valid national ID.
NATIONAL_CODE_PREFIXES = {
    "001": ("تهران", "تهران"), "002": ("تهران", "تهران"), "003": ("تهران", "تهران"),
    "004": ("تهران", "تهران"), "005": ("تهران", "تهران"), "006": ("تهران", "تهران"),
    "007": ("تهران", "تهران"), "008": ("تهران", "تهران"), "009": ("تهران", "تهران"),
    "020": ("تهران", "کرج"), "021": ("تهران", "کرج"), "022": ("تهران", "کرج"),
    "030": ("آذربایجان شرقی", "تبریز"), "031": ("آذربایجان شرقی", "تبریز"),
    "032": ("آذربایجان شرقی", "مراغه"), "033": ("آذربایجان شرقی", "مرند"),
    "040": ("آذربایجان غربی", "ارومیه"), "041": ("آذربایجان غربی", "خوی"),
    "045": ("اردبیل", "اردبیل"), "050": ("اصفهان", "اصفهان"),
    "051": ("اصفهان", "کاشان"), "052": ("اصفهان", "نجف‌آباد"),
    "060": ("البرز", "کرج"), "061": ("البرز", "کرج"),
    "065": ("ایلام", "ایلام"), "070": ("بوشهر", "بوشهر"),
    "075": ("تهران", "شهریار"), "080": ("چهارمحال و بختیاری", "شهرکرد"),
    "085": ("خراسان جنوبی", "بیرجند"), "090": ("خراسان رضوی", "مشهد"),
    "091": ("خراسان رضوی", "مشهد"), "092": ("خراسان رضوی", "نیشابور"),
    "095": ("خراسان شمالی", "بجنورد"), "100": ("خوزستان", "اهواز"),
    "105": ("خراسان رضوی", "نیشابور"), "110": ("اصفهان", "فلاورجان"),
    "115": ("اصفهان", "فریدن"), "120": ("اصفهان", "سمیرم"),
    "125": ("اصفهان", "کاشان"), "127": ("اصفهان", "اصفهان"),
    "136": ("آذربایجان شرقی", "تبریز"), "145": ("اردبیل", "اردبیل"),
    "150": ("آذربایجان شرقی", "اهر"), "154": ("آذربایجان شرقی", "مراغه"),
    "160": ("آذربایجان شرقی", "هشترود"), "170": ("فارس", "شیراز"),
    "175": ("فارس", "مرودشت"), "180": ("فارس", "کازرون"),
    "185": ("فارس", "لار"), "190": ("فارس", "جهرم"),
    "200": ("قم", "قم"), "205": ("قزوین", "قزوین"),
    "208": ("قزوین", "تاکستان"), "210": ("کردستان", "سنندج"),
    "215": ("مازندران", "قائمشهر"), "220": ("مازندران", "نوشهر"),
    "225": ("مازندران", "سوادکوه"), "228": ("فارس", "شیراز"),
    "229": ("فارس", "شیراز"), "230": ("فارس", "شیراز"),
    "235": ("کرمانشاه", "اسلام‌آباد غرب"), "240": ("کهگیلویه و بویراحمد", "یاسوج"),
    "245": ("گلستان", "گرگان"), "250": ("گیلان", "رشت"),
    "255": ("گیلان", "لاهیجان"), "260": ("لرستان", "خرم‌آباد"),
    "265": ("مازندران", "ساری"), "270": ("مازندران", "بابل"),
    "275": ("مرکزی", "اراک"), "280": ("هرمزگان", "بندرعباس"),
    "285": ("همدان", "همدان"), "290": ("یزد", "یزد"),
    # Values used by legacy fixtures and imported records in this project.
    "800": ("تهران", "تهران"), "812": ("تهران", "تهران"), "910": ("تهران", "تهران"),
}


def normalize_national_code(value: object) -> str:
    return english_numbers(str(value or "")).strip()


def national_code_location(value: object) -> tuple[str, str] | None:
    code = normalize_national_code(value)
    if len(code) < 3 or not code[:3].isdigit() or code[:3] == "000":
        return None
    # Every non-zero three-digit prefix is structurally a birth-place prefix.
    # Use the detailed local catalog when available; otherwise keep the code
    # valid and expose the prefix for a later official city-directory lookup.
    return NATIONAL_CODE_PREFIXES.get(code[:3], ("استان/شهر نیازمند تطبیق رسمی", code[:3]))


def is_valid_national_code(value: object, *, require_location: bool = False) -> bool:
    code = normalize_national_code(value)
    if len(code) != 10 or not code.isdigit() or len(set(code)) == 1:
        return False
    total = sum(int(code[index]) * (10 - index) for index in range(9))
    remainder = total % 11
    check = int(code[9])
    if check != (remainder if remainder < 2 else 11 - remainder):
        return False
    return not require_location or national_code_location(code) is not None


def national_code_error(value: object, *, require_location: bool = False) -> str | None:
    code = normalize_national_code(value)
    if len(code) != 10 or not code.isdigit():
        return "کد ملی باید دقیقاً ۱۰ رقم عددی باشد."
    if not is_valid_national_code(code):
        return "کد ملی معتبر نیست؛ رقم کنترل با فرمول استاندارد ایران مطابقت ندارد."
    if require_location and national_code_location(code) is None:
        return "پیش‌شماره کد ملی با استان و شهر صادرکننده شناخته‌شده مطابقت ندارد."
    return None


def is_valid_iranian_mobile(value: object) -> bool:
    phone = english_numbers(str(value or "")).strip()
    return len(phone) == 11 and phone.isdigit() and phone.startswith("09")
