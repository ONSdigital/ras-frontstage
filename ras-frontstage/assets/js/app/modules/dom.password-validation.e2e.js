describe('password validation [DOM module]', () => {

	/*it('Should work', () => {
		expect(true).toBe(false);
	});*/

	it('should do some assertions', function() {
		browser.url('http://webdriver.io');
		expect(browser.getTitle()).toBe('WebdriverIO - Selenium 2.0 javascript bindings for nodejs');
	});

});
