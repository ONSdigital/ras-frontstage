export const commonPath = './common/assets';
export const appPath = './app';
export const distPath = './app/static';

export const paths = {
	common: commonPath,
	styles: {
		//dir: commonPath + '/styles/', // Local
		dir: '../sdc-global-design-patterns/assets/sass', // Using pattern library

		includePaths: [
			'../sdc-global-design-patterns/assets/sass',
			'../sdc-global-design-patterns/'
		],
		input: appPath + '/styles/**/{fixed,responsive}.scss',
		output: distPath + '/css/'
	},
	scripts: {
		dir: commonPath + '/js/',
		input: commonPath + '/js/**/*.js',
		output: distPath + '/js/',
		browserifyEntries: [
			`./${commonPath}/js/polyfills.js`,
			`${appPath}/assets/js/app/main.js`
		],
		rollupifyEntries: `${appPath}/assets/js/app/main.js`,
		docsSrc: [
			//'README.md',
			//`${commonPath}/js/**/*.js`,
			`${appPath}/assets/js/**/*.js`
		]
	},
	test: {
		input: appPath + '/js/**/*.js',
		karmaConf: './karma.conf.js',
		karmaSpec: appPath + '/assets/js/**/*.spec.js',
		//wdioConf: 'tests/functional/wdio.conf.js',
		wdioConf: 'tests/functional/wdio.conf.js',
		//wdioSpec: 'tests/functional/spec',
		coverage: 'tests/karma/coverage/',
		results: 'tests/karma/results/',
		errorShots: 'tests/errorShots'
	}
};
