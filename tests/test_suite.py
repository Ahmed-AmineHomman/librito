"""Empty unittest discovery target."""


def load_tests(loader, standard_tests, pattern):
    return loader.suiteClass()
