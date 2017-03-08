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
        'jquery-3.1.1',
		'jasmine',
        //'jasmine-jquery'
    ],

    files: [
      testDir + '/**/*.js',
      testDir + '/**/*spec.js'
    ],

    exclude: [
		testDir + '/**/*e2e.js'
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
      'karma-jasmine',
      'karma-jquery',
      //'karma-jasmine-jquery'
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

    autoWatch:true,

    mochaReporter: {
      output: 'full'
    },

    colors: true,
    logLevel: config.LOG_INFO
  })
}
