import AirDatepicker from 'air-datepicker';
import 'air-datepicker/air-datepicker.css';
import isWithinInterval from 'date-fns/isWithinInterval';
import isEqual from 'date-fns/isEqual';

// Animation datepicker
import { createPopper } from '../../libs/@popperjs/core/esm/index.js';


// Import all locales
import localeAr from 'air-datepicker/locale/ar';
import localeBg from 'air-datepicker/locale/bg';
import localeCa from 'air-datepicker/locale/ca';
import localeCs from 'air-datepicker/locale/cs';
import localeDa from 'air-datepicker/locale/da';
import localeDe from 'air-datepicker/locale/de';
import localeEl from 'air-datepicker/locale/el';
import localeEn from 'air-datepicker/locale/en';
import localeEs from 'air-datepicker/locale/es';
import localeEu from 'air-datepicker/locale/eu';
import localeFi from 'air-datepicker/locale/fi';
import localeFr from 'air-datepicker/locale/fr';
import localeHr from 'air-datepicker/locale/hr';
import localeHu from 'air-datepicker/locale/hu';
import localeId from 'air-datepicker/locale/id';
import localeIt from 'air-datepicker/locale/it';
import localeJa from 'air-datepicker/locale/ja';
import localeKo from 'air-datepicker/locale/ko';
import localeNb from 'air-datepicker/locale/nb';
import localeNl from 'air-datepicker/locale/nl';
import localePl from 'air-datepicker/locale/pl';
import localePt from 'air-datepicker/locale/pt';
import localeRo from 'air-datepicker/locale/ro';
import localeRu from 'air-datepicker/locale/ru';
import localeSk from 'air-datepicker/locale/sk';
import localeSv from 'air-datepicker/locale/sv';
import localeTh from 'air-datepicker/locale/th';
import localeTr from 'air-datepicker/locale/tr';
import localeUk from 'air-datepicker/locale/uk';
import localeZh from 'air-datepicker/locale/zh';

document.addEventListener('DOMContentLoaded', function () {
    const datepickerElements = document.querySelectorAll('[data-datepicker]');

    const localeMap = {
        ar: localeAr, //Arabic
        bg: localeBg, //Bulgarian
        ca: localeCa, //Catalan
        cs: localeCs, //Czech
        da: localeDa, //Danish
        de: localeDe, //German
        el: localeEl, //Greek
        en: localeEn, // Use our explicit English locale
        es: localeEs, //Spanish
        eu: localeEu, //Basque
        fi: localeFi, //Finnish
        fr: localeFr, //French
        hr: localeHr, //Croatian
        hu: localeHu, //Hungarian
        id: localeId, //Indonesian
        it: localeIt, //Italian
        ja: localeJa, //Japanese
        ko: localeKo, //Korean
        nb: localeNb, //Norwegian Bokmål
        nl: localeNl, //Dutch
        pl: localePl, //Polish
        pt: localePt, //Portuguese
        ro: localeRo, //Romanian
        ru: localeRu, //Russian
        sk: localeSk, //Slovak
        sv: localeSv, //Swedish
        th: localeTh, //Thai
        tr: localeTr, //Turkish
        uk: localeUk, //Ukrainian
        zh: localeZh //Chinese
    };

    (datepickerElements || []).forEach(function (element) {
        const languageCode = element.getAttribute('data-language') || 'en';

        // Create base options
        const options = {
            dateFormat: element.getAttribute('data-date-format') || 'yyyy-MM-dd',
            locale: localeMap[languageCode] || localeEn, // Fallback to English
            autoClose: element.getAttribute('data-auto-close') === 'true',
            view: element.getAttribute('data-view') || 'days',
            minView: element.getAttribute('data-min-view') || 'days',
            isMobile: element.getAttribute('data-mobile') === 'true',
            inline: element.getAttribute('data-inline') === 'true',
            onSelect: function (formattedDate, date, inst) {},
        };

        // Timepicker configuration
        if (element.getAttribute('data-timepicker') === 'true') {
            options.timepicker = true;
            options.timeFormat = element.getAttribute('data-time-format') || 'hh:mm AA';
        }

        if (element.getAttribute('data-multiple-dates') === 'true')
            options.multipleDates = true;

        if (element.getAttribute('data-min-date'))
            options.minDate = new Date(element.getAttribute('data-min-date'));

        if (element.getAttribute('data-max-date'))
            options.maxDate = new Date(element.getAttribute('data-max-date'));

        if (element.getAttribute('data-selected-dates'))
            options.selectedDates = element.getAttribute('data-selected-dates').split(',').map(date => new Date(date.trim()));

        if (element.getAttribute('data-range') === 'true')
            options.range = true;

        if (element.getAttribute('data-disabled-date')) {
            const disabledDate = new Date(element.getAttribute('data-disabled-date').trim());
            const isDisabledDateIsInRange = ({ date, datepicker }) => {
                const selectedDate = datepicker.selectedDates[0];
                if (selectedDate && datepicker.selectedDates.length === 1) {
                    const sortedDates = [selectedDate, date].sort((a, b) => {
                        if (a.getTime() > b.getTime()) {
                            return 1;
                        }
                        return -1;
                    });

                    return (isWithinInterval(disabledDate, {
                        start: sortedDates[0],
                        end: sortedDates[1]
                    }));
                }
                return false;
            };

            options.onBeforeSelect = ({ date, datepicker }) => {
                return !isDisabledDateIsInRange({ date, datepicker });
            };

            options.onFocus = ({ date, datepicker }) => {
                if (isDisabledDateIsInRange({ date, datepicker }) || isEqual(date, disabledDate))
                    datepicker.$datepicker.classList.add('-disabled-range-');
                else
                    datepicker.$datepicker.classList.remove('-disabled-range-');
            };

            options.onRenderCell = ({ date }) => {
                if (date.toLocaleDateString() === disabledDate.toLocaleDateString()) {
                    return {
                        disabled: true
                    };
                }
                return {};
            };
        }

        // Add position configuration
        options.position = function ({ $datepicker, $target, $pointer, isViewChange, done }) {
            let popper = createPopper($target, $datepicker, {
                placement: 'bottom',
                modifiers: [
                    {
                        name: 'flip',
                        options: {
                            padding: {
                                top: 64
                            }
                        }
                    },
                    {
                        name: 'offset',
                        options: {
                            offset: [0, 20]
                        }
                    },
                    {
                        name: 'arrow',
                        options: {
                            element: $pointer
                        }
                    }
                ]
            });
            return function completeHide() {
                popper.destroy();
                done();
            };
        };

        // Initialize datepicker with all options
        new AirDatepicker(element, options);
    });
});



// Jalali datepicker
  document.addEventListener("DOMContentLoaded", function () {
    // Initial values
    jalaliDatepicker.startWatch({
      selector: "input[data-jdp]",  // No Change
      autoShow: true,               // Open with auto facuse
      autoHide: true,               // Click outside => closed
      hideAfterChange: true,        // Close after choose date
      persianDigits: true,      // Persian Numbers    
    //   minDate: "today",      // Start from today  
    });
  });