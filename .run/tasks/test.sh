# vim: set ft=bash sw=3 ts=3 expandtab:
# runscript: customized=true

# Limnoria has a custom type of test suite that needs to be run in a special
# way, which makes this awkward. We need to run both types of tests and also
# add the -a option when doing coverage for the normal test suite, so coverage
# data is merged.  So, this basically duplicates the implementation in the
# standard "run_command pytest" implementation.

help_test() {
   echo "- run test: Run the unit tests"
   echo "- run test -c: Run the unit tests with coverage"
   echo "- run test -ch: Run the unit tests with coverage and open the HTML report"
}

task_test() {
   coverage="no"
   html="no"

   while getopts ":ch" option; do
     case $option in
       c)
         coverage="yes"
         ;;
       h)
         html="yes"
         ;;
       ?)
         echo "invalid option -$OPTARG"
         exit 1
         ;;
     esac
   done

   color=""
   if [ "$GITHUB_ACTIONS" == "true" ] && [ "$RUNNER_OS" == "Windows" ]; then
      color="--color no"  # color messes up the terminal on Windows in GHA
   fi

   if [ $coverage == "yes" ]; then
      run_command uvrun coverage run "$(run_command uvrun which supybot-test)" --clean --plugins-dir=src HcoopMeetbot
      RESULT=$?
      rm -rf logs web tmp backup test-data test-conf  # supybot-test leaves around a lot of junk
      if [ $RESULT != 0 ]; then
         exit 1
      fi

      run_command uvrun coverage run -a -m pytest --testdox --force-testdox $color src/tests  # note -a to append data

      run_command uvrun coverage report
      run_command uvrun coverage lcov -o .coverage.lcov
      if [ $html == "yes" ]; then
         run_command uvrun coverage html -d .htmlcov
         run_command openfile .htmlcov/index.html
      fi
   else
      run_command uvrun run supybot-test --clean --plugins-dir=src HcoopMeetbot
      RESULT=$?
      rm -rf logs web tmp backup test-data test-conf  # supybot-test leaves around a lot of junk
      if [ $RESULT != 0 ]; then
         exit 1
      fi

      run_command uvrun pytest --testdox --force-testdox $color src/tests
   fi
}
