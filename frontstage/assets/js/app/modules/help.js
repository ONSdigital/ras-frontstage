import domready from '../../../../../common/assets/js/app/modules/domready';

domready(function () {
  var btn = document.querySelector('.js-help-btn');
  var help = document.querySelector('.js-help-body');
  var classClosed = 'is-closed';
  var firstClosed = 'first-closed';

  var openedByClick = false;

  if (help === null || btn === null) {
    return false;
  }

  btn.classList.remove('u-vh');
  help.classList.add(classClosed);

  help.addEventListener('focus', function (e) {
    help.classList.remove(classClosed);
  }, true);

  help.addEventListener('blur', function (e) {
    if (!openedByClick) {
      help.classList.add(classClosed);
    }
  }, true);

  btn.addEventListener('click', function (e) {
    e.preventDefault();
    openedByClick = !openedByClick;
    help.classList.remove(firstClosed);
    help.classList.toggle(classClosed);
  });
});


/*
domready(() => {
  const btn = document.querySelector('.js-help-btn');
  const help = document.querySelector('.js-help-body');
  const classClosedInit = 'is-closed--init';
  const classClosed = 'is-closed';

  let openedByClick = false;

  if (help === null || btn === null) {
    return false;
  }

  //help.classList.add(classClosedInit);
  help.classList.add(classClosed);
  btn.classList.remove('u-vh');

  help.addEventListener('focus', e => {
    help.classList.remove(classClosed);
  }, true);

  help.addEventListener('blur', e => {
    if (!openedByClick) {
      help.classList.add(classClosed);
    }
  }, true);

  btn.addEventListener('click', e => {
    e.preventDefault();
    openedByClick = !openedByClick;
    help.classList.toggle(classClosed);
  });
});
*/
