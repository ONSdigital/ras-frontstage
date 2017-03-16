'use strict';

import { userErrorModel, userErrorResetModel } from './errors.dom.model';

let userErrors = [],

	inputTextErrorClass = 'input--text-error',
	fieldErrorLabelProperty = 'sdcFieldErrorLabel';


export function setErrorEmitter(emitter) {
	emitter.on('user-error', (e, data) => {
		handleUserError(userErrorModel(data))
	});
	emitter.on('user-error:reset', (e, data) => handleUserErrorReset(userErrorResetModel(data)));
}

function handleUserError(data) {

	if(data.fields && data.fields.length) {
		data.fields.forEach(fieldError);
	}

	userErrors.push(data);
}

function handleUserErrorReset(data) {

	if(data.fields && data.fields.length) {
		data.fields.forEach(fieldErrorReset);
	}

	userErrors.length = 0;
}

function fieldError(optsFieldErrObj) {

	/**
	 * A better way to do this?
	 */
	let fieldAlreadyErroring = userErrors.find(errObj => errObj.fields.find(fieldErrObj => fieldErrObj.el === optsFieldErrObj.el)),

		html = optsFieldErrObj.messages ? `<ul class="list list--bare list--errors">${optsFieldErrObj.messages.map(fieldErrorMessage).join('')}</ul>` : '';

	if(!fieldAlreadyErroring) {

		let $el = $(html);

		$(optsFieldErrObj.el).addClass(inputTextErrorClass);
		$el.insertBefore(optsFieldErrObj.el);
		optsFieldErrObj.el[fieldErrorLabelProperty] = $el[0];
	}
}

function fieldErrorMessage (message) {
	return `<li class="list__item pluto" data-error="true" data-error-msg="${message}">${message}</li>`;
}

function fieldErrorReset($field) {
	$field.removeClass(inputTextErrorClass);
	$($field[0][fieldErrorLabelProperty]).remove();
}
