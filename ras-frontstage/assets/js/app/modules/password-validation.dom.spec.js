import { default as passwordValidationModule,
	errorEmitter as passwordValidationModuleErrorEmitter,
	newPasswordFieldGroupClass,
	passwordFieldClass,
	passwordConfirmationFieldClass } from './password-validation.dom';

describe('password validation [DOM module]', () => {

	let el,

		fixture =
		`<div class="${newPasswordFieldGroupClass}">
			<input class="${passwordFieldClass}" value="" type="text" />
			<input class="${passwordConfirmationFieldClass}" value="" type="text" />
		</div>`;

	beforeEach(() => {
		el = document.createElement('div');
		el.innerHTML = fixture;
		document.body.appendChild(el);

		passwordValidationModule();
	});

	afterEach(() => {
		document.body.removeChild(el);
	});

	it('DOM to be setup correctly', function() {
		expect($(`.${newPasswordFieldGroupClass}`)[0]).not.toBeFalsy();
		expect($(`.${passwordFieldClass}`)[0]).not.toBeFalsy();
		expect($(`.${passwordConfirmationFieldClass}`)[0]).not.toBeFalsy();
	});

	describe('new pasword [field]', () => {

		let $newPasswordEl,
			stub;

		beforeEach(() => {
			$newPasswordEl = $(`.${passwordFieldClass}`);
			stub = {
				fakeHandler: function (e, data) {
					console.log(e, data);
				}
			};
			spyOn(stub, 'fakeHandler');
			passwordValidationModuleErrorEmitter.on('user-error', stub.fakeHandler);
		});

		describe('when unfocused', () => {

			it('should validate without an error response when supplied with a valid password', () => {
				$newPasswordEl.val('Valid password123%');
				$newPasswordEl.trigger('blur');

				expect(stub.fakeHandler).not.toHaveBeenCalled();
			});

			it('should validate with an error response when supplied with an invalid password', () => {
				$newPasswordEl.val('should fail validation');
				$newPasswordEl.trigger('blur');

				expect(stub.fakeHandler).toHaveBeenCalledTimes(1);
			});
		});
	});

	describe('confirm password [field]', () => {

		let $newPasswordEl,
			$confirmPassword,
			stub;

		beforeEach(() => {
			$newPasswordEl = $(`.${passwordFieldClass}`);
			$confirmPassword = $(`.${passwordConfirmationFieldClass}`);
			stub = {
				fakeHandler: function (e, data) {
					console.log(e, data);
				}
			};
			spyOn(stub, 'fakeHandler');
			passwordValidationModuleErrorEmitter.on('user-error', stub.fakeHandler);
		});

		describe('when unfocused', () => {

			it('should validate without response new password and confirm password field are equal', () => {
				$newPasswordEl.val('Valid_password123%');
				$confirmPassword.val('Valid_password123%');
				$confirmPassword.trigger('blur');

				expect(stub.fakeHandler).not.toHaveBeenCalled();
			});

			it('should validate with error response new password and confirm password field are not equal', () => {
				$newPasswordEl.val('Valid_password123%');
				$confirmPassword.val('Other_valid_password123%');
				$confirmPassword.trigger('blur');

				expect(stub.fakeHandler).toHaveBeenCalledTimes(1);
			});
		});
	});

});
