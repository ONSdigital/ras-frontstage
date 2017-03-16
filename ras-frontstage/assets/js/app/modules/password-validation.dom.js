'use strict';

import { default as validation,
	validateCharacterLength,
	validateHasCapitalLetter,
	validateHasSymbol,
	validateHasNumber,
	validateEqual } from '../../modules/validators';

export const newPasswordFieldGroupClass = 'js-new-password-group',
	passwordFieldClass = 'js-new-password',
	passwordConfirmationFieldClass = 'js-confirm-new-password',

	fieldStrengthValidationConfig = [
		validateCharacterLength,
		validateHasCapitalLetter,
		validateHasSymbol,
		validateHasNumber
	],

	errorEmitter = $({});

export default () => {

	/**
	 * Find new password field scope
	 */
	$(`.${newPasswordFieldGroupClass}`).each((i, el) => {

		/**
		 * Find scoped fields
		 */
		let newPassword = $(el).find(`.${passwordFieldClass}`),
			confirmPassword = $(el).find(`.${passwordConfirmationFieldClass}`);

		applyPasswordValidation(newPassword, confirmPassword);
	});
}

function applyPasswordValidation($newPasswordEl, $confirmPasswordEl) {

	let areFieldsEqual = validateFieldsEqual.bind({}, $newPasswordEl, $confirmPasswordEl),
		resetFieldsDispatch = function () {

			errorEmitter.trigger('user-error:reset', [{
				'fields': [
					$newPasswordEl,
					$confirmPasswordEl
				]
			}]);
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

		if(!areFieldsEqual()) {

			let messages = ['Your passwords do not match'],
				failedStrengthValidation = validatePasswordField($confirmPasswordEl);

			if(failedStrengthValidation.length) {
				messages.unshift('This password does not meet the criteria');
			}

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
