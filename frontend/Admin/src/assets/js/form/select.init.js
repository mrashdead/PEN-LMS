VirtualSelect.init({
  ele: '#sample-select',
  options: [
    { label: 'گزینه 1', value: '1' },
    { label: 'گزینه 2', value: '2' },
    { label: 'گزینه 3', value: '3' },
  ],
  selectedValue: 0
});

VirtualSelect.init({
  ele: '#search-select',
  options: [
    { label: 'گزینه 1', value: '1' },
    { label: 'گزینه 2', value: '2' },
    { label: 'گزینه 3', value: '3' },
  ],
  selectedValue: 0,
  search: true,
});

VirtualSelect.init({
  ele: '#multiple-select',
  options: [
    { label: 'گزینه 1', value: '1' },
    { label: 'گزینه 2', value: '2' },
    { label: 'گزینه 3', value: '3' },
  ],
  selectedValue: 0,
  multiple: true,
});

VirtualSelect.init({
  ele: '#multipleWithoutSearchSelect',
  options: [
    { label: 'گزینه 1', value: '1' },
    { label: 'گزینه 2', value: '2' },
    { label: 'گزینه 3', value: '3' },
    { label: 'گزینه 4', value: '4' },
    { label: 'گزینه 5', value: '5' },
    { label: 'گزینه 6', value: '6' },
    { label: 'گزینه 7', value: '7' },
    { label: 'گزینه 8', value: '8' },
  ],
  selectedValue: 0,
  multiple: true,
  search: false,
});

VirtualSelect.init({
  ele: '#disabledOptionSelect',
  options: [
    { label: 'گزینه 1', value: '1' },
    { label: 'گزینه 2', value: '2' },
    { label: 'گزینه 3', value: '3' },
    { label: 'گزینه 4', value: '4' },
    { label: 'گزینه 5', value: '5' },
    { label: 'گزینه 6', value: '6' },
    { label: 'گزینه 7', value: '7' },
    { label: 'گزینه 8', value: '8' },
  ],
  selectedValue: 0,
  disabledOptions: [2, 6, 8]
});

VirtualSelect.init({
  ele: '#optionGroupSelect',
  options: [
    {
      label: 'گروه گزینه 1',
      options: [
        { label: 'گزینه 1', value: '1' },
        { label: 'گزینه 2', value: '2' },
        { label: 'گزینه 3', value: '3' },
        { label: 'گزینه 4', value: '4' },
        { label: 'گزینه 5', value: '5' },
        { label: 'گزینه 6', value: '6' },
        { label: 'گزینه 7', value: '7' },
        { label: 'گزینه 8', value: '8' },
      ]
    },
    {
      label: 'گروه گزینه 2',
      options: [
        { label: 'گزینه 1', value: '1' },
        { label: 'گزینه 2', value: '2' },
        { label: 'گزینه 3', value: '3' },
        { label: 'گزینه 4', value: '4' },
        { label: 'گزینه 5', value: '5' },
        { label: 'گزینه 6', value: '6' },
        { label: 'گزینه 7', value: '7' },
        { label: 'گزینه 8', value: '8' },
      ]
    },
  ],
  multiple: true,
  search: false,
});

VirtualSelect.init({
  ele: '#preselectValue',
  options: [
    { label: 'گزینه 1', value: '1' },
    { label: 'گزینه 2', value: '2' },
    { label: 'گزینه 3', value: '3' },
    { label: 'گزینه 4', value: '4' },
    { label: 'گزینه 5', value: '5' },
    { label: 'گزینه 6', value: '6' },
    { label: 'گزینه 7', value: '7' },
    { label: 'گزینه 8', value: '8' },
  ],
  selectedValue: 3,
});

VirtualSelect.init({
  ele: '#preselectMultipleValue',
  options: [
    { label: 'گزینه 1', value: '1' },
    { label: 'گزینه 2', value: '2' },
    { label: 'گزینه 3', value: '3' },
    { label: 'گزینه 4', value: '4' },
    { label: 'گزینه 5', value: '5' },
    { label: 'گزینه 6', value: '6' },
    { label: 'گزینه 7', value: '7' },
    { label: 'گزینه 8', value: '8' },
  ],
  selectedValue: [3, 4],
  multiple: true,
});


VirtualSelect.init({
  ele: '#hideClearButton',
  options: [
    { label: 'گزینه 1', value: '1' },
    { label: 'گزینه 2', value: '2' },
    { label: 'گزینه 3', value: '3' },
    { label: 'گزینه 4', value: '4' },
    { label: 'گزینه 5', value: '5' },
    { label: 'گزینه 6', value: '6' },
    { label: 'گزینه 7', value: '7' },
    { label: 'گزینه 8', value: '8' },
  ],
  selectedValue: 0,
  hideClearButton: true,
});

VirtualSelect.init({
  ele: '#customWidthDropbox',
  options: [
    { label: 'گزینه 1', value: '1' },
    { label: 'گزینه 2', value: '2' },
    { label: 'گزینه 3', value: '3' },
    { label: 'گزینه 4', value: '4' },
    { label: 'گزینه 5', value: '5' },
    { label: 'گزینه 6', value: '6' },
    { label: 'گزینه 7', value: '7' },
    { label: 'گزینه 8', value: '8' },
  ],
  selectedValue: 0,
  dropboxWidth: '130px',
});

