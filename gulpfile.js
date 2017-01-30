let gulp = require('gulp'),
	sass = require('gulp-sass'),
	concat = require('gulp-concat');


gulp.task('compile:sass:base', () => {

	return gulp.src('./ras-frontstage/ons-base.sass')
		.pipe(sass({indentedSyntax: false}).on('error', sass.logError))
		.pipe(concat('ons-base.min.css'))
		.pipe(gulp.dest('./ras-frontstage/static'));

});

gulp.task('compile:sass', () => {

	return gulp.src('./ras-frontstage/main.sass')
		.pipe(sass({indentedSyntax: false}).on('error', sass.logError))
		.pipe(concat('site.min.css'))
		.pipe(gulp.dest('./ras-frontstage/static'));

});

gulp.task('watch:compile:sass', ['compile:sass', 'compile:sass:base'], () => {
	gulp.watch(['./ras-frontstage/**/*.scss', './ras-frontstage/**/*.sass'], ['compile:sass', 'compile:sass:base']);
});

gulp.task('dev', [
	'watch:compile:sass'
], () => {

});

gulp.task('default', ['sass']);
