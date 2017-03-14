import { default as passwordValidationModule,
	newPasswordFieldGroupClass,
	passwordFieldClass,
	passwordConfirmationFieldClass } from './password-validation.dom';

describe('password validation [DOM module]', () => {

	let DOM = $(
		`<div class="${newPasswordFieldGroupClass}">
			<input class="${passwordFieldClass}" value="" type="text" />
			<input class="${passwordConfirmationFieldClass}" value="" type="text" />
		</div>`
	);

	beforeEach(() => {

		console.log(expect(DOM).toHaveClass);
		//$(document).appendTo(DOM);
		//passwordValidationModule();
	});

	/*it('Should work', () => {
	 expect(true).toBe(false);
	 });*/

	it('should do some assertions', function() {
		expect(true).toBe(true);
		expect(DOM).toHaveClass(newPasswordFieldGroupClass);
	});

});
