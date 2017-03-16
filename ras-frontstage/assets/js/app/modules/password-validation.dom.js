'use strict';

import { default as validation,
	validateCharacterLength,
	validateHasCapitalLetter,
	validateHasSymbol,
	validateHasNumber,
	validateEqual } from '../../modules/validators';
import Emitter from '../helpers/emitter';

export const newPasswordFieldGroupClass = 'js-new-password-group',
	passwordFieldClass = 'js-new-password',
	passwordConfirmationFieldClass = 'js-confirm-new-password',

	/**
	 * Specify validation to use
	 * @type {[*]}
	 */
	fieldStrengthValidationConfig = [
		validateCharacterLength,
		validateHasCapitalLetter,
		validateHasSymbol,
		validateHasNumber
	],

	errorEmitter = Emitter.create();

export default () => {

	/**
	 * Find new password field scope
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

function applyPasswordValidation(scope) {

	let areFieldsEqual = validateFieldsEqual.bind({}, scope.$newPasswordEl, scope.$confirmPasswordEl),

		resetFieldsDispatch = function () {
			errorEmitter.trigger('user-error:reset', [{
				'fields': [
					scope.$newPasswordEl,
					scope.$confirmPasswordEl
				]
			}]);
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

function validatePasswordField($el) {

	let str = $el.val();

	return fieldStrengthValidationConfig
		.filter(validate => !validate(str));
}

function validateFieldsEqual($newPasswordEl, $confirmPasswordEl) {

	return validateEqual($newPasswordEl.val(), $confirmPasswordEl.val());
}

function passwordUserError(opts) {

	errorEmitter.trigger('user-error', [{
		'fields': opts.fields
	}]);
}
