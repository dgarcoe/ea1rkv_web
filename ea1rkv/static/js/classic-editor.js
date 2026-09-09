/* Self-hosted classic editing; keep Wagtail references when saving HTML. */
(() => {
  function initialise() {
    document.querySelectorAll('textarea.ea1rkv-classic-editor').forEach((field) => {
      if (field.dataset.classicReady || field.id.includes('__prefix__')) return;
      field.dataset.classicReady = 'true';
      tinymce.init({
        target: field,
        base_url: field.dataset.tinymceBase,
        suffix: '.min',
        license_key: 'gpl',
        language: 'es',
        height: 440,
        menubar: 'edit view insert format table tools',
        plugins: 'lists link table code fullscreen searchreplace wordcount',
        toolbar: 'undo redo | blocks | bold italic underline | bullist numlist blockquote | link clubimage clubdocument | table | removeformat fullscreen code',
        toolbar_mode: 'wrap',
        block_formats: 'Párrafo=p; Título 2=h2; Título 3=h3; Título 4=h4',
        branding: false,
        promotion: false,
        convert_urls: false,
        paste_data_images: false,
        extended_valid_elements: 'a[href|title|linktype|id],img[src|alt|data-wagtail-image|data-wagtail-format],span[data-wagtail-media|contenteditable]',
        content_style: 'body{font-family:system-ui,sans-serif;font-size:17px;line-height:1.65;padding:12px}img{max-width:100%;height:auto}table{border-collapse:collapse}td,th{border:1px solid #aaa;padding:8px}[data-wagtail-media]{display:block;background:#eef2f6;padding:16px}',
        setup(editor) {
          editor.ui.registry.addButton('clubimage', {
            icon: 'image', tooltip: 'Insertar imagen de la biblioteca',
            onAction() {
              const bookmark = editor.selection.getBookmark();
              new window.ImageChooserModal(field.dataset.imageChooser).open({}, (image) => {
                editor.selection.moveToBookmark(bookmark);
                editor.insertContent(editor.dom.createHTML('img', {
                  src: image.preview.url, alt: image.title,
                  'data-wagtail-image': image.id, 'data-wagtail-format': 'fullwidth',
                }));
              });
            },
          });
          editor.ui.registry.addButton('clubdocument', {
            icon: 'document-properties', tooltip: 'Insertar documento de la biblioteca',
            onAction() {
              const bookmark = editor.selection.getBookmark();
              new window.DocumentChooserModal(field.dataset.documentChooser).open({}, (doc) => {
                editor.selection.moveToBookmark(bookmark);
                editor.insertContent(editor.dom.createHTML('a', {
                  href: doc.url, linktype: 'document', id: doc.id,
                }, editor.dom.encode(doc.title)));
              });
            },
          });
          editor.on('change input undo redo', () => {
            editor.save();
            field.dispatchEvent(new Event('input', {bubbles: true}));
          });
        },
      }).catch(() => { delete field.dataset.classicReady; });
    });
  }
  document.addEventListener('submit', () => tinymce.triggerSave(), true);
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', initialise);
  else initialise();
  new MutationObserver(initialise).observe(document.documentElement, {childList: true, subtree: true});
})();
