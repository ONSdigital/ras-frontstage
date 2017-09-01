from selenium import webdriver

from frontstage import app


class Browser(object):
    base_url = app.config['SELENIUM_TEST_URL']
    driver = webdriver.Chrome()
    driver.implicitly_wait(10)

    def close(self):
        """
        close the webdriver instance
        """
        self.driver.quit()

    def visit(self, location=''):
        """
        navigate webdriver to different pages
        """
        url = self.base_url + location
        self.driver.get(url)

    def find_by_id(self, selector):
        """
        find a page element in the DOM
        """
        return self.driver.find_element_by_id(selector)

    def find_by_name(self, selector):
        """
        find a page element in the DOM
        """
        return self.driver.find_element_by_name(selector)

    def find_by_link_text(self, selector):
        """
        find a page element in the DOM
        """
        return self.driver.find_element_by_link_text(selector)

    def find_by_path(self, selector):
        """
        find an element by path (not recommended)
        """
        return self.driver.find_element_by_xpath(selector)
