-- Lua utils for MoxPP
--
-- Copyright (c) 2025 Moxibyte GmbH
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


-- Internal functions
function mox_is_windows()
    ds = package.config:sub(1,1)
    return ds == "\\"
end
function mox_discover_subfolders(folder)
    if mox_is_windows() then
        return mox_discover_subfolders_win(folder)
    else
        return mox_discover_subfolders_linux(folder)
    end
end
function mox_discover_subfolders_win(folder)
    return io.popen("dir \"" .. folder .. "\" /b /ad"):lines()
end
function mox_discover_subfolders_linux(folder)
    return io.popen("find \"./" .. folder .. "\" -maxdepth 1 -type d -printf '%f\n'" ):lines()
end
function mox_cli_mox_command(command)
    if mox_is_windows() then
        return "python %{wks.location}/scripts/mox.py " .. command
    else
        return "python3 %{wks.location}/scripts/mox.py " .. command
    end
end

-- For you usable helpers
function mox_runpy_postbuild(command)
    postbuildcommands {
        mox_cli_mox_command(command)
    }
end
function mox_runpy_prebuild(command)
    prebuildcommands {
        mox_cli_mox_command(command)
    }
end

-- For you usable functions
function mox_project(name, output_name)
    hmox_project_name = name

    if output_name==nil then
        output_name = name
    end

    project(name)
        location "./"
        targetname(output_name)
        targetsuffix ""

        targetdir "%{wks.location}/build/%{cfg.architecture}-%{cfg.buildcfg}/bin/"
        objdir    "%{wks.location}/build/%{cfg.architecture}-%{cfg.buildcfg}/obj/%{prj.name}/"

        debugdir  "%{wks.location}/app"

        files {
            "%{prj.location}/**.lua",
            "%{prj.location}/**.txt", "%{prj.location}/**.md",
            "%{prj.location}/**.json", "%{prj.location}/**.jsonc", "%{prj.location}/**.xml",
            "%{prj.location}/**.c", "%{prj.location}/**.cc", "%{prj.location}/**.cpp", "%{prj.location}/**.cxx",
            "%{prj.location}/**.h", "%{prj.location}/**.hh", "%{prj.location}/**.hpp", "%{prj.location}/**.hxx"
        }

        includedirs {
            "%{prj.location}",
            "%{wks.location}",
            "%{wks.location}/" .. cmox_src_folder,
        }

        defines {
            cmox_macro_prefix .. "VERSION=\"" .. _OPTIONS["mox_version"] .. "\"",
        }

        -- GCC Prefix
        if mox_is_windows() then
            filter { "system:not Windows" }
                gccprefix (_OPTIONS["mox_gcc_prefix"])
            filter {}
        end

        -- Debug / Release
        for idx,conf in pairs(cmox_configurations_n) do
            local is_debug = cmox_configurations_d[idx]
            filter { "configurations:" .. conf }
                defines {
                    cmox_macro_prefix .. conf:upper()
                }
                if is_debug then
                    defines {
                        "DEBUG",
                        cmox_macro_prefix .. "DEBUG",
                    }
                    symbols "On"
                else
                    defines {
                        "NDEBUG",
                        cmox_macro_prefix .. "NDEBUG",
                    }
                    optimize "On"
                end
            filter {}
        end

        -- Define: OS
        filter { "system:windows" }
            defines {
                cmox_macro_prefix .. "OS_WINDOWS",
                "WINVER=0x0A00",
                "_WIN32_WINNT=0x0A00",
            }
        filter {}
        filter { "system:unix or linux" }
            defines {
                cmox_macro_prefix .. "OS_LINUX",
            }
        filter {}

        -- Define: Architecture
        filter { "architecture:x86" }
            defines {
                cmox_macro_prefix .. "ARCH_X86",
                cmox_macro_prefix .. "ARCH_TYPE_X86",
                cmox_macro_prefix .. "BIT_32",
            }
        filter {}
        filter { "architecture:x86_64" }
            defines {
                cmox_macro_prefix .. "ARCH_X86_64",
                cmox_macro_prefix .. "ARCH_TYPE_X86",
                cmox_macro_prefix .. "BIT_64",
            }
        filter {}
        filter { "architecture:ARM" }
            defines {
                cmox_macro_prefix .. "ARCH_ARM",
                cmox_macro_prefix .. "ARCH_TYPE_ARM",
                cmox_macro_prefix .. "BIT_32",
            }
        filter {}
        filter { "architecture:ARM64" }
            defines {
                cmox_macro_prefix .. "ARCH_ARM64",
                cmox_macro_prefix .. "ARCH_TYPE_ARM",
                cmox_macro_prefix .. "BIT_64",
            }
        filter {}

        -- DLL Distribution
        if cmox_copy_dlls then
            for idx,conf in pairs(cmox_configurations_n) do
                local is_debug = cmox_configurations_d[idx]

                filter { "configurations:" .. conf, "kind:ConsoleApp or WindowedApp" }
                    if is_debug then
                        mox_runpy_postbuild("distdlls %{wks.location}/dlls/Debug-%{cfg.architecture} %{cfg.targetdir}")
                    else
                        mox_runpy_postbuild("distdlls %{wks.location}/dlls/Release-%{cfg.architecture} %{cfg.targetdir}")
                    end
                filter {}
            end
        end

        -- Ignore linker warning on windows
        if mox_is_windows() then
            linkoptions { "/IGNORE:4099" }
        end

        -- Custom project configuration
        if cmox_function_setupproject~=nil then
            cmox_function_setupproject()
        end

