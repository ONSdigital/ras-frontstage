/**
 * Error emitter list
 * @type {Array<Emitter>}
 */
let emitters = [],
	userErrors = [],

	inputTextErrorClass = 'input--text-error',
	fieldErrorLabelProperty = 'sdcFieldErrorLabel';

export default () => {

}

export function handleUserError(data) {

	if(data.fields && data.fields.length) {
		data.fields.forEach(fieldError);
	}

	userErrors.push(data);
}

export function handleUserErrorReset(data) {

	if(data.fields && data.fields.length) {
		data.fields.forEach(fieldErrorReset);
	}

	userErrors.length = 0;
}

function fieldError(optsFieldErrObj) {

	/*let existingFields = [];*/

	/**
	 * A better way to do this
	 */
	let fieldAlreadyErroring = userErrors.find(errObj => errObj.fields.find(fieldErrObj => fieldErrObj.el === optsFieldErrObj.el));

	var html = `
		<ul class="list list--bare list--errors">
			<li class="list__item pluto" data-error="true" data-error-msg="${optsFieldErrObj.message}">
				${optsFieldErrObj.message}
			</li>
		</ul>`;

	if(!fieldAlreadyErroring) {

		let $el = $(html);

		$(optsFieldErrObj.el).addClass(inputTextErrorClass);
		$el.insertBefore(optsFieldErrObj.el);
		optsFieldErrObj.el[fieldErrorLabelProperty] = $el[0];
	}
}

function fieldErrorReset($field) {
	$field.removeClass(inputTextErrorClass);
	$($field[0][fieldErrorLabelProperty]).remove();
}

/**
 * Accepting an error emitter type object
 * @param <Emitter>
 */
/*
export function setErrorEmitter(emitter) {
	emitters.push(emitter);
	emitter.on('user-error', (e, data) => handleUserError(data));
	emitter.on('user-error:reset', (e, data) => handleUserErrorReset(data));
}
*/
