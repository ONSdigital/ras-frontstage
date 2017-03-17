import gulp from 'gulp';
import jsdoc from 'gulp-jsdoc3';

let config = {};
export default opts => {
	config = opts ? Object.assign({}, config, opts) : config;
}

export function docs(cb) {
	return gulp.src(config.paths.scripts.docsSrc, {read: false})
		.pipe(jsdoc(cb));
}
