import {
	default as validationModule,
	validateCharacterLength,
	validateHasCapitalLetter,
	validateHasSymbol,
	validateHasNumber,
	validateEqual,
	validateIsEmail
} from './validators';

describe('validator [module]', () => {

	describe('validateEqual [method]', () => {

		it('should return true when both strings compared are equal', () => {
			expect(validateEqual('Some string 123 %)@', 'Some string 123 %)@')).toBe(true);
		});

		it('should return true when both strings compared are not equal', () => {
			expect(validateEqual('Some string 123 %)@', 'nope')).toBe(false);
		});
	});

	describe('validateCharacterLength [method]', () => {

		it('should return true when supplied with a valid minimum length string of 8', () => {
			expect(validateCharacterLength('long enough')).toBe(true);
		});

		it('should return false when supplied with an invalid length password', () => {
			expect(validateCharacterLength('invalid')).toBe(false);
		});
	});

	describe('validateHasCapitalLetter [method]', () => {

		it('should return true when supplied with a string that has a capital letter', () => {
			expect(validateHasCapitalLetter('capital Letter')).toBe(true);
		});

		it('should return false when supplied with a string without a capital letter', () => {
			expect(validateHasCapitalLetter('invalid lower case only')).toBe(false);
		});
	});

	describe('validateHasSymbol [method]', () => {

		it('should return true when supplied a string with any of the following symbols: !$£%^&*()_+|~-=`{}[]:";\'<>?,./', () => {
			expect(validateHasSymbol('!')).toBe(true);
			expect(validateHasSymbol('$')).toBe(true);
			expect(validateHasSymbol('£')).toBe(true);
			expect(validateHasSymbol('%')).toBe(true);
			expect(validateHasSymbol('^')).toBe(true);
			expect(validateHasSymbol('&')).toBe(true);
			expect(validateHasSymbol('*')).toBe(true);
			expect(validateHasSymbol('(')).toBe(true);
			expect(validateHasSymbol(')')).toBe(true);
			expect(validateHasSymbol('_')).toBe(true);
			expect(validateHasSymbol('+')).toBe(true);
			expect(validateHasSymbol('|')).toBe(true);
			expect(validateHasSymbol('~')).toBe(true);
			expect(validateHasSymbol('-')).toBe(true);
			expect(validateHasSymbol('=')).toBe(true);
			expect(validateHasSymbol('`')).toBe(true);
			expect(validateHasSymbol('{')).toBe(true);
			expect(validateHasSymbol('}')).toBe(true);
			expect(validateHasSymbol('[')).toBe(true);
			expect(validateHasSymbol(']')).toBe(true);
			expect(validateHasSymbol(':')).toBe(true);
			expect(validateHasSymbol('"')).toBe(true);
			expect(validateHasSymbol(';')).toBe(true);
			expect(validateHasSymbol('\'')).toBe(true);
			expect(validateHasSymbol('<')).toBe(true);
			expect(validateHasSymbol('>')).toBe(true);
			expect(validateHasSymbol('?')).toBe(true);
			expect(validateHasSymbol(',')).toBe(true);
			expect(validateHasSymbol('.')).toBe(true);
			expect(validateHasSymbol('/')).toBe(true);
		});

		it('should return false when supplied a string without a symbol', () => {
			expect(validateHasSymbol('Not 1 symbol')).toBe(false);
		});
	});

	describe('validateHasNumber [method]', () => {

		it('should return true when supplied with a number', () => {
			expect(validateHasNumber('has the number 5')).toBe(true);
		});

		it('should return false when supplied without a number', () => {
			expect(validateHasNumber('has no number')).toBe(false);
		});
	});

	describe('validateIsEmail [method]', () => {

		it('should return true when supplied with a valid email address', () => {
			expect(validateIsEmail('test@testing.com')).toBe(true);
		});

		it('should return false when suplied with an invalid email address', () => {
			expect(validateIsEmail('fake email!!.')).toBe(false);
		});
	});

	describe('module', () => {

		it('shoxwuld be configurable', () => {
			validationModule({
				characterLen: {
					min: 6
				}
			});

			expect(validateCharacterLength('six ch')).toBe(true);
		})
	});

});
