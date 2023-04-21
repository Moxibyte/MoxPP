from conan import ConanFile

class MoxPPRecipe(ConanFile):
    settings = "os", "compiler", "build_type", "arch"
    generators = "PremakeDeps"

    def requirements(self):
        self.requires("spdlog/1.11.0")

    # Does not work?! Try in future conan versions
    def configure(self):
        self.options["spdlog"].wchar_support = True
