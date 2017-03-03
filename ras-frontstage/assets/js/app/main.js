import 'babel-polyfill';
import domready from '../../../../common/assets/js/app/modules/domready';

import '../../../../common/assets/js/app/modules/details-toggle';
import '../../../../common/assets/js/app/modules/inpagelink';
import '../../../../common/assets/js/app/modules/focus-styles';

import {
	default as passwordValidation,
	errorEmitter as passwordValidationErrorEmitter
} from './app.password-validation';

/**
 * Boot DOM
 */
domready(passwordValidation);

passwordValidationErrorEmitter.on('error', (data) => {
	console.log(data);
});
