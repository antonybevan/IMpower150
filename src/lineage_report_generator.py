import os
import sqlite3

class LineageReportGenerator:
    def __init__(self, db_path='metadata.db', output_dir='outputs/submission'):
        self.db_path = db_path
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_report(self):
        """Generates an aesthetic, interactive HTML lineage report showing variable-to-concept tracing."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        cur = conn.cursor()
        
        # 1. Fetch Variables and their Concepts
        cur.execute("""
            SELECT v.variable, v.dataset, v.role, v.datatype, v.bc_id, b.bc_name, b.cosmos_bc_id, b.bc_definition
            FROM variables v
            LEFT JOIN biomedical_concepts b ON v.bc_id = b.bc_id
            ORDER BY v.dataset, v.variable
        """)
        vars_data = cur.fetchall()
        
        # 2. Fetch Rules and their assessor/target info
        cur.execute("""
            SELECT r.rule_id, r.target_variable, r.logic_type, r.assessor, r.criteria_type, r.endpoint_id
            FROM derivation_rules r
        """)
        rules_data = cur.fetchall()
        
        # Build HTML content
        html_content = []
        html_content.append("""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>IMpower150 Variable Lineage & Semantic Mapping Report</title>
    <style>
        body {
            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
            background-color: #060810;
            color: #C8D4E4;
            max-width: 1100px;
            margin: 40px auto;
            padding: 0 20px;
        }
        .header {
            background: linear-gradient(135deg, #0A0D18 0%, #181D2E 100%);
            border: 1px solid #181D2E;
            padding: 30px;
            border-radius: 8px;
            margin-bottom: 30px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.5);
            text-align: center;
        }
        .header h1 {
            margin: 0;
            font-size: 26px;
            font-weight: 700;
            color: #76E4F7;
        }
        .header p {
            margin: 8px 0 0 0;
            color: #6B7A94;
            font-size: 12px;
            letter-spacing: 2px;
            text-transform: uppercase;
        }
        .card {
            background-color: #0A0D18;
            border: 1px solid #181D2E;
            border-radius: 8px;
            padding: 24px;
            margin-bottom: 24px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        }
        h2 {
            font-size: 18px;
            color: #EDF2F7;
            border-left: 3px solid #B794F4;
            padding-left: 12px;
            margin-top: 0;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }
        th, td {
            text-align: left;
            padding: 12px;
            border-bottom: 1px solid #181D2E;
            font-size: 13px;
        }
        th {
            background-color: #101424;
            color: #EDF2F7;
            font-weight: bold;
        }
        tr:hover {
            background-color: #101424;
        }
        .code {
            font-family: monospace;
            background-color: #101424;
            color: #F6AD55;
            padding: 2px 6px;
            border-radius: 4px;
        }
        .badge {
            background-color: rgba(104, 211, 145, 0.12);
            border: 1px solid rgba(104, 211, 145, 0.3);
            color: #68D391;
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: bold;
        }
        .badge-rules {
            background-color: rgba(252, 129, 129, 0.12);
            border: 1px solid rgba(252, 129, 129, 0.3);
            color: #FC8181;
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>IMpower150 Computable Lineage Ledger</h1>
        <p>Phase 8 Variable-to-Concept Semantic Mapping</p>
    </div>
    
    <div class="card">
        <h2>1. Variables & COSMoS Concepts Trace</h2>
        <table>
            <thead>
                <tr>
                    <th>Variable (Dataset)</th>
                    <th>Role</th>
                    <th>Biomedical Concept Name</th>
                    <th>COSMoS ID</th>
                    <th>Concept Definition</th>
                </tr>
            </thead>
            <tbody>""")

        for row in vars_data:
            var_name, dataset, role, datatype, bc_id, bc_name, cosmos_bc_id, bc_definition = row
            bc_name = bc_name or "Unlinked"
            cosmos_bc_id = cosmos_bc_id or "N/A"
            bc_definition = bc_definition or "N/A"
            
            html_content.append(f"""
                <tr>
                    <td><span class="code"><strong>{dataset}.{var_name}</strong></span></td>
                    <td>{role}</td>
                    <td><span class="badge">{bc_name}</span></td>
                    <td><code>{cosmos_bc_id}</code></td>
                    <td style="color: #A0AEC0;">{bc_definition}</td>
                </tr>""")

        html_content.append("""
            </tbody>
        </table>
    </div>

    <div class="card">
        <h2>2. Rules & Downstream Variable Lineage</h2>
        <table>
            <thead>
                <tr>
                    <th>Rule ID</th>
                    <th>Derives Variable</th>
                    <th>Logic Type</th>
                    <th>Assessor</th>
                    <th>RECIST Version</th>
                    <th>Clinical Endpoint ID</th>
                </tr>
            </thead>
            <tbody>""")

        for row in rules_data:
            rule_id, target_var, logic_type, assessor, criteria_type, endpoint_id = row
            html_content.append(f"""
                <tr>
                    <td><strong>{rule_id}</strong></td>
                    <td><span class="code">{target_var}</span></td>
                    <td><span class="badge-rules">{logic_type}</span></td>
                    <td>{assessor}</td>
                    <td>{criteria_type}</td>
                    <td><code>{endpoint_id}</code></td>
                </tr>""")

        html_content.append("""
            </tbody>
        </table>
    </div>
    
    <div style="text-align: center; color: #718096; font-size: 11px; margin-top: 40px;">
        <p>IMpower150 Semantic Audit Lineage ledger &bull; Generated dynamically from SQLite Metadata Database &bull; Confidential</p>
    </div>
</body>
</html>""")
        
        report_path = os.path.join(self.output_dir, "lineage_report.html")
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(html_content))
            
        conn.close()
        print(f"[LineageReportGenerator] Generated premium HTML lineage report: {report_path}")
        return report_path

if __name__ == '__main__':
    generator = LineageReportGenerator()
    generator.generate_report()
