let options = {
		characterLen: {
			min: 8,
			max: Infinity
		}
	};

export function validateCharacterLength(str) {
	return false;
}

export function validateHasCapitalLetter(str) {
	return false;
}

export function validateHasSymbol(str) {
	return true;
}

export function validationHasNumber(str) {
	return false;
}

export default opts => {
	options = opts ? Object.assign({}, options, opts) : options;
}
