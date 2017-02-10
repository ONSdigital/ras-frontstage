import gulp from 'gulp';
import {styles, lint as lintStyles} from './common/gulp/styles';
import {bundle} from './common/gulp/scripts';
import {paths} from './gulp/paths';

let sass = require('gulp-sass'),
	concat = require('gulp-concat');


/**
 * Compile common tasks
 */
gulp.task('compile:common:styles', () => {
	return styles(paths);
});

gulp.task('compile:common:scripts', () => {
	return bundle(true, paths);
});

gulp.task('watch:common:styles', ['compile:common:styles'], () => {
	gulp.watch(['./common/assets/styles/**/*.scss'], ['compile:common:styles']);
});

gulp.task('watch:common:scripts', ['compile:common:scripts'], () => {
	gulp.watch(['./common/assets/scripts/**/*.js'], ['compile:common:scripts']);
});



/**
 * App specific tasks
 */
gulp.task('compile:sass', () => {

	return gulp.src('./ras-frontstage/main.scss')
		.pipe(sass({indentedSyntax: false}).on('error', sass.logError))
		.pipe(concat('site.min.css'))
		.pipe(gulp.dest('./ras-frontstage/static'));

});

gulp.task('watch:sass', ['compile:sass'], () => {
	gulp.watch(['./ras-frontstage/**/*.scss'], ['compile:sass']);
});

gulp.task('dev', [
	'watch:common:styles',
	'watch:common:scripts',
	'watch:sass'
], () => {

});

gulp.task('default', ['sass']);
