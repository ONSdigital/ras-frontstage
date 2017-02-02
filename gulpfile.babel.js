import gulp from 'gulp';
import {styles, lint as lintStyles} from './common/gulp/styles';
import {paths} from './gulp/paths';

let sass = require('gulp-sass'),
	concat = require('gulp-concat');


/**
 * Compile common tasks
 */
gulp.task('common:build:styles', () => {
	return styles(paths);
});

gulp.task('watch:common:build:styles', () => {
	gulp.watch(['./common/**/*.scss'], ['common:build:styles']);
	styles(paths);
});


gulp.task('compile:sass:base', () => {

	return gulp.src('./ras-frontstage/ons-base.scss')
		.pipe(sass({indentedSyntax: false}).on('error', sass.logError))
		.pipe(concat('ons-base.min.css'))
		.pipe(gulp.dest('./ras-frontstage/static'));

});

gulp.task('compile:sass', () => {

	return gulp.src('./ras-frontstage/main.scss')
		.pipe(sass({indentedSyntax: false}).on('error', sass.logError))
		.pipe(concat('site.min.css'))
		.pipe(gulp.dest('./ras-frontstage/static'));

});

gulp.task('watch:compile:sass', ['compile:sass', 'compile:sass:base'], () => {
	gulp.watch(['./ras-frontstage/**/*.scss'], ['compile:sass', 'compile:sass:base']);
});

gulp.task('dev', [
	'watch:common:build:styles',
	'watch:compile:sass'
], () => {

});

gulp.task('default', ['sass']);
