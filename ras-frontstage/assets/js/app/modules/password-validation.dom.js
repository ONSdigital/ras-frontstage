import { default as validation,
	validateCharacterLength,
	validateHasCapitalLetter,
	validateHasSymbol,
	validateHasNumber,
	validateEqual } from '../../modules/validators';

export const newPasswordFieldGroup = 'js-new-password-group',
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
	$(`.${newPasswordFieldGroup}`).each((i, el) => {

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
		validatePasswordField($newPasswordEl)
	});

	$confirmPasswordEl.on('blur', () => {
		areFieldsEqual()
	});

	$newPasswordEl.on('focus', () => resetFieldsDispatch());
	$confirmPasswordEl.on('focus', () => resetFieldsDispatch());
}

function validatePasswordField($el) {

	let str = $el.val(),
		failedStrengthValidation = fieldStrengthValidationConfig
			.filter(validate => !validate(str));

	return failedStrengthValidation.length ?
		(() => {
			errorEmitter.trigger('user-error', {
				'page-title': 'Your password doesn\'t meet the requirements',
				'page-link-message': 'Please choose a different password',

				'fields': [{
					'el': $el[0],
					'message': 'This password does not meet the criteria'
				}]
			});
			return false;
		})() :
		true;
}

function validateFieldsEqual($newPasswordEl, $confirmPasswordEl) {

	return !validateEqual($newPasswordEl.val(), $confirmPasswordEl.val()) ?
		(() => {
			errorEmitter.trigger('user-error', [{
				'page-title': 'Your passwords do not match',
				'page-link-message': 'Please check the passwords and try again',

				'fields': [{
					'el': $confirmPasswordEl[0],
					'message': 'Your passwords do not match'
				}]
			}]);
			return false;
		})() :
		true;
}
