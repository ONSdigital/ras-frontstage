import { handleUserError, handleUserErrorReset } from './modules/errors.dom';
import { errorEmitter as passwordValidationErrorEmitter } from './modules/password-validation.dom';

passwordValidationErrorEmitter.on('user-error', (e, data) => handleUserError(data));
passwordValidationErrorEmitter.on('user-error:reset', (e, data) => handleUserErrorReset(data));
