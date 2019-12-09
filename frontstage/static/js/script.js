"use strict";

function _instanceof(left, right) { if (right != null && typeof Symbol !== "undefined" && right[Symbol.hasInstance]) { return !!right[Symbol.hasInstance](left); } else { return left instanceof right; } }

function _toConsumableArray(arr) { return _arrayWithoutHoles(arr) || _iterableToArray(arr) || _nonIterableSpread(); }

function _nonIterableSpread() { throw new TypeError("Invalid attempt to spread non-iterable instance"); }

function _iterableToArray(iter) { if (Symbol.iterator in Object(iter) || Object.prototype.toString.call(iter) === "[object Arguments]") return Array.from(iter); }

function _arrayWithoutHoles(arr) { if (Array.isArray(arr)) { for (var i = 0, arr2 = new Array(arr.length); i < arr.length; i++) { arr2[i] = arr[i]; } return arr2; } }

function _classCallCheck(instance, Constructor) { if (!_instanceof(instance, Constructor)) { throw new TypeError("Cannot call a class as a function"); } }

function _defineProperties(target, props) { for (var i = 0; i < props.length; i++) { var descriptor = props[i]; descriptor.enumerable = descriptor.enumerable || false; descriptor.configurable = true; if ("value" in descriptor) descriptor.writable = true; Object.defineProperty(target, descriptor.key, descriptor); } }

function _createClass(Constructor, protoProps, staticProps) { if (protoProps) _defineProperties(Constructor.prototype, protoProps); if (staticProps) _defineProperties(Constructor, staticProps); return Constructor; }

async function submitButton() {
  var buttons = _toConsumableArray(document.querySelectorAll('.js-submit-btn'));

  var submitType;

  if (buttons.length) {
    buttons.forEach(function (button) {
      if (button.classList.contains('js-timer')) {
        submitType = 'timer';
      } else if (button.classList.contains('js-loader')) {
        submitType = 'loader';
      }

      new SubmitButton(button, submitType);
    });
  }
}
var i = 0;

var SubmitButton =
/*#__PURE__*/
function () {
  function SubmitButton(button, submitType) {
    _classCallCheck(this, SubmitButton);

    this.button = button;
    this.form = _toConsumableArray(document.getElementsByTagName('form'))[0] || null;
    this.submitType = submitType;

    if (this.submitType == 'loader') {
      if (this.form.length) {
        this.form.addEventListener('submit', this.loaderButton.bind(this));
      } else {
        this.button.addEventListener('click', this.loaderButton.bind(this));
      }
    } else if (this.submitType == 'timer') {
      if (this.form && this.form.length) {
        this.form.addEventListener('submit', this.timerButton.bind(this));
      } else {
        this.button.addEventListener('click', this.timerButton.bind(this));
      }
    }
  }

  _createClass(SubmitButton, [{
    key: "loaderButton",
    value: function loaderButton() {
      this.button.classList.add('is-loading');
      this.button.setAttribute('disabled', true);
    }
  }, {
    key: "timerButton",
    value: function timerButton(event) {
      if (this.button.tagName === 'A') {
        i++;

        if (i > 1) {
          event.preventDefault();
        }
      } else {
        this.button.setAttribute('disabled', true);
      }

      setTimeout(function (button) {
        button.removeAttribute('disabled');
        i = 0;
      }, 1000, this.button);
    }
  }]);

  return SubmitButton;
}();


submitButton();