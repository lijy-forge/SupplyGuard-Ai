import copy, json, pathlib, sys
EVALS=pathlib.Path(__file__).resolve().parents[3]/"evals"
sys.path.insert(0,str(EVALS))
import run_eval  # noqa: E402

def test_all_offline_scenarios_pass():
    report=run_eval.run_all()
    assert [r["id"] for r in report if not r["passed"]]==[]
    assert len({r["id"] for r in report})==len(report)==18

def test_scenarios_are_distinct():
    data=json.loads((EVALS/"scenarios.json").read_text(encoding="utf-8"))
    for flow in ("quality","risk"):
        bodies=[json.dumps({k:v for k,v in s.items() if k not in ("id","title")},sort_keys=True) for s in data[flow]]
        assert len(set(bodies))==len(bodies)

def test_harness_detects_wrong_expectations():
    data=json.loads((EVALS/"scenarios.json").read_text(encoding="utf-8"))
    risk=copy.deepcopy(data["risk"][0]); risk["expect"]["recommendations"]=["SUP-005","SUP-002"]
    quality=copy.deepcopy(data["quality"][0]); quality["expect"]["writes_after_decision"]=0
    assert run_eval.run_risk(risk,False)[0] and run_eval.run_quality(quality,False)[0]
