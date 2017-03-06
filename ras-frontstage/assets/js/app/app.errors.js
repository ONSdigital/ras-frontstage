import { setErrorEmitter } from './modules/dom.error-messages';
import { errorEmitter as passwordValidationErrorEmitter } from './modules/dom.password-validation';

setErrorEmitter(passwordValidationErrorEmitter);
