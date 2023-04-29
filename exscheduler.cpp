#include <chrono>
#include <ctime>
#include <fstream>
#include <iostream>
#include <string>
#include <functional>
#include <json/json.h>


/***************************************************/
/*************** Read here first *******************/
/***************************************************/
/* been compiling with:
 * g++ -ljsoncpp -o testscheduler exscheduler.cpp
 * to test this out;
 * 
 * also please be aware I use the variable name "ens"
 * as a shortcut in two different locations but one
 * is for the active list and one is for the original
 * ensembles file */

int hmsToSeconds(int hour, int min, int sec)
{
	return sec + min * 60 + hour * 3600;
}

void setup(Json::Value ensembles_file)
{
	/* this assumes the ensembles are in "dummy_ensembles.json" file for now */
	std::string filename = "dummy_ensembles.json";
	Json::Value ensembles;
	std::ifstream ensemble_ifile(filename, std::ifstream::binary);
	ensemble_ifile >> ensembles;

	Json::Value ens = ensembles["ensemble_list"]; /* shortcut for orig file */

	/* this gets every ensemble and creates a new Json::Value for
	 * each start time as well as for each iteration based on the
	 * interval times */
	std::vector<Json::Value> all_ensembles;
	for (int i = 0; i < ens.size(); i++) {
		int i_hour   = ens[i]["start_time"]["hour"].asInt();
		int i_minute = ens[i]["start_time"]["minute"].asInt();
		int i_second = ens[i]["start_time"]["second"].asInt();
		int tot_time = hmsToSeconds(i_hour, i_minute, i_second);
		for (int j = 0; j <= ens[i]["iterations"].asInt(); j++) {
			int iter_seconds = ens[i]["interval"].asInt();
			Json::Value func_event;
			func_event["title"] = ens[i]["title"].asString() + "-" + std::to_string(j);
			func_event["function"] = ens[i]["function"];
			func_event["time"] = tot_time + iter_seconds * j;
			all_ensembles.push_back(func_event);
		}
	}

	/* teardown sets setup as next func then sleeps for 1-2 mins */
	Json::Value teardown;
	teardown["title"] = "teardown";
	teardown["function"] = "teardown";
	teardown["time"] = 86399; /* one min before midnight */

	all_ensembles.push_back(teardown);
	
	/* bubble sort :) */
	/* this just sorts all of the enumerated ensembles */
	for (int i = 0; i < all_ensembles.size(); i++) {
		for (int j = i+1; j < all_ensembles.size(); j++) {
			if (all_ensembles[j]["time"].asInt() < all_ensembles[i]["time"].asInt()) {
				Json::Value tmp = all_ensembles[i];
				all_ensembles[i] = all_ensembles[j];
				all_ensembles[j] = tmp;
			}
		}
	}

	Json::StyledWriter styledWriter;
	std::ofstream ensemble_ofile("active_ensembles.json", std::ifstream::binary);

	/* add enumerated ensembles to a Json "root" object then write them */
	Json::Value root;
	for (int i = 0; i < all_ensembles.size(); i++) {
		root["ensemble_list"].append(all_ensembles[i]);
	}
	/* next_ensemble is a simple integer to make it easy to index
	 * into which ensemble we want the next time we wake up */
	root["next_ensemble"] = 0;
	ensemble_ofile << styledWriter.write(root) << std::endl;
}
	

int someFunc() {
	std::cout << "someFunc called!" << std::endl;
	return 0;
}


