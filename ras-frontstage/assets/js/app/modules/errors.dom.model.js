'use strict';

export function userErrorModel(data) {

	if(!data.fields || !data.fields.length) {
		throw 'Invalid user error model from data ' + JSON.stringify(data) + '. At least one field needed.';
	}

	let model;

	model = {
		'fields': data.fields.map(fieldErrorModel)
	};

	data['page-title'] && data['page-link-message'] &&
		(model['page-title'] = 				opts['page-title'])
		(model['page-link-message'] = 		opts['page-link-message']);

	return model;

}

export function userErrorResetModel(data) {

	if(!data.fields || !data.fields.length) {
		throw 'Invalid user error reset model from data ' + JSON.stringify(data) + '. At least one field needed.';
	}

	return {
		'fields': data.fields
	};
}

export function fieldErrorModel(data) {

	if(!data.el) {
		throw 'Invalid field error model from data ' + JSON.stringify(data) + '. Field element needed.';
	}

	let model;

	model = {
		'el': data.el
	};

	data['messages'] && data['messages'].length &&
		(model['messages'] = data['messages']);

	return model;
}
