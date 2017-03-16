'use strict';

import { setErrorEmitter } from './modules/errors.dom';
import { errorEmitter as passwordValidationErrorEmitter } from './modules/password-validation.dom';

setErrorEmitter(passwordValidationErrorEmitter);
