import os
import duckdb

class SASLogParser:
    def __init__(self, duck_path='analytics.duckdb'):
        self.duck_path = duck_path
        self._init_duckdb_schema()

    def _init_duckdb_schema(self):
        conn = duckdb.connect(self.duck_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS execution_log (
                log_id VARCHAR PRIMARY KEY,
                run_id VARCHAR,
                program_name VARCHAR,
                line_num INTEGER,
                log_type VARCHAR,
                message TEXT,
                created_ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.close()

    def parse_log_file(self, log_path, run_id):
        """Parses a SAS log file and extracts errors, warnings, and empty dataset notes."""
        if not os.path.exists(log_path):
            print(f"[SASLogParser] Log file not found: {log_path}")
            return []

        program_name = os.path.basename(log_path)
        findings = []
        conn = duckdb.connect(self.duck_path)

        with open(log_path, 'r', encoding='utf-8') as f:
            for idx, line in enumerate(f, start=1):
                line_str = line.strip()
                log_type = None
                
                # Check for standard SAS log message classifications
                if line_str.startswith("ERROR:"):
                    log_type = "ERROR"
                elif line_str.startswith("WARNING:"):
                    log_type = "WARNING"
                elif line_str.startswith("NOTE:") and ("0 observations" in line_str or "obs=0" in line_str or "There were 0 observations" in line_str):
                    log_type = "NOTE_OBS_ZERO"
                    
                if log_type:
                    log_id = f"LOG_{run_id}_{os.path.splitext(program_name)[0]}_{idx}"
                    conn.execute("""
                        INSERT OR REPLACE INTO execution_log (log_id, run_id, program_name, line_num, log_type, message)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, [log_id, run_id, program_name, idx, log_type, line_str])
                    findings.append({
                        "log_id": log_id,
                        "line_num": idx,
                        "log_type": log_type,
                        "message": line_str
                    })
        conn.close()
        print(f"[SASLogParser] Parsed {program_name}. Logged {len(findings)} anomalies to analytical store.")
        return findings

if __name__ == '__main__':
    parser = SASLogParser()
    # Test on a dummy path
    parser.parse_log_file("outputs/logs/derive_rule_pfs_aval.log", "RUN_TEST")
