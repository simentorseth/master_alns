# Notes for the ALNS Metaheuristic

## Numbers and parameter values in instances
Numbers are based on the technical specification given for the Rem Energy CSOV, found athttps://www.remoffshore.no/fleet/rem-energy/

## Solution Representation

The solution representation consists of two arrays. The first array keeps track of each vessel and turbine visits. Each vessel is separated by a separator, where the separator is the number zero. The second array tracks which charging stations have been used by each vessel. The size of the second array is the number of vessels.

[1, 3, 5, 0, 2, 4, 6]

The example above shows a soltion of an instance. Here, the first vessel visits turbines 1, 3, and 5; after the 0 separator, the next vessel visits turbines 2, 4, and 6.

### Questions to yourself

* Q: What happens if a vessel is not used?
    * A: Should not be a problem? The vessel is not used, thus not in the first array nor in the second.
 



## Feasibility function

* What should it keep track of?
* Assume valid solution?



## Cost function


## Solution representation
