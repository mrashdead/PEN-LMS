import * as FilePond from 'filepond';
import FilePondPluginImagePreview from 'filepond-plugin-image-preview';
import FilePondPluginImageExifOrientation from 'filepond-plugin-image-exif-orientation';
import FilePondPluginFileValidateSize from 'filepond-plugin-file-validate-size';
import FilePondPluginImageEdit from 'filepond-plugin-image-edit';
import 'filepond/dist/filepond.min.css';
import 'filepond-plugin-image-preview/dist/filepond-plugin-image-preview.css';

FilePond.registerPlugin(
    FilePondPluginImagePreview,
    FilePondPluginImageExifOrientation,
    FilePondPluginFileValidateSize,
    FilePondPluginImageEdit
);

FilePond.create(
    document.querySelector('#multipleFileUpload')
);

FilePond.create(
    document.querySelector('#squareUpload'),
    {
        labelIdle: `Drag & Drop your picture or <span class="filepond--label-action">Browse</span>`,
        imagePreviewHeight: 120,
        imageCropAspectRatio: '1:1',
        // imageResizeTargetWidth: 50,
        // imageResizeTargetHeight: 50,
        stylePanelLayout: 'compact circle',
        styleLoadIndicatorPosition: 'center bottom',
        styleProgressIndicatorPosition: 'right bottom',
        styleButtonRemoveItemPosition: 'left bottom',
        styleButtonProcessItemPosition: 'right bottom',
    }
);