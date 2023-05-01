#include <chrono>
#include <ctime>
#include <fstream>
#include <iostream>
#include <json/json.h>

int someFunc() {
  std::cout << "someFunc called!" << endl;
  return 0;
}

int main(int argc, char* argv[]) {
  const double TIME_SHUTDOWN = 5; // find real shutdon and wakeup times later
  const double TIME_WAKEUP = 5;

  str filename = "ensembles.json";
  if (argc > 1) {
    filename = argv[1];
  }

  // set up istream and read current ensemble function data
  Json::Value ensembles;
  std::ifstream ensemble_ifile(filename, std::ifstream::binary);
  ensemble_ifile >> ensembles;

  // temporary, for testing while we work
  std::cout << ensembles << "\n";
  std::cout << ensembles["ensemble_list"][0] << "\n";

  // fetch current ensemble
  auto const next_ensemble = ensembles["next_ensemble"];
  std::vector<Callable> ensemble;
  if (next_ensemble == "") {
    /* Dylan
    TODO: find ensemble with earliest start time by comparing hour, then min,
    then sec to find earliest

    if next ensemble's time - curr_time is less than shutdown + wakeup time,
    write next_ensemble to file, then go to sleep
    */
  }
  else {
    for (auto e : ensembles["ensemble_list"]) {
      if (e["title"] == next_ensemble) {
        ensemble.append(e["function"]);
      }
    }
  }

  // perform ensemble functions
  for (auto f : ensemble) {
    std::invoke(f, inputs); // Wesley
    // TODO: allow for function arguments via e["inputs"]
    // should just be comma-separated list of inputs
  }

  /* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * */

  // Hannah
  // TODO: update each individual ensemble's next execution time IF IT WAS CALLED
  if (next_ensemble == "" ) { // might need to change this but the first ensemble executing
    add interval secs to value of start_time
  }
  else if (determine if intervals remain) {
    add interval secs to current value of next_time
  }
  else {
    set next_time to default (23:59:59 or just blank really)
  }

  // save next ensemble to disk
  /*
  TODO: replace next_ensemble with title of next-occurring ensemble
  (i.e., lowest hr/min/sec in next_time)
  Might want to make a function with "next_time"/"start_time" argument options
  to find lowest next/start time among all ensembles, since this is really the
  same as the line 34 TODO
  */
  ensembles["next_ensemble"] = "dummy2"; // replace dummy2 obviously

  Json::StyledWriter styledWriter;
  Json::FastWriter fastWriter;
  std::ofstream ensemble_ofile(filename, std::ifstream::binary);
  ofstream << styledWriter.write(ensembles) << std::endl;
  ofstream << fastWriter.write(ensembles) << std::endl;

  /* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * */

  // calculations
  auto curr_time = std::chrono::system_clock::now();
  auto next_time = std::chrono::system_clock::now(); // TODO: change this to clocktime of next ensemble
  std::chrono::duration<double> sleep_time = next_time - curr_time - TIME_SHUTDOWN - TIME_WAKEUP;
  if (sleep_time <= 0) {
    // not enough time to go into sleep and wake up again before next ensemble
    sleep(sleep_time); // C++ sleep function, not sleep timer
  }
  std::time_t end_time = std::chrono::system_clock::to_time_t(next_time); // idk what this is
  std::cout << "sleep time: " << sleep_time.count() << "s" << std::endl;

  // send sleep command to sleep timer
  // someRefToSleepTimer.sleep(sleep_time);
  std::cout << "temporary print replacing sleep: sleepTimer.sleep(" <<
                sleep_time << ");" << std::endl;
}
