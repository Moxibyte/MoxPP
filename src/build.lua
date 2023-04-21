-- This line starts a new project it needs to be the first line 
-- Arguments
-- 1) Name of the project used in the visual studio solution
-- 2) Output name of the project (name of the exe / lib)
mox_project("HelloWorld", "hello_world")

-- This line selects the programming language 
-- Options
-- A) mox_c()
-- B) mox_cpp(cppstd)
--    cppstd: C++ Version (optional, default to C++20)
-- C) mox_cs(dotnet)
--    notnet: .NET Framework version (optional, default to 4.6)
mox_cpp("C++20")

-- This line select the type of output
-- Options
-- A) mox_console()
--    Default console application
-- B) mox_windowed()
--    Windowd application without console (Windows only)
-- C) mox_sharedlib()
--    Shared library (.dll / .so)
-- D) mox_staticlib()
--    Static library
mox_console()

-- Further setup:
-- Now you can all the premake5 setting you like
-- https://premake.github.io/docs

-- Use the following to add linking to other projects
-- links { "ProjectName", "ProjectName2", ... }

-- Use the following to build after other projects
-- dependson { "ProjectName", "ProjectName2", ... }
