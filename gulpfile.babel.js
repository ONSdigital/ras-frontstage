import gulp from 'gulp';
import { paths, appPath, distPath } from './gulp/paths';
import sass from 'gulp-sass';
import concat from 'gulp-concat';
import webdriver from 'gulp-webdriver';

import { default as stylesModule, styles, lint as lintStyles } from './common/gulp/styles';
import { default as scriptsModule, bundle, copyScripts } from './common/gulp/scripts';
import { default as scriptsDocsModule, docs } from './gulp/scripts.doc';
import { default as testsModule, unitTests, functionalTests } from './common/gulp/tests';

const config = {
	paths: paths
};

scriptsModule(config);
scriptsDocsModule(config);
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

gulp.task('compile:common:scripts:docs', () => {
	return docs();
});


gulp.task('watch:common:styles', ['compile:common:styles'], () => {
	gulp.watch([
		`${appPath}/assets/styles/**/*.scss`,
		'../sdc-global-design-patterns/**/*.scss'
	], ['compile:common:styles']);
});

gulp.task('watch:common:scripts', ['compile:common:scripts'], () => {
	gulp.watch([paths.scripts.input, `${appPath}/assets/js/**/*.js`], ['compile:common:scripts']);
});

gulp.task('watch:common:scripts:doc', ['compile:common:scripts:docs'], () => {
	gulp.watch(paths.scripts.docsSrc, ['compile:common:scripts:docs']);
});


/**
 * App specific tasks
 */
gulp.task('compile:sass', () => {
	return gulp.src(`${appPath}/main.scss`)
		.pipe(sass({indentedSyntax: false}).on('error', sass.logError))
		.pipe(concat('site.min.css'))
		.pipe(gulp.dest(`${distPath}`));
});

gulp.task('watch:sass', ['compile:sass'], () => {
	gulp.watch([`${appPath}/**/*.scss`], ['compile:sass', 'compile:common:styles']);
});


/**
 * Test
 */
gulp.task('test:scripts:unit', (done) => {
	return unitTests(done, false)
});

gulp.task('test:scripts:e2e', function() {
	return gulp.src('wdio.conf.js').pipe(webdriver());
});


/**
 * Gulp tasks
 */
 gulp.task('default', [
 	'compile:sass',
	'compile:common:styles',
	'compile:common:scripts',
	'compile:common:scripts:docs'
 ]);

gulp.task('dev', [
	'watch:common:styles',
	'watch:common:scripts',
	'watch:sass'
]);

gulp.task('test', [
	'test:scripts:unit',
	'test:scripts:e2e'
]);
