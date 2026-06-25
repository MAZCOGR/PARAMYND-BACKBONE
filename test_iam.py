from google.iam.v1 import policy_pb2

policy = policy_pb2.Policy()
try:
    policy.bindings.add(role='roles/run.invoker', members=['allUsers'])
    print("SUCCESS")
except Exception as e:
    print("ERROR:", repr(e))
