import json, pathlib, sys

def score(result, case):
    sources={e["source_type"] for e in result.get("evidence",[])}
    return all(x in sources for x in case["expected_sources"]) and bool(result.get("answer"))

def main(results_path):
    cases=json.loads(pathlib.Path(__file__).with_name("golden_path.json").read_text())
    results={x["id"]:x for x in json.loads(pathlib.Path(results_path).read_text())}
    passed=sum(score(results.get(c["id"],{}),c) for c in cases)
    print(json.dumps({"cases":len(cases),"passed":passed,"score":passed/len(cases)},indent=2))
    raise SystemExit(0 if passed==len(cases) else 1)
if __name__=="__main__": main(sys.argv[1])
