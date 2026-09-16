// DOM element where the Timeline will be attached
var container = document.getElementById('visualization');

// Create a DataSet (allows two way data-binding)
var items = new vis.DataSet([
  { id: 1, content: 'گزینه 1', start: '2025-04-20' },
  { id: 2, content: 'گزینه 2', start: '2025-04-14' },
  { id: 3, content: 'گزینه 3', start: '2025-04-18' },
  { id: 4, content: 'گزینه 4', start: '2025-04-16', end: '2025-04-19' },
  { id: 5, content: 'گزینه 5', start: '2025-04-25' },
  { id: 6, content: 'گزینه 6', start: '2025-04-27', type: 'point' }
]);

// Configuration for the Timeline
var options = {};

// Create a Timeline
var timeline = new vis.Timeline(container, items, options);


// create groups to highlight groupUpdate
var groups = new vis.DataSet([
  { id: 1, content: 'گروه 1' },
  { id: 2, content: 'گروه 2' }
]);
// create a DataSet with items
var items = new vis.DataSet([
  { id: 1, content: 'قابل ویرایش', editable: true, start: '2025-08-23', group: 1 },
  { id: 2, content: 'قابل ویرایش', editable: true, start: '2025-08-23T23:00:00', group: 2 },
  { id: 3, content: 'فقط خواندنی', editable: false, start: '2025-08-24T16:00:00', group: 1 },
  { id: 4, content: 'فقط خواندنی', editable: false, start: '2025-08-26', end: '2025-09-02', group: 2 },
  { id: 5, content: 'فقط ویرایش زمان', editable: { updateTime: true, updateGroup: false, remove: false }, start: '2025-08-28', group: 1 },
  { id: 6, content: 'فقط ویرایش گروه', editable: { updateTime: false, updateGroup: true, remove: false }, start: '2025-08-29', group: 2 },
  { id: 7, content: 'فقط حذف', editable: { updateTime: false, updateGroup: false, remove: true }, start: '2025-08-31', end: '2025-09-03', group: 1 },
  { id: 8, content: 'پیش‌فرض', start: '2025-09-04T12:00:00', group: 2 }
]);

var container = document.getElementById('visualization2');
var options = {
  editable: true   // default for all items
};

var timeline = new vis.Timeline(container, items, groups, options);