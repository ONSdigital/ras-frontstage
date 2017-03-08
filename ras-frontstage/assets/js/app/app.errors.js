import { setErrorEmitter } from './modules/error-messages.dom';
import { errorEmitter as passwordValidationErrorEmitter } from './modules/password-validation.dom';

setErrorEmitter(passwordValidationErrorEmitter);
