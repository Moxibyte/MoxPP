from conan import ConanFile

class MoxPPRecipe(ConanFile):
    settings = "os", "compiler", "build_type", "arch"
    generators = "PremakeDeps"

    def requirements(self):
        # You can add your own external requirements. Spdlog is provided as an example!
        self.requires("spdlog/1.13.0")

        # This is required for unit testing! Only remove it when not using unit tests!
        # You can also swap the testing framework. There is no hard reference to gtest in MoxPP!
        self.requires("gtest/1.15.0") 

    def configure(self):
        # This only works on windows (we added this so that you can see
        # how to change settings of packages)
        # self.options["spdlog"].wchar_support = True
        pass
