if __name__ == '__main__':
    from behave import __main__ as behave_executable
    behave_executable.main(None)

    def before_scenario(context, scenario):
        if "ignore" in scenario.effective_tags:
            scenario.skip("Unimplemented Functionality")
            return
