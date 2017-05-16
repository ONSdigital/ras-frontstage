describe('password validation', () => {

	it('should do some assertions', function() {
		browser.url('http://localhost:5001/reset-password');
		expect(browser.getTitle()).toBe('Reset password');
	});

});
