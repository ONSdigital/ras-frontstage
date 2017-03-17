'use strict';

import { default as validation,
	validateCharacterLength,
	validateHasCapitalLetter,
	validateHasSymbol,
	validateHasNumber,
	validateEqual } from '../../modules/validators';
import Emitter from '../helpers/emitter';

/**
 * Export classes for testing
 */
export const newPasswordFieldGroupClass = 'js-new-password-group',
	passwordFieldClass = 'js-new-password',
	passwordConfirmationFieldClass = 'js-confirm-new-password',

	errorEmitter = Emitter.create();

/**
 * Specify validation to use
 */
let fieldStrengthValidationConfig = [
	validateCharacterLength,
	validateHasCapitalLetter,
	validateHasSymbol,
	validateHasNumber
];

/**
 * @module passwordValidation
 * @description DOM module to attached password validation behaviours to new password and confirm password type fields.
 */
export default () => {

	/**
	 * Find password fields scope
	 */
	$(`.${newPasswordFieldGroupClass}`).each((i, el) => {

		/**
		 * Find scoped fields
		 */
		let $scopeEl = $(el),
			$newPasswordEl = $scopeEl.find(`.${passwordFieldClass}`),
			$confirmPasswordEl = $scopeEl.find(`.${passwordConfirmationFieldClass}`);

		applyPasswordValidation({ $scopeEl, $newPasswordEl, $confirmPasswordEl });
	});
}

/**
 * module:passwordValidation~applyPasswordValidation
 * @param scope An object representing the current scope. With a collection of associated fields.
 */
function applyPasswordValidation(scope) {

	let areFieldsEqual = validateFieldsEqual.bind({}, scope.$newPasswordEl, scope.$confirmPasswordEl),

		resetFieldsDispatch = function () {
			errorEmitter.trigger('user-error:reset', {
				'fields': [
					scope.$newPasswordEl,
					scope.$confirmPasswordEl
				]
			});
		};

	scope.$newPasswordEl.on('blur', () => {

		let failedStrengthValidation = validatePasswordField(scope.$newPasswordEl);

		if(failedStrengthValidation.length) {

			passwordUserError({
				'fields': [{
					'el': scope.$newPasswordEl[0],
					'messages': ['This password does not meet the criteria']
				}]
			});
		}
	});

	scope.$confirmPasswordEl.on('blur', () => {

		let messages = [],
			areFieldsEqualResult = areFieldsEqual(),
			failedStrengthValidationResults = validatePasswordField(scope.$confirmPasswordEl);

		if(!areFieldsEqualResult) {
			messages.push('Your passwords do not match');
		}

		if(failedStrengthValidationResults.length) {
			messages.unshift('This password does not meet the criteria');
		}

		if(!areFieldsEqualResult || failedStrengthValidationResults.length) {
			passwordUserError({
				'fields': [{
					'el': scope.$confirmPasswordEl[0],
					'messages': messages
				}]
			});
		}
	});

	scope.$newPasswordEl.on('focus', resetFieldsDispatch);
	scope.$confirmPasswordEl.on('focus', resetFieldsDispatch);
}

/**
 * module:passwordValidation~validatePasswordField
 * @param $el A jQuery element with a password type of field.
 * @returns {Array.<*>}
 */
function validatePasswordField($el) {

	let str = $el.val();

	return fieldStrengthValidationConfig
		.filter(validate => !validate(str));
}

/**
 * module:passwordValidation~validateFieldsEqual
 * @param $newPasswordEl
 * @param $confirmPasswordEl
 * @returns {*}
 */
function validateFieldsEqual($newPasswordEl, $confirmPasswordEl) {

	return validateEqual($newPasswordEl.val(), $confirmPasswordEl.val());
}

/**
 * module:passwordValidation~passwordUserError
 * @param opts Data needed to produce an error
 */
function passwordUserError(opts) {

	errorEmitter.trigger('user-error', {
		'fields': opts.fields
	});
}
