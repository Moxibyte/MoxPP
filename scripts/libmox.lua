-- Lua utils for MoxPP
--
-- Copyright (c) 2026 Moxibyte GmbH
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
        return "%{wks.location}/mox.bat " .. command
    else
        return "%{wks.location}/mox.sh " .. command
    end
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
        characterset "Unicode"

        targetdir ("%{wks.location}/build/" .. _OPTIONS["mox_premake_arch"] .. "-%{cfg.buildcfg}/bin/")
        objdir    ("%{wks.location}/build/" .. _OPTIONS["mox_premake_arch"] .. "-%{cfg.buildcfg}/obj/%{prj.name}/")

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
            cmox_macro_prefix .. "WORKSPACE_ROOT=\"" .. path.getabsolute(_WORKING_DIR) .. "\"",
            cmox_macro_prefix .. "PROJECT_ROOT=\"" .. path.getabsolute("./") .. "\"",
        }

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
                    if hmox_conan_release_only then
                        runtime "Release"
                    else
                        runtime "Debug"
                    end
                else
                    defines {
                        "NDEBUG",
                        cmox_macro_prefix .. "NDEBUG",
                    }
                    optimize "On"
                    runtime "Release"
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
        filter { "system:macosx" }
            defines {
                cmox_macro_prefix .. "OS_MACOS",
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
        filter { "architecture:universal" }
            defines {
                cmox_macro_prefix .. "ARCH_UNIVERSAL",
                cmox_macro_prefix .. "ARCH_TYPE_APPLESILICON",
                cmox_macro_prefix .. "BIT_64",
            }
        filter {}

        -- Post-build (always wired for every configuration; postbuild.py decides what to do)
        for idx,conf in pairs(cmox_configurations_n) do
            local is_debug = cmox_configurations_d[idx]
            -- When conan is release-only, debug configs still consume Release DLLs
            local effective_debug = is_debug and not hmox_conan_release_only
            filter { "configurations:" .. conf }
                mox_runpy_postbuild(effective_debug)
                mox_runpy_prebuild(effective_debug)
            filter {}
        end

        -- Windows options
        if mox_is_windows() then
            filter { "system:Windows" }
                -- Ignore linker warning on windows
                linkoptions { 
                    "/IGNORE:4099",
                }
                -- UTF8 build
                buildoptions {
                    "/utf-8",
                }
            filter {}
        end

        -- Non-Windows options
        if not mox_is_windows() then
            filter { "system:macosx" }
                -- dylib location (note: work not when creating app/dmg packages)
                linkoptions {
                    "-Wl,-rpath,@executable_path",
                }
            filter {}
            
            filter { "system: not windows and not macosx" }
                -- GCC Prefix
                gccprefix (_OPTIONS["mox_gcc_prefix"])
                -- so searching
                linkoptions {
                    "-Wl,--disable-new-dtags",
                    "-Wl,-rpath,'$$ORIGIN'",
                }
            filter {}
        end

        -- Fast compile
        multiprocessorcompile "On"

        -- Custom project configuration
        if cmox_function_setupproject~=nil then
            cmox_function_setupproject()
        end

end
function mox_c()
    language "C"

    mox_add_conan_building()
    for idx,conf in pairs(cmox_configurations_n) do
        local is_debug = cmox_configurations_d[idx]     
        moxpp_dependencies_build(conf, is_debug)
    end
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
    for idx,conf in pairs(cmox_configurations_n) do
        local is_debug = cmox_configurations_d[idx]     
        moxpp_dependencies_build(conf, is_debug)
    end
end
function mox_console()
    kind "ConsoleApp"
    defines {
        cmox_macro_prefix .. "APP",
        cmox_macro_prefix .. "CONSOLE",
    }
    linkgroups "On"
    mox_add_conan_linking()
    for idx,conf in pairs(cmox_configurations_n) do
        local is_debug = cmox_configurations_d[idx]     
        moxpp_dependencies_link(conf, is_debug)
    end
end
function mox_windowed()
    kind "WindowedApp"
    defines {
        cmox_macro_prefix .. "APP",
        cmox_macro_prefix .. "WINDOWED",
    }
    linkgroups "On"
    mox_add_conan_linking()
    for idx,conf in pairs(cmox_configurations_n) do
        local is_debug = cmox_configurations_d[idx]     
        moxpp_dependencies_link(conf, is_debug)
    end
end
function mox_sharedlib()
    kind "SharedLib"
    defines {
        cmox_macro_prefix .. "LIB",
        cmox_macro_prefix .. "LIB_SHARED",
    }
    linkgroups "On"
    mox_add_conan_linking()
    for idx,conf in pairs(cmox_configurations_n) do
        local is_debug = cmox_configurations_d[idx]     
        moxpp_dependencies_link(conf, is_debug)
    end
end
function mox_staticlib()
    kind "StaticLib"
    defines {
        cmox_macro_prefix .. "LIB",
        cmox_macro_prefix .. "LIB_STATIC",
    }
end
function mox_utility()
    kind "Utility"
end
function mox_none()
    kind "None"
end

-- Unit testing interface
function mox_setup_test()
    group("auxiliary")
    mox_project("unittest")
    mox_cpp()
    mox_console()
    links(hmox_test_requirements)
end
function mox_test_requirement()
    table.insert(hmox_test_requirements, hmox_project_name)
end

-- Internal functions
-- path.translate(..., "/") ensures forward-slash separators so a trailing slash never
-- produces the cmd.exe \" escaping bug (e.g. "C:\path\" eats the closing quote).
function mox_runpy_postbuild(is_debug)
    local flag = is_debug and "true" or "false"
    postbuildcommands {
        mox_cli_mox_command(
            'postbuild --project_name "%{prj.name}" --project_path "%{path.translate(prj.location, "/")}" --output_path "%{path.translate(cfg.targetdir, "/")}" --project_configuration "%{cfg.buildcfg}" --is_debug ' .. flag .. ' --project_architecture "%{cfg.architecture}" --project_kind "%{cfg.kind}"'
        )
    }
end
function mox_runpy_prebuild(is_debug)
    local flag = is_debug and "true" or "false"
    prebuildcommands {
        mox_cli_mox_command(
            'prebuild --project_name "%{prj.name}" --project_path "%{path.translate(prj.location, "/")}" --output_path "%{path.translate(cfg.targetdir, "/")}" --project_configuration "%{cfg.buildcfg}" --is_debug ' .. flag .. ' --project_architecture "%{cfg.architecture}" --project_kind "%{cfg.kind}"'
        )
    }
end
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
            if is_debug and not hmox_conan_release_only then
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
