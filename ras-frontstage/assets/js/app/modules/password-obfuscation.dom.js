'use strict';

/**
 * Export classes for testing
 */
export const passwordObfuscationGroupClass = 'js-password-obfuscation-group',
	passwordObfuscationToggle = 'js-password-obfuscation-toggle',
	passwordObfuscationField = 'js-password-obfuscation-field';

export default () => {

	$(`.${passwordObfuscationGroupClass}`).each((i, el) => applyObfuscationToggle({ $scopeEl: $(el) }));

}

function applyObfuscationToggle(scope) {

	/**
	 * Scoped fields
	 */
	let $scopeEl = scope.$scopeEl,
		$toggle = $scopeEl.find(`.${passwordObfuscationToggle}`),
		$field = $scopeEl.find(`.${passwordObfuscationField}`);

	$toggle.on('click', () => {

		let currentType = $field.attr('type');

		$field.attr('type', (currentType === 'password' ? 'text' : 'password'));

	});
}
