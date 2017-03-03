import gulp from 'gulp';
import { default as stylesModule, styles, lint as lintStyles } from './common/gulp/styles';
import { default as scriptsModule, bundle, copyScripts } from './common/gulp/scripts';
import { paths, appPath } from './gulp/paths';
import sass from 'gulp-sass';
import concat from 'gulp-concat';
import { default as testsModule, unitTests, functionalTests } from './common/gulp/tests'

const config = {
	paths: paths
};

scriptsModule(config);
stylesModule(config);
testsModule(config);


/**
 * Compile common tasks
 */
gulp.task('compile:common:styles', () => {
	return styles();
});

gulp.task('compile:common:scripts', () => {
	return bundle(false);
});

gulp.task('watch:common:styles', ['compile:common:styles'], () => {
	gulp.watch(['./common/assets/styles/**/*.scss'], ['compile:common:styles']);
});

gulp.task('watch:common:scripts', ['compile:common:scripts'], () => {
	gulp.watch([paths.scripts.input, `${appPath}/assets/js/**/*.js`], ['compile:common:scripts']);
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


/**
 * Test
 */
gulp.task('test:scripts:unit', (done) => {
	unitTests(done, false)
});

/*gulp.task('test:scripts:functional:sauce', (done) => {
	process.env.BASEURL = getEnv()
	functionalTests(done)
});*/

gulp.task('test:scripts', ['test:scripts:unit'])



/**
 * Tools
 */
gulp.task('dev', [
	'watch:common:styles',
	'watch:common:scripts',
	'watch:sass'
]);

gulp.task('test', [
	'test:scripts'
])

gulp.task('default', ['sass']);
