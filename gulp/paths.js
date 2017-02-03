export const commonPath = './common/assets';
export const appPath = './ras-frontstage';
export const distPath = './ras-frontstage/static';

export const paths = {
	styles: {
		dir: commonPath + '/styles/',
		input: appPath + '/styles/**/{fixed,responsive}.scss',
		output: distPath + '/css/'
	}
};

/*export const paths = {
	app: appPath,
	input: appPath + '/!**!/!*',
	output: distPath,
	scripts: {
		dir: appPath + '/js/',
		input: appPath + '/js/!**!/!*.js',
		output: distPath + '/js/'
	},
	styles: {
		dir: appPath + '/styles/',
		input: appPath + '/styles/!**!/{fixed,responsive}.scss',
		input_all: appPath + '/styles/!**!/!*.scss',
		output: distPath + '/css/'
	},
	templates: {
		dir: appPath + '/templates/',
		input: [homePath + '/templates/!**!/!*.html', homePath + '/themes/!**!/!*.html']
	},
	svgs: {
		dir: appPath + '/img/',
		input: appPath + '/img/!**!/!*.svg',
		output: distPath + '/img/'
	},
	images: {
		input: appPath + '/img/!**.{svg,png,jpg,jpeg,gif,ico}',
		output: distPath + '/img/'
	},
	fonts: {
		input: appPath + '/fonts/!**!/!*.{ttf,woff,woff2}',
		output: distPath + '/fonts/'
	},
	webfonts: {
		input: appPath + '/webfonts/!**.{svg,woff,woff2,eot,ttf}',
		output: distPath + '/webfonts/'
	},
	test: {
		input: appPath + '/js/!**!/!*.js',
		karmaConf: 'tests/karma/karma.conf.js',
		karmaSpec: 'tests/karma/spec/!**!/!*.js',
		wdioConf: 'tests/functional/wdio.conf.js',
		wdioSpec: 'tests/functional/spec',
		coverage: 'tests/karma/coverage/',
		results: 'tests/karma/results/',
		errorShots: 'tests/errorShots'
	}
}*/
