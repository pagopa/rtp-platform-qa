#!/usr/bin/env python3
import json
import sys
import matplotlib.pyplot as plt

def analyze_k6_json(filename):
    summary = None
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if entry.get("type") == "Summary":
                summary = entry.get("data", {})
                break

    if not summary:
        print("❌ Summary non trovato nel file.")
        sys.exit(1)

    metrics = summary.get("metrics", {})

    total_requests = metrics.get("http_reqs", {}).get("values", {}).get("count", 0)
    failure_rate = metrics.get("http_req_failed", {}).get("values", {}).get("rate", 0) * 100
    success_rate = 100 - failure_rate

    dur_vals = metrics.get("http_req_duration", {}).get("values", {})
    avg_duration = dur_vals.get("avg", 0)
    p95_duration = dur_vals.get("p(95)", 0)

    print(f"Richieste totali: {total_requests}")
    print(f"Success rate: {success_rate:.2f}%")
    print(f"Failure rate: {failure_rate:.2f}%")
    print(f"Avg duration: {avg_duration:.2f} ms")
    print(f"P95 duration: {p95_duration:.2f} ms")

    plt.figure()
    plt.bar(['Success', 'Failure'], [success_rate, failure_rate])
    plt.ylabel('Percentage (%)')
    plt.ylim(0, 100)
    plt.title('Success vs Failure Rate')
    plt.savefig('success_failure_rate.png')
    print("✔️ Chart salvato: success_failure_rate.png")

    plt.figure()
    plt.bar(['Average', 'P95'], [avg_duration, p95_duration])
    plt.ylabel('Duration (ms)')
    plt.title('Response Time Metrics')
    plt.savefig('response_time_metrics.png')
    print("✔️ Chart salvato: response_time_metrics.png")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <k6-results.json>")
        sys.exit(1)
    analyze_k6_json(sys.argv[1])
