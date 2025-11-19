/*********************************************
 * OPL 22.1.1.0 Model
 * Author: olive
 * Creation Date: 16 Nov 2025 at 18:07:34
 *********************************************/
// Species Habitat Optimization Model in OPL

// Sets
{string} Cells = ...;
{string} Actions = ...;
{string} Species = ...;
{string} Connections = ...;
{string} Coexistance = {"coexist_eliomys", "coexist_oryctolagus"};
{string} Ext_Species = Species union {"corridor"};

// Parameters
float Costs[Cells][Ext_Species] = ...;
float SuitabilityScores[Cells][Ext_Species] = ...;
{string} Neighbors[Cells] = ...;
float Area[Cells] = ...;

// Assuming SpeciesDistances is structured as SpeciesDistances[Species][Cells] = [array of distances]
range DistRange = 1..24;
float SpeciesDistances[Species][Cells][DistRange] = ...;

// Decision variables
dvar boolean add[Cells][Species];
dvar boolean cor[Cells];
dvar boolean con[Cells][Species];
dvar boolean con_o[Cells][Species][DistRange];
dvar boolean coex[Cells][Coexistance]; // predator coexistance variables, define index set accordingly

// Objective: Maximize weighted habitat suitability plus connectivity minus coexistence penalty
float origin_coef = 0.5;
float coexist_coef = 0.5;

maximize sum(c in Cells) (Area[c] * sum(s in Species) (add[c][s] * (
		SuitabilityScores[c][s]
		+ origin_coef * sum(o in DistRange) (con_o[c][s][o])
	))
	- coexist_coef * sum(cex in Coexistance) (coex[c][cex]));

// Budget constraint
float Budget = 1000;
float min_balance = 0.2;
float epsilon = 0.0001;
subject to {
  // Budget constraint
  sum(c in Cells) (Costs[c]["corridor"]*cor[c] + sum(s in Species) (Costs[c][s] * add[c][s])) <= Budget;
  
  // Coexistance linking constraint
  forall(c in Cells) {
    coex[c]["coexist_eliomys"] <= add[c]["eliomys"];
    coex[c]["coexist_eliomys"] <= add[c]["martes"];
    coex[c]["coexist_eliomys"] >= add[c]["eliomys"] + add[c]["martes"] - 1;
    coex[c]["coexist_oryctolagus"] <= add[c]["oryctolagus"];
    coex[c]["coexist_oryctolagus"] <= add[c]["martes"];
    coex[c]["coexist_oryctolagus"] >= add[c]["oryctolagus"] + add[c]["martes"] - 1;
  }
  
  // Balance constraint
  forall(s1 in Species) {
    sum(c in Cells) (Area[c] * sum(s in Species) (
		(SuitabilityScores[c][s] * add[c][s]
		+ sum(o in DistRange) (con_o[c][s][o]))
		* ((s1 == s) ? 1-min_balance : -min_balance)
	)) >= 0;
  }
  
  forall(c in Cells, s in Species) {
    // Connection usage constraint
    0.5*(add[c][s]+cor[c]) <= con[c][s];
    con[c][s] <= add[c][s]+cor[c];
    
    // Connection summary linking constraint
    epsilon*sum(o in DistRange) (con_o[c][s][o]) <= con[c][s];
    con[c][s] <= sum(o in DistRange) (con_o[c][s][o]);
    
    // Connection to origin constraints
    forall(o in DistRange) {
      if (SpeciesDistances[s][c][o] > 1) {
        if(SpeciesDistances[s][c][o] > 1000) {
          con_o[c][s][o] == 0;
        }
        else {
          con_o[c][s][o] <= sum(n in Neighbors[c]) (
	        	con_o[n][s][o] * ((SpeciesDistances[s][n][o] < SpeciesDistances[s][c][o]) ? 1:0)
	        );
        }
      }
    }
  }
}

execute {
  // Optional execution logic: print solution summary, etc
  writeln("Optimal value: ", cplex.getObjValue());
}
 