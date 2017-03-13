import 'babel-polyfill';
import domready from '../../../../common/assets/js/app/modules/domready';

import '../../../../common/assets/js/app/modules/details-toggle';
import '../../../../common/assets/js/app/modules/inpagelink';
import '../../../../common/assets/js/app/modules/focus-styles';

import { default as errors } from './modules/errors.dom';
import { default as passwordValidation } from './modules/password-validation.dom';


/**
 * Application specific setup
 */
import './app.errors';


/**
 * Boot DOM
 */
domready(passwordValidation);
domready(errors);
