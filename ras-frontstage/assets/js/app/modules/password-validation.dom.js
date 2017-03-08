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
	];

export let errorEmitter = $({});

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

	let areFieldsEqual = validateFieldsEqual.bind({}, $newPasswordEl, $confirmPasswordEl);

	$newPasswordEl.on('blur', () => {
		validatePasswordField($newPasswordEl) &&
		areFieldsEqual()
	});

	$confirmPasswordEl.on('blur', () => {
		areFieldsEqual()
	});
}

function validatePasswordField($el) {

	let str = $el.val(),
		failedStrengthValidation = fieldStrengthValidationConfig
			.filter(validate => !validate(str));

	return failedStrengthValidation.length ?
		(() => {
			errorEmitter.trigger('error', {
				'title': 'Your password doesn\'t meet the requirements',
				'link-message': 'Please choose a different password'
			});
			return false;
		})() :
		true;
}

function validateFieldsEqual($newPasswordEl, $confirmPasswordEl) {

	return !validateEqual($newPasswordEl.val(), $confirmPasswordEl.val()) ?
		(() => {
			errorEmitter.trigger('error', [{
				'title': 'Your passwords do not match',
				'link-message': 'Please check the passwords and try again'
			}]);
			return false;
		})() :
		true;
}
