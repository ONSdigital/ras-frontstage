let gulp = require('gulp'),
	sass = require('gulp-sass'),
	concat = require('gulp-concat');

gulp.task('sass', () => {

	return gulp.src('./ras-frontstage/main.sass')
		.pipe(sass({indentedSyntax: false}).on('error', sass.logError))
		.pipe(concat('site.min.css'))
		.pipe(gulp.dest('./ras-frontstage/static'));

});

gulp.task('compile:sass', () => {

	return gulp.src('./ras-frontstage/main.sass')
		.pipe(sass({indentedSyntax: false}).on('error', sass.logError))
		.pipe(concat('site.min.css'))
		.pipe(gulp.dest('./ras-frontstage/static'));

});

gulp.task('watch:compile:sass', ['compile:sass'], () => {
	gulp.watch('./ras-frontstage/**/*.scss', ['compile:sass']);
});

gulp.task('dev', [
	'watch:compile:sass'
], () => {

});

gulp.task('default', ['sass']);
