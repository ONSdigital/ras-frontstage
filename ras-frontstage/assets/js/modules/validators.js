let config = {
		characterLen: {
			min: 8,
			max: Infinity
		}
	};


export function validateEqual(str1, str2) {
	return str1 === str2;
}

export function validateCharacterLength(str) {
	return str.length >= config.characterLen.min;
}

export function validateHasCapitalLetter(str) {
	return /[A-Z]/.test(str);
}

export function validateHasSymbol(str) {
	return /[-!$£%^&*()_+|~=`{}\[\]:";'<>?,.\/]/.test(str);
}

export function validateHasNumber(str) {
	return str.split('').some(function (ch) { return parseInt(ch) });
}

export function validateIsEmail(str) {

	/**
	 * General Email Regex (RFC 5322 Official Standard)
	 * http://emailregex.com/
	 */
	return /^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/.test(str);
}

export default opts => {
	config = opts ? Object.assign({}, config, opts) : config;
}
