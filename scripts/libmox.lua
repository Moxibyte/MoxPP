-- Lua utils for MoxPP
-- 
-- Copyright (c) 2023 Moxibyte GmbH
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
  
        -- Defines
        filter { "system:windows" }
            defines {
                cmox_macro_prefix .. "OS_WINDOWS",
                "WINVER=0x0A00",
                "_WIN32_WINNT=0x0A00",
            }
        filter {}
        filter { "system:unix" }
            defines {
                cmox_macro_prefix .. "OS_LINUX",
            }
        filter {}

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
    if cppstd==nil then
        cppstd = "C++20"
    end
    
    language "C++"
    cppdialect(cppstd)

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
                func("debug_x86_64")
            else
                func("release_x86_64")
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
