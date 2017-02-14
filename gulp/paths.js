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
	}
};
