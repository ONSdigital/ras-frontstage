from tests.behavioural.features.browser import Browser


def before_scenario(context, scenario):
    if "ignore" in scenario.effective_tags:
        scenario.skip("Not Implemented")
        return


def before_all(context):
    context.browser = Browser()


def after_all(context):
    context.browser.close()
