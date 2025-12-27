#!/usr/bin/env python3
"""
run_checks.py
Automatizaremos:
 - kubectl apply -k k8s/
 - conftest test k8s/manifests --policy policies/conftest
 - terraform init & plan (iac/)
 - recolecta evidencias en ./evidence/
"""
import subprocess
import shutil
import os
import sys
from datetime import datetime
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVIDENCE_DIR = os.path.join(ROOT, "evidence")
IAC_DIR = os.path.join(ROOT, "iac")
K8S_DIR = os.path.join(ROOT, "k8s", "manifests")
POLICY_DIR = os.path.join(ROOT, "policies", "conftest")

def run(cmd, cwd=None, capture=False):
    print(f"> {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, text=True, capture_output=capture)
    if capture:
        return result.returncode, result.stdout + result.stderr
    return result.returncode, None

def ensure_evidence():
    os.makedirs(EVIDENCE_DIR, exist_ok=True)

def save(name, content):
    path = os.path.join(EVIDENCE_DIR, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[saved] {path}")

def collect_k8s_info():
    files = {
        "k8s_all.txt": ["kubectl", "get", "all", "-n", "agua-inteligente", "-o", "wide"],
        "k8s_netpols.yaml": ["kubectl", "get", "networkpolicies", "-n", "agua-inteligente", "-o", "yaml"],
        "k8s_rbac.yaml": ["kubectl", "get", "role,rolebinding", "-n", "agua-inteligente", "-o", "yaml"]
    }
    for fname, cmd in files.items():
        rc, out = run(cmd, capture=True)
        save(fname, out if out else f"rc={rc}\nno output")

def apply_k8s():
    print("Applying k8s via kustomize...")
    rc, _ = run(["kubectl", "apply", "-k", "k8s/"])
    if rc != 0:
        print("kubectl apply returned non-zero", rc)

def run_conftest():
    print("Running conftest tests...")
    rc, out = run(["conftest", "test", "k8s/manifests", "--policy", "policies/conftest"], capture=True)
    save("conftest_output.txt", out if out else f"rc={rc}\nno output")
    return rc

def terraform_plan():
    print("Terraform init & plan...")
    rc, out = run(["terraform", "init", "-input=false"], cwd=IAC_DIR, capture=True)
    save("terraform_init.txt", out if out else f"rc={rc}")
    rc, out = run(["terraform", "plan", "-input=false", "-detailed-exitcode", "-out=tfplan.binary"], cwd=IAC_DIR, capture=True)
    save("terraform_plan_raw.txt", out if out else f"rc={rc}")
    # show plan if exists
    plan_path = os.path.join(IAC_DIR, "tfplan.binary")
    if os.path.exists(plan_path):
        rc, out = run(["terraform", "show", "-no-color", "tfplan.binary"], cwd=IAC_DIR, capture=True)
        save("terraform_plan.txt", out if out else f"rc={rc}")
    return rc

def create_zip():
    zip_name = os.path.join(ROOT, "examen_entrega.zip")
    with zipfile.ZipFile(zip_name, "w", zipfile.ZIP_DEFLATED) as z:
        for folder, _, files in os.walk(EVIDENCE_DIR):
            for f in files:
                full = os.path.join(folder, f)
                arc = os.path.relpath(full, ROOT)
                z.write(full, arc)
        z.write(os.path.join(ROOT,"README.md"), "README.md")
        z.write(os.path.join(ROOT,"video_script.md"), "video_script.md")
    print(f"Created {zip_name}")

def main():
    ensure_evidence()
    apply_k8s()
    collect_k8s_info()
    conftest_rc = run_conftest()
    terraform_rc = terraform_plan()
    save("run_timestamp.txt", datetime.utcnow().isoformat() + "Z\n")
    create_zip()
    print("Done. Evidence in ./evidence and examen_entrega.zip")
    if conftest_rc != 0:
        print("Conftest returned non-zero (policy violations).")
    if terraform_rc == 2:
        print("Terraform plan detected changes (drift).")
    sys.exit(0)

if __name__ == "__main__":
    main()