end
function mox_c()
    language "C"

    mox_add_conan_building()
end
function mox_cs(dotnet)
    if dotnet==nil then
        dotnet = "4.6"
    end

    language "C#"
    dotnetframework(dotnet)
end
function mox_cpp(cppstd)
    language "C++"
    cppdialect(cmox_cpp_version)

    mox_add_conan_building()
end
function mox_console()
    kind "ConsoleApp"
    defines {
        cmox_macro_prefix .. "APP",
        cmox_macro_prefix .. "CONSOLE",
    }
    linkgroups "On"
    mox_add_conan_linking()
end
function mox_windowed()
    kind "WindowedApp"
    defines {
        cmox_macro_prefix .. "APP",
        cmox_macro_prefix .. "WINDOWED",
    }
    linkgroups "On"
    mox_add_conan_linking()
end
function mox_sharedlib()
    kind "SharedLib"
    defines {
        cmox_macro_prefix .. "LIB",
        cmox_macro_prefix .. "LIB_SHARED",
    }
    linkgroups "On"
    mox_add_conan_linking()
end
function mox_staticlib()
    kind "StaticLib"
    defines {
        cmox_macro_prefix .. "LIB",
        cmox_macro_prefix .. "LIB_STATIC",
    }
end
function mox_none()
    kind "None"
end

-- Unit testing interface
function mox_setup_test()
    group("")
    mox_project("unittest")
    mox_cpp()
    mox_console()
    links(hmox_test_requirements)
end
function mox_test_requirement()
    table.insert(hmox_test_requirements, hmox_project_name)
end


-- Internal functions
function mox_add_conan_linking_step(conf)
    conan_setup_link(conf)
end
function mox_add_conan_building_step(conf)
    conan_setup_build(conf)
end
function mox_add_conan_itterate(func)
    for idx,conf in pairs(cmox_configurations_n) do
        local is_debug = cmox_configurations_d[idx]
        filter { "configurations:" .. conf }
            if is_debug then
                func("debug_" .. _OPTIONS["mox_premake_arch"]:lower())
            else
                func("release_" .. _OPTIONS["mox_premake_arch"]:lower())
            end
        filter {}
    end
end
function mox_add_conan_linking()
    mox_add_conan_itterate(mox_add_conan_linking_step)
end
function mox_add_conan_building()
    mox_add_conan_itterate(mox_add_conan_building_step)
end