int main(int argc, char* argv[]) {
	const double TIME_SHUTDOWN = 0.5; // find real shutdon and wakeup times later
	const double TIME_WAKEUP = 0.5;

	std::string filename = "active_ensembles.json";
	if (argc > 1) {
		filename = argv[1];
	}

	// set up istream and read active ensemble function data
	Json::Value ensembles;
	std::ifstream ensemble_ifile(filename, std::ifstream::binary);
	ensemble_ifile >> ensembles;

	// temporary, for testing while we work
	//std::cout << ensembles << "\n";
	//std::cout << ensembles["ensemble_list"][0] << "\n";

	// fetch current ensemble
	int next_ensemble = ensembles["next_ensemble"].asInt();
	if (next_ensemble == -1) { /* should run setup */
		std::cout << "next ensemble is setup!!\n";
		setup(ensembles);
		next_ensemble++;
		/* call to function that checks if next_ensemble is already
		 * past current time and if so, runs the ensemble, iterates
		 * next_ensemble and checks again */

		/* once all missed ensembles are caught up, call to function
		 * that checks if next_ensemble is far enough away to make
		 * sleep worthwhile */
	} else { /* next ensemble is a real one */
		std::cout << "next ensemble is something other than setup!!\n";
		/* get function needed to be called by indexing ensemble_list
		 * with next_ensemble, run it, then iterate next_ensemble and
		 * do the same checks as above
		 * NOTE: maybe checks should just be right after this if-else
		 * since both branches need to do the same checks */
	}

	Json::Value ens = ensembles["ensemble_list"]; /* shortcut for active */
	int nearest_ens_time = ens[next_ensemble]["time"].asInt();

	std::time_t t = std::time(0); /* right now */
	std::tm* now = std::localtime(&t);
	int curr_time_seconds = hmsToSeconds(now->tm_hour, now->tm_min, now->tm_sec);
	std::cout << "now in seconds: " << curr_time_seconds << std::endl;
	std::cout << "next ensemble time in seconds: " << nearest_ens_time << std::endl;

	return 0;

	/* the following lines (stuff with Callables) doesn't seem to work
	 * so I commented it out for the sake of compiling and testing
	 * the other work going on */
		
	//std::vector<Callable> ensemble;
	//else {
	//	for (auto e : ensembles["ensemble_list"]) {
	//		if (e["title"] == next_ensemble) {
	//			ensemble.append(e["function"]);
	//		}
	//	}
	//}

//	// perform ensemble functions
//	for (auto f : ensemble) {
//		std::invoke(f, inputs); // Wesley
//		// TODO: allow for function arguments via e["inputs"]
//		// should just be comma-separated list of inputs
//	}
//
//	/* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * */
//
//	/* Hannah
//	   TODO: update each individual ensemble's next execution time IF IT WAS CALLED
//	   if (next_ensemble == "" might need to change this but the first ensemble executing) {
//	   add interval secs to value of start_time
//	   }
//	   else if (determine if intervals remain) {
//	   add interval secs to current value of next_time
//	   }
//	   else {
//	   set next_time to default (23:59:59 or just blank really)
//	   }
//	*/
//
//	// save next ensemble to disk
//	/*
//	  TODO: replace next_ensemble with title of next-occurring ensemble
//	  (i.e., lowest hr/min/sec in next_time)
//	  Might want to make a function with "next_time"/"start_time" argument options
//	  to find lowest next/start time among all ensembles, since this is really the
//	  same as the line 34 TODO
//	*/
//	ensembles["next_ensemble"] = "dummy2"; // replace dummy2 obviously
//
//	Json::StyledWriter styledWriter;
//	Json::FastWriter fastWriter;
//	std::ofstream ensemble_ofile(filename, std::ifstream::binary);
//	ofstream << styledWriter.write(ensembles) << std::endl;
//	ofstream << fastWriter.write(ensembles) << std::endl;
//
//	/* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * */
//
//	// calculations
//	auto curr_time = std::chrono::system_clock::now();
//	auto next_time = std::chrono::system_clock::now(); // TODO: change this to clocktime of next ensemble
//	std::chrono::duration<double> sleep_time = next_time - curr_time - TIME_SHUTDOWN - TIME_WAKEUP;
//	if (sleep_time <= 0) {
//		// not enough time to go into sleep and wake up again before next ensemble
//		sleep(sleep_time); // C++ sleep function, not sleep timer
//	}
//	std::time_t end_time = std::chrono::system_clock::to_time_t(next_time); // idk what this is
//	std::cout << "sleep time: " << sleep_time.count() << "s" << std::endl;
//
//	// send sleep command to sleep timer
//	// someRefToSleepTimer.sleep(sleep_time);
//	std::cout << "temporary print replacing sleep: sleepTimer.sleep(" <<
//		sleep_time << ");" << std::endl;
}
