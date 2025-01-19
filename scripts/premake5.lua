-- premake5.lua root script
-- 
-- Copyright (c) 2025 Ludwig Füchsl
-- 
-- Permission is hereby granted, free of charge, to any person obtaining a copy
-- of this software and associated documentation files (the "Software"), to deal
-- in the Software without restriction, including without limitation the rights
-- to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
-- copies of the Software, and to permit persons to whom the Software is
-- furnished to do so, subject to the following conditions:
-- 
-- The above copyright notice and this permission notice shall be included in all
-- copies or substantial portions of the Software.
-- 
-- THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
-- IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
-- FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
-- AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
-- LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
-- OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
-- SOFTWARE.

include "libmox.lua"
include "../dependencies/conandeps.premake5.lua"
include "../mox.lua"

hmox_test_requirements = {}

newoption {
    trigger = "mox_premake_arch",
    value = "ARCH",
    description = "Defines the architecture to use for building the project (premake native)",
    category = "MoxPP",
    allowed = {
        { "x86", "32-Bit x86" },
        { "x86_64", "64-Bit x86" },
        { "ARM", "32-Bit ARM" },
        { "ARM64", "64-Bit ARM" },
    },
    default = "x86_64"
}
newoption {
    trigger = "mox_conan_arch",
    value = "ARCH",
    description = "Defines the architecture to use by the dependencies",
    category = "MoxPP",
    allowed = {
        { "x86", "32-Bit x86" },
        { "x86_64", "64-Bit x86" },
        { "armv7", "armv7 (32-Bit)" },
        { "armv8", "armv8 (64-Bit)" },
    },
    default = "x86_64"
}
newoption {
    trigger = "mox_version",
    value = "VERSION",
    description = "Set the version string injected as preprocessor macro",
    category = "MoxPP",
    default = "unknown"
}

workspace(cmox_product_name)
    -- Workspace configuration
    configurations(cmox_configurations_n)
    architecture(_OPTIONS["mox_premake_arch"])
    location "../"

    -- Custom workspace configuration
    if cmox_function_setupworkspace~=nil then
        cmox_function_setupworkspace()
    end

    -- Load projects
    if cmox_project_architecture == "single" then
        hmox_project_dir = "../" .. cmox_src_folder .. "/"
        include(hmox_project_dir .. "build.lua")
    elseif cmox_project_architecture == "flat" then
        for dir in mox_discover_subfolders("../" .. cmox_src_folder)
        do 
            hmox_project_dir = "../" .. cmox_src_folder .. "/" .. dir .. "/" 
            local buildFile = hmox_project_dir .. "build.lua" 
            if os.isfile(buildFile) then
                include(buildFile)
            end
        end
    elseif cmox_project_architecture == "hierarchical" then
        for dir in mox_discover_subfolders("../" .. cmox_src_folder)
        do 
            group(dir)
            for subdir in mox_discover_subfolders("../" .. cmox_src_folder .. "/" .. dir)
            do
                hmox_project_dir = "../" .. cmox_src_folder .. "/" .. dir .. "/" .. subdir .. "/"
                local buildFile =  hmox_project_dir .. "build.lua"
                if os.isfile(buildFile) then
                    include(buildFile)
                end
            end
        end
    elseif cmox_project_architecture == "manual" then
        cmox_function_includeprojects()
    end

    -- Unittest
    if cmox_unit_test_src ~= nil then
        include("../" .. cmox_unit_test_src .. "/build.lua")
    end 
