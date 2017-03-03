module.exports = function(config) {
  var testDir = 'ras-frontstage/assets/js';

  config.set({

    basePath: './',

    client: {
      mocha: {
        timeout: 4000
      }
    },

    frameworks: [
        //'commonjs',
        'browserify',
		'jasmine',
    ],

    files: [
      testDir + '/**/*.js',
      testDir + '/**/*spec.js'
    ],

    preprocessors: {
      [testDir + '/**/*.js']: [
        //'commonjs',
        'browserify'
      ],
      [testDir+ '/**/*spec.js']: [
		'browserify'
      ]
      /*'**!/!*.js': [
		  //'commonjs',
          'coverage'
      ]*/
    },

    plugins: [
      'karma-browserify',
      'karma-mocha-reporter',
      'karma-chrome-launcher',
      'karma-phantomjs-launcher',
      'karma-coverage',
      'karma-jasmine'
    ],

    browserify: {
      debug: true,
      //transform: ['babelify'],
      transform: [
        [
          "babelify",
          {
            "presets": ["es2015", "stage-2"],
            "sourceMaps": false
          }
        ]
      ],
      paths: [
          './node_modules',
          './ras-frontstage/assets/js/'
      ]
    },

    reporters: [
		'progress',
		'coverage',
        'mocha'
    ],

    browsers: ['PhantomJS'],

    coverageReporter: {
      dir : 'coverage/',
      reporters: [
        { type: 'html', subdir: 'html' },
        { type: 'lcovonly', subdir: 'lcov' },
        { type: 'cobertura', subdir: 'cobertura' }
      ]
    },


    mochaReporter: {
      output: 'full'
    },

    colors: true,
    logLevel: config.LOG_INFO
  })
}
