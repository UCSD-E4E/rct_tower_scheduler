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
  const double TIME_SHUTDOWN = 0.5; // find real shutdon and wakeup times later
  const double TIME_WAKEUP = 0.5;

  // fetch current ensemble data from disk
  // const next_ensemble = ?

  str filename = "ensembles.json";
  if (argc > 1) {
    filename = argv[1];
  }

  // set up istream and read current ensemble function data
  Json::Value ensembles;
  std::ifstream ensemble_file(filename, std::ifstream::binary);
  ensemble_file >> ensembles;

  // temporary while we work
  std::cout << ensembles << "\n";
  std::cout << ensembles["ensemble_list"][0] << "\n";

  /*
  std::filebuf fb;
  if (fb.open (filename,std::ios::in))
  {
    std::istream instream(&fb);
    while (instream) {
      // change this to find and store current ensemble data
      std::cout << char(is.get());
    }
    fb.close();
  }
  else {
    std::cout << "invalid ensemble json file" << endl;
    return 1;
  }
  */

  // perform ensemble functions
  for (auto f : ensemble) {
    std::invoke(f);
  }

  // calculations
  auto curr_time = std::chrono::system_clock::now();
  auto next_time = std::chrono::system_clock::now(); // change this to clocktime of next ensemble
  std::chrono::duration<double> sleep_time = next_time - curr_time - TIME_SHUTDOWN - TIME_WAKEUP;
  if (sleep_time <= 0) {
    // spin/sit idle, not enough time to go into sleep and wake up again before next ensemble
  }
  std::time_t end_time = std::chrono::system_clock::to_time_t(end); // idk what this is
  std::cout << "sleep time: " << sleep_time.count() << "s" << std::endl;

  // save next ensemble to disk

  // send sleep command to sleep timer
  someRefToSleepTimer.sleep(sleep_time);
}
