let gulp = require('gulp'),
	sass = require('gulp-sass'),
	concat = require('gulp-concat');

gulp.task('sass', () => {

	return gulp.src('./ras-frontstage/main.sass')
		.pipe(sass().on('error', sass.logError))
		.pipe(concat('site.min.css'))
		.pipe(gulp.dest('./ras-frontstage/static'));

	/*return gulp.src('./ras-frontstage/templates/!**!/!*.scss')
		.pipe(sass().on('error', sass.logError))
		.pipe(gulp.dest('./dist'));*/

});

gulp.task('default', ['sass']);
