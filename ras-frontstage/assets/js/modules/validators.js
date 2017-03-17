'use strict';

/**
 * Default configuration for module
 * @type {{characterLen: {min: number, max: Number}}}
 */
let config = {
		characterLen: {
			min: 8,
			max: Infinity
		}
	};

/**
 * Check two strings are equal
 * @param str1
 * @param str2
 * @returns {boolean}
 */
export function validateEqual(str1, str2) {
	return str1 === str2;
}

/**
 * Check string length is within the correct range
 * @param str
 * @returns {boolean}
 */
export function validateCharacterLength(str) {
	return str.length >= config.characterLen.min && str.length <= config.characterLen.max;
}

/**
 * Check string has capital letter
 * @param str
 * @returns {boolean}
 */
export function validateHasCapitalLetter(str) {
	return /[A-Z]/.test(str);
}

/**
 * Check string has symbol
 * @param str
 * @returns {boolean}
 */
export function validateHasSymbol(str) {
	return /[-!$£%^&*()_+|~=`{}\[\]:";'<>?,.\/]/.test(str);
}

/**
 * Check string has number
 * @param str
 * @returns {boolean}
 */
export function validateHasNumber(str) {
	return str.split('').some(ch => parseInt(ch));
}

/**
 * Check string is a valid email address
 * @param str
 * @returns {boolean}
 */
export function validateIsEmail(str) {

	/**
	 * General Email Regex (RFC 5322 Official Standard)
	 * http://emailregex.com/
	 */
	return /^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/.test(str);
}

/**
 * Configure module default value
 * @param opts
 */
export default opts => {
	config = opts ? Object.assign({}, config, opts) : config;
}
