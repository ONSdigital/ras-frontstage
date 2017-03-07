export const commonPath = './common/assets';
export const appPath = './ras-frontstage';
export const distPath = './ras-frontstage/static';

export const paths = {
	common: commonPath,
	styles: {
		dir: commonPath + '/styles/',
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
		rollupifyEntries: `${appPath}/assets/js/app/main.js`
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
