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
	$(`.${newPasswordFieldGroupClass}`).each((i, el) => applyPasswordValidation({
		$scopeEl: $(el)
	}));
}

/**
 * module:passwordValidation~applyPasswordValidation
 * @param scope An object representing the current scope. With a collection of associated fields.
 */
function applyPasswordValidation(scope) {

	/**
	 * Find scoped fields
	 */
	let $scopeEl = scope.$scopeEl,
		$newPasswordEl = $scopeEl.find(`.${passwordFieldClass}`),
		$confirmPasswordEl = $scopeEl.find(`.${passwordConfirmationFieldClass}`);

	let areFieldsEqual = validateFieldsEqual.bind({}, $newPasswordEl, $confirmPasswordEl),

		resetFieldsDispatch = function () {
			errorEmitter.trigger('user-error:reset', {
				'fields': [
					$newPasswordEl,
					$confirmPasswordEl
				]
			});
		};

	$newPasswordEl.on('blur', () => {

		let failedStrengthValidation = validatePasswordField($newPasswordEl);

		if(failedStrengthValidation.length) {

			passwordUserError({
				'fields': [{
					'el': $newPasswordEl[0],
					'messages': ['This password does not meet the criteria']
				}]
			});
		}
	});

	$confirmPasswordEl.on('blur', () => {

		let messages = [],
			areFieldsEqualResult = areFieldsEqual(),
			failedStrengthValidationResults = validatePasswordField($confirmPasswordEl);

		if(!areFieldsEqualResult) {
			messages.push('Your passwords do not match');
		}

		if(failedStrengthValidationResults.length) {
			messages.unshift('This password does not meet the criteria');
		}

		if(!areFieldsEqualResult || failedStrengthValidationResults.length) {
			passwordUserError({
				'fields': [{
					'el': $confirmPasswordEl[0],
					'messages': messages
				}]
			});
		}
	});

	$newPasswordEl.on('focus', resetFieldsDispatch);
	$confirmPasswordEl.on('focus', resetFieldsDispatch);
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
