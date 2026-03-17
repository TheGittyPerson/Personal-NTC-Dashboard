# Personal Network Traffic Categorization Dashboard (macOS)

A local web dashboard that shows what percentage of **your Mac's** internet activity is streaming, gaming, browsing, messaging, etc. — updated live — using only tools already built into macOS (data source: `tcpdump` DNS queries).

## Run

From this folder:

```bash
python3 -m pip install -r requirements.txt
sudo python3 app.py
```

Then open `http://localhost:8080`.

## Notes

- Requires `sudo` because `tcpdump` needs packet capture privileges.
- The chart is **based on DNS queries** (counts), so it reflects browsing activity rather than exact bandwidth.
- If your primary interface isn't detected correctly, set it explicitly:

```bash
sudo INTERFACE=en0 python3 app.py
```

