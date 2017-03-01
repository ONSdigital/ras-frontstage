import domready from '../../../../common/assets/js/app/modules/domready';
import { default as passwordValidation,
	validateCharacterLength,
	validateHasCapitalLetter,
	validateHasSymbol,
	validationHasNumber } from './modules/password-validation';

const passwordValidatorClass = 'js-password-validation',
	fieldValidationConfig = [
		{
			FUNC: validateCharacterLength
		},
		{
			FUNC: validateHasCapitalLetter
		},
		{
			FUNC: validateHasSymbol
		},
		{
			FUNC: validationHasNumber
		}
	];

function appPasswordValidation() {
	passwordValidation();

	$(`.${passwordValidatorClass}`).each((i, el) => {
		applyPasswordValidation($(el));
	});
}

function applyPasswordValidation($el) {
	$el.on('blur', () => { validateField($el) });
}

function validateField($el) {
	let str = $el.val(),
		failedValidation = fieldValidationConfig.filter(item => !item.FUNC(str));

	console.log(failedValidation);
}

domready(appPasswordValidation);
