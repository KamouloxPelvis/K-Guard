import subprocess
import json

def run_trivy_scan(image_name: str):
    try:
        # On lance Trivy via subprocess
        # On utilise le format JSON pour que K-Guard puisse le traiter
        command = [
            "trivy", "image", 
            "--format", "json", 
            "--severity", "HIGH,CRITICAL",
            image_name
        ]
        
        process = subprocess.run(command, capture_output=True, text=True)
        
        if process.returncode != 0:
            return {"status": "error", "message": process.stderr}

        report = json.loads(process.stdout)
        
        results = report.get('Results', [])
        vulnerabilities = results[0].get('Vulnerabilities', []) if results else []
        
        return {
            "status": "success",
            "image": image_name,
            "summary": {
                "critical": len([v for v in vulnerabilities if v['Severity'] == 'CRITICAL']),
                "high": len([v for v in vulnerabilities if v['Severity'] == 'HIGH'])
            },
            "vulnerabilities": [
                {
                    "id": v['VulnerabilityID'], 
                    "pkg": v['PkgName'], 
                    "severity": v['Severity'],
                    "installed_version": v.get('InstalledVersion'),
                    "fixed_version": v.get('FixedVersion') # <-- On ajoute ça !
                }
                for v in vulnerabilities
            ]
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}