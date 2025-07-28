# Test Program to do a batch run of Test.py
import json
import Test

for i in range(1,5):
    with open("parameters.json",'r') as file:
        data = file.read()
    dict = json.loads(data)
    dict['test_flag'] = i
    data = json.dumps(dict)
    with open("parameters.json",'w') as file:
        file.write(data)
    # exec(open("Test.py").read())
    # import subprocess
    # subprocess.call("Test.py", shell=True)
    Test.test_fun()
    print(Test.dummy)


