let config = {
		characterLen: {
			min: 8,
			max: Infinity
		}
	};


export function validateEqual(str1, str2) {
	console.log(str1, str2);
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

export default opts => {
	config = opts ? Object.assign({}, config, opts) : config;
}
