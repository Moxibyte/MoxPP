-- Automatic setup of unittest
-- This function will execute the following lines of code:
--    group("")
--    mox_project("unittest")
--    mox_cpp()
--    mox_console()
--    links(hmox_test_requirements) 
--
-- You can modify building of the test in this file! This file is only "called" when tests are enabled!

mox_setup_test()
