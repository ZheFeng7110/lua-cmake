# lua-cmake    https://github.com/ZheFeng7110/lua-cmake
#
# Providing `CMakeLists.txt` for CMake users to build Lua. You can copy
# this file to the source of Lua, then use it as a CMake based project.
#
# This file is used to test Lua. You should put it into `test` directory.
# (Because the parent CMakeLists.txt usage `add_subdirectory(test)`).

cmake_minimum_required(VERSION 3.28...4.0.2)

project(lua_test C)

option(LUA_TESTS_RUN_COMPLETE_TESTS
    "Enabled to run Complete tests(see https://www.lua.org/tests/#complete). \
Or disabled to run Basic tests(see https://www.lua.org/tests/#basic)."
    OFF
)
option(LUA_TESTS_RUN_INTERNAL_TESTS
    "Enabled to run Internal tests(see https://www.lua.org/tests/#internal)."
    OFF
)

if (LUA_TESTS_RUN_INTERNAL_TESTS)
    target_sources(lua_core PRIVATE "${LUA_SOURCE_DIRECTORY}/ltests.c")
    target_compile_definitions(lua_core PUBLIC LUA_USER_H=\"ltests.h\")
endif ()

if (NOT (DEFINED luaInterpreterBuiltExecutable))
    message(FATAL_ERROR "luaInterpreterBuiltExecutable is not defined. Please set it "
        "to the path of the built Lua interpreter executable."
    )
endif ()

if (LUA_TESTS_RUN_COMPLETE_TESTS)
    set(luaTestsNotInternalTestCTestName "lua_complete_tests")
    set(luaTestsBasicTestCommandArgs "")
else ()
    set(luaTestsNotInternalTestCTestName "lua_basic_tests")
    set(luaTestsBasicTestCommandArgs "-e_U=true")
endif ()

add_test(
    NAME ${luaTestsNotInternalTestCTestName}
    COMMAND ${luaInterpreterBuiltExecutable} ${luaTestsBasicTestCommandArgs} all.lua
    WORKING_DIRECTORY "${LUA_SOURCE_DIRECTORY}/test"
)
