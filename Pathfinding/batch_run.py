import json
import subprocess
from main_simulation_bicr import run_simulation

# No of requests

no_of_req = [i for i in range(1300,2101,200)]

fleet_size = [20,50,100,200]

# BiCriterion

bicr_conditions = ['1','2','3']

bicr_policies = ['2b']
# demand_coefficient = [float(i) for i in range(1,11,1)]
demand_coefficient = [0.01,0.1,0.5,1.0]

for r in no_of_req:
    for v in fleet_size:
        print("Req ", r, " Fleet ", v, " False Myopic")
        # First run myopic assignment
        # Update parameter json file
        with open("parameters.json",'r') as file:
            data = file.read()
        para_dict = json.loads(data)
        para_dict["request_size"] = r
        para_dict["fleet_size"] = v
        para_dict["bicr_flag"] = "False"
        # Save json file
        data = json.dumps(para_dict)
        with open("parameters.json",'w') as file:
            file.write(data)
        # Run program for this scenario
        # exec(open("main_simulation_bicr.py").read())
        run_simulation()
        # subprocess.call("main_simulation_bicr.py", shell=True)
        # Now run for different bi-criterion conditions and reward coefficients
        # You can add more loops here for more conditions
        for reward in demand_coefficient:
            for condition in bicr_conditions:
                print("Req ", r, " Fleet ", v, " True 2b Reward ",reward," Condition ",condition)

                # Update parameter json file
                with open("parameters.json", 'r') as file:
                    data = file.read()
                para_dict = json.loads(data)
                para_dict["bicr_flag"] = "True"
                # For now always use 2b bicr policy (multi-objective)
                para_dict["bicr_policy"] = '2b'
                para_dict["bicr_condi"] = condition
                para_dict["reward_coeff"] = reward
                # Save json file
                data = json.dumps(para_dict)
                with open("parameters.json", 'w') as file:
                    file.write(data)
                # Now run program for these scenarios
                # exec(open("main_simulation_bicr.py").read())
                # subprocess.call("main_simulation_bicr.py", shell=True)
                run_simulation()
            # End of bicr conditions loop
        # End of different reward coeffs loop
    # End of fleet size loop
# End of demand size loop