VirtualSelect.init({
  ele: '#allowNewOption',
  options: [
    { label: 'گزینه 1', value: '1' },
    { label: 'گزینه 2', value: '2' },
    { label: 'گزینه 3', value: '3' },
    { label: 'گزینه 4', value: '4' },
    { label: 'گزینه 5', value: '5' },
    { label: 'گزینه 6', value: '6' },
    { label: 'گزینه 7', value: '7' },
    { label: 'گزینه 8', value: '8' },
  ],
  allowNewOption: true,
});

VirtualSelect.init({
  ele: '#markMatchedLabel',
  options: [
    { label: 'گزینه 1', value: '1' },
    { label: 'گزینه 2', value: '2' },
    { label: 'گزینه 3', value: '3' },
    { label: 'گزینه 4', value: '4' },
    { label: 'گزینه 5', value: '5' },
    { label: 'گزینه 6', value: '6' },
    { label: 'گزینه 7', value: '7' },
    { label: 'گزینه 8', value: '8' },
  ],
  markSearchResults: true,
});

VirtualSelect.init({
  ele: '#showingSelectedOption',
  options: [
    { label: 'گزینه 1', value: '1' },
    { label: 'گزینه 2', value: '2' },
    { label: 'گزینه 3', value: '3' },
    { label: 'گزینه 4', value: '4' },
    { label: 'گزینه 5', value: '5' },
    { label: 'گزینه 6', value: '6' },
    { label: 'گزینه 7', value: '7' },
    { label: 'گزینه 8', value: '8' },
  ],
  showSelectedOptionsFirst: true,
  multiple: true,
});

VirtualSelect.init({
  ele: '#aliasForSearching',
  options: [
    { label: 'رنگ‌ها', value: 'colors', alias: 'نارنجی, قرمز' },
    { label: 'میوه‌ها', value: 'fruits', alias: ['پرتقال', 'سیب'] },
    { label: 'ماه‌ها', value: 'months', alias: 'فروردین' },
    { label: 'سایر', value: 'others' }
  ],
  selectedValue: 0
});

VirtualSelect.init({
  ele: '#maximumValues',
  options: [
    { label: 'گزینه 1', value: '1' },
    { label: 'گزینه 2', value: '2' },
    { label: 'گزینه 3', value: '3' },
    { label: 'گزینه 4', value: '4' },
    { label: 'گزینه 5', value: '5' },
    { label: 'گزینه 6', value: '6' },
    { label: 'گزینه 7', value: '7' },
    { label: 'گزینه 8', value: '8' },
  ],
  maxValues: 4,
  multiple: true,
});

VirtualSelect.init({
  ele: '#labelDescription',
  options: [
    { label: 'گزینه 1', value: '1', description: 'توضیحات 1' },
    { label: 'گزینه 2', value: '2', description: 'توضیحات 2' },
    { label: 'گزینه 3', value: '3', description: 'توضیحات 3' },
  ],
  hasOptionDescription: true,
  search: false,
});

VirtualSelect.init({
  ele: '#showOptionOnlySearch',
  options: [
    { label: 'گزینه 1', value: '1', description: 'توضیحات 1' },
    { label: 'گزینه 2', value: '2', description: 'توضیحات 2' },
    { label: 'گزینه 3', value: '3', description: 'توضیحات 3' },
  ],
  showOptionsOnlyOnSearch: true,
});

VirtualSelect.init({ ele: 'select' });

VirtualSelect.init({
  ele: "#sample-image",
  options: [
    {
      label: "گزینه‌های 1",
      value: "1",
      description: "توضیحات 1",
      classNames: "fo",
    },
    {
      label: "گزینه‌های 2",
      value: "2",
      description: "توضیحات 2",
      classNames: "nz",
    },
    {
      label: "گزینه‌های 3",
      value: "3",
      description: "توضیحات 3",
      classNames: "bi",
    },
  ],
  labelRenderer: sampleLabelRenderer,
});

function sampleLabelRenderer(data) {
  let prefix = "";
  /** skipping options those are added newly by allowNewOption feature */
  if (!data.isCurrentNew && !data.isNew)  /** project developer has to add their own logic to create image/icon tag */
    prefix = `<i class="flag flag-${data.classNames} ltr:mr-2 rtl:ml-2"></i>`;
  return `${prefix}${data.label}`;
}

VirtualSelect.init({
  ele: '#popup-multi-select',
  options: [
    { label: 'گزینه 1', value: '1' },
    { label: 'گزینه 2', value: '2' },
    { label: 'گزینه 3', value: '3' },
    { label: 'گزینه 4', value: '4' },
    { label: 'گزینه 5', value: '5' },
    { label: 'گزینه 6', value: '6' },
    { label: 'گزینه 7', value: '7' },
    { label: 'گزینه 8', value: '8' },
    { label: 'گزینه 9', value: '9' },
    { label: 'گزینه 10', value: '10' },
  ],
  selectedValue: 0,
  multiple: true,
  popupDropboxBreakpoint: '3000px'
});

VirtualSelect.init({
  ele: '#popup-single-select',
  options: [
    { label: 'گزینه 1', value: '1' },
    { label: 'گزینه 2', value: '2' },
    { label: 'گزینه 3', value: '3' },
    { label: 'گزینه 4', value: '4' },
    { label: 'گزینه 5', value: '5' },
  ],
  selectedValue: 0,
  popupDropboxBreakpoint: '3000px'
});


VirtualSelect.init({
  ele: '#value-tag',
  options: [
    { label: 'گزینه 1', value: '1' },
    { label: 'گزینه 2', value: '2' },
    { label: 'گزینه 3', value: '3' },
    { label: 'گزینه 4', value: '4' },
    { label: 'گزینه 5', value: '5' },
  ],
  multiple: true,
  showValueAsTags: true,
});
