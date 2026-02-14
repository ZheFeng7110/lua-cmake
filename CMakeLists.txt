# lua-cmake    https://github.com/ZheFeng7110/lua-cmake
#
# Providing `CMakeLists.txt` for CMake users to build Lua. You can copy
# this file to the source of Lua, then use it as a CMake based project.
#
# If the source directory of Lua is not same to this `CMakeLists.txt` file,
# you should set variable "LUA_SOURCE_DIRECTORY" to specify the source directory of Lua.
#
# Embedding Lua in your project:
#     Please set `LUA_BUILD_COMPILER` and `LUA_BUILD_INTERPRETER` OFF,
#     then link lib `lua_core` and `lua_stdlib` to your project.
#     (e.g. target_link_libraries(your_project PUBLIC/PRIVATE/INTERFACE lua_core lua_stdlib))
#
# Building Lua interpreter or compiler:
#     Please set `LUA_BUILD_COMPILER` or `LUA_BUILD_INTERPRETER` ON.
#
# Running tests:
#     Please set `LUA_BUILD_INTERPRETER` and `LUA_ENABLE_TESTS` ON.
#
# Usage:
#     Configure: cmake -B build -D <...>
#     Build: cmake --build build
#     Test: cd build && ctest .

cmake_minimum_required(VERSION 3.28...4.0.2)

project(lua C)

set(LUA_USE_PLATFORM_FEATURES "" CACHE STRING
    "Choose suitable platform-specific features. Options are: \"POSIX\", \
\"MACOSX\", \"LINUX\" or empty for none."
)
option(LUA_32BITS "Enables Lua with 32-bit integers and 32-bit floats." OFF)

option(LUA_BUILD_SHARED_LIBRARY "Build lua_core and lua_stdlib as a shared library." OFF)
option(LUA_BUILD_INTERPRETER "Enabled to build Lua interpreter('lua' executable file)." ON)
option(LUA_BUILD_COMPILER "Enabled to build Lua compiler('luac' executable file)." ON)

option(LUA_ENABLE_TESTS "Enable building and running tests." OFF)

set(LUA_SOURCE_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}" CACHE PATH
    "The source directory of Lua. If the source directory of Lua is not same to \
this `CMakeLists.txt` file, you should set it."
)

block ()  # Target: lua_core
    set(subProjectName "lua_core")

    if (LUA_BUILD_SHARED_LIBRARY)
        add_library(${subProjectName} SHARED)

        if (MSVC)
            target_compile_definitions(${subProjectName} PUBLIC LUA_BUILD_AS_DLL)
        endif ()
    else ()
        add_library(${subProjectName} STATIC)
    endif ()

    set(srcFiles
        lzio.c lctype.c lopcodes.c lmem.c lundump.c ldump.c lstate.c
        lgc.c llex.c lcode.c lparser.c ldebug.c lfunc.c lobject.c ltm.c
        lstring.c ltable.c ldo.c lvm.c lapi.c

        lauxlib.c
    )
    list(TRANSFORM srcFiles PREPEND "${LUA_SOURCE_DIRECTORY}/")

    target_sources(${subProjectName} PRIVATE ${srcFiles})

    target_include_directories(${subProjectName} PUBLIC "${CMAKE_CURRENT_LIST_DIR}")

    string(TOUPPER "${LUA_USE_PLATFORM_FEATURES}" luaUsePlatformFeatures)
    if (luaUsePlatformFeatures STREQUAL "POSIX")
        target_compile_definitions(${subProjectName} PUBLIC LUA_USE_POSIX)
    elseif (luaUsePlatformFeatures STREQUAL "MACOSX")
        target_compile_definitions(${subProjectName} PUBLIC LUA_USE_MACOSX)
    elseif (luaUsePlatformFeatures STREQUAL "LINUX")
        target_compile_definitions(${subProjectName} PUBLIC LUA_USE_LINUX)
    elseif (NOT (luaUsePlatformFeatures STREQUAL ""))
        message(FATAL_ERROR "LUA_USE_PLATFORM_FEATURES must be either \"POSIX\", \
\"MACOSX\", \"LINUX\" or empty for none.")
    endif ()

    if (LUA_32BITS)
        target_compile_definitions(${subProjectName} PUBLIC LUA_32BITS)
    endif ()

    if (CMAKE_C_STANDARD LESS_EQUAL 89)
        target_compile_definitions(${subProjectName} PUBLIC LUA_USE_C89)
    endif ()

    if (UNIX AND NOT APPLE)
        target_link_libraries(${subProjectName} PRIVATE m)
    endif ()
endblock ()

block ()  # Target: lua_stdlib
    set(subProjectName "lua_stdlib")

    if (LUA_BUILD_SHARED_LIBRARY)
        add_library(${subProjectName} SHARED)
    else ()
        add_library(${subProjectName} STATIC)
    endif ()

    target_link_libraries(${subProjectName} PUBLIC lua_core)

    set(srcFiles
        lbaselib.c lcorolib.c ldblib.c liolib.c lmathlib.c loadlib.c
        loslib.c lstrlib.c ltablib.c lutf8lib.c linit.c
    )
    list(TRANSFORM srcFiles PREPEND "${LUA_SOURCE_DIRECTORY}/")

    target_sources(${subProjectName} PRIVATE ${srcFiles})

    if (UNIX AND NOT APPLE)
        target_link_libraries(${subProjectName} PRIVATE m)
    endif ()
endblock ()

# Target: lua
if (LUA_BUILD_INTERPRETER)
    add_executable(${PROJECT_NAME})

    target_sources(${PROJECT_NAME} PRIVATE "${LUA_SOURCE_DIRECTORY}/lua.c")
    target_link_libraries(${PROJECT_NAME} PRIVATE lua_core lua_stdlib)
endif ()

if (LUA_BUILD_COMPILER)
    if ((EXISTS "${LUA_SOURCE_DIRECTORY}/luac.c") AND
        (NOT (IS_DIRECTORY "${LUA_SOURCE_DIRECTORY}/luac.c"))
    )
        block ()  # Target: luac
            set(subProjectName "luac")

            add_executable(${subProjectName})
            target_sources(${subProjectName} PRIVATE "${LUA_SOURCE_DIRECTORY}/luac.c")
            target_link_libraries(${subProjectName} PRIVATE lua_core)
        endblock ()
    else ()
        message(WARNING "File \"${LUA_SOURCE_DIRECTORY}/luac.c\" does "
            "not exists, so will not build Lua compiler even \"LUA_BUILD_COMPILER\" ON."
        )
    endif ()
endif ()

if (LUA_ENABLE_TESTS)
    if (NOT (LUA_BUILD_INTERPRETER))
        message(FATAL_ERROR "To run tests of lua requires \"LUA_BUILD_INTERPRETER\" on.")
    endif ()

    enable_testing()

    get_target_property(luaExecutableDir ${PROJECT_NAME} BINARY_DIR)

    set(luaInterpreterBuiltExecutable "${luaExecutableDir}/${PROJECT_NAME}")
    add_subdirectory(test)
endif ()
