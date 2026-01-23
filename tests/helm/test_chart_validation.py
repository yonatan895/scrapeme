"""
Helm chart validation tests.

These tests validate the Helm chart templates without requiring a Kubernetes cluster.
They use PyYAML to parse YAML templates and perform structural validation.
"""

import os
import re
from pathlib import Path
from typing import Any

import pytest
import yaml

# Chart paths
CHART_DIR = Path(__file__).parent.parent.parent / "charts" / "scrapeme"
TEMPLATES_DIR = CHART_DIR / "templates"
VALUES_FILE = CHART_DIR / "values.yaml"
CHART_FILE = CHART_DIR / "Chart.yaml"
ARGOCD_DIR = Path(__file__).parent.parent.parent / "argocd"


class TestChartStructure:
    """Tests for Helm chart file structure."""

    def test_chart_yaml_exists(self) -> None:
        """Chart.yaml must exist."""
        assert CHART_FILE.exists(), "Chart.yaml is missing"

    def test_values_yaml_exists(self) -> None:
        """values.yaml must exist."""
        assert VALUES_FILE.exists(), "values.yaml is missing"

    def test_templates_directory_exists(self) -> None:
        """templates directory must exist."""
        assert TEMPLATES_DIR.exists(), "templates directory is missing"

    def test_required_templates_exist(self) -> None:
        """All required templates must exist."""
        required_templates = [
            "deployment.yaml",
            "service.yaml",
            "configmap.yaml",
            "secret.yaml",
            "serviceaccount.yaml",
            "_helpers.tpl",
            "NOTES.txt",
        ]
        for template in required_templates:
            template_path = TEMPLATES_DIR / template
            assert template_path.exists(), f"Required template {template} is missing"

    def test_production_templates_exist(self) -> None:
        """Production-ready templates must exist."""
        production_templates = [
            "ingress.yaml",
            "pdb.yaml",
            "hpa.yaml",
            "servicemonitor.yaml",
        ]
        for template in production_templates:
            template_path = TEMPLATES_DIR / template
            assert template_path.exists(), f"Production template {template} is missing"


class TestChartYaml:
    """Tests for Chart.yaml content."""

    @pytest.fixture
    def chart_data(self) -> dict[str, Any]:
        """Load Chart.yaml content."""
        with open(CHART_FILE) as f:
            return yaml.safe_load(f)

    def test_chart_api_version(self, chart_data: dict[str, Any]) -> None:
        """Chart must use apiVersion v2."""
        assert chart_data.get("apiVersion") == "v2"

    def test_chart_has_name(self, chart_data: dict[str, Any]) -> None:
        """Chart must have a name."""
        assert chart_data.get("name") == "scrapeme"

    def test_chart_has_version(self, chart_data: dict[str, Any]) -> None:
        """Chart must have a version."""
        assert "version" in chart_data
        # Version should be semver-ish
        version = chart_data["version"]
        assert re.match(r"^\d+\.\d+\.\d+", version), f"Invalid version format: {version}"

    def test_chart_has_app_version(self, chart_data: dict[str, Any]) -> None:
        """Chart must have an appVersion."""
        assert "appVersion" in chart_data

    def test_chart_has_dependencies(self, chart_data: dict[str, Any]) -> None:
        """Chart must define dependencies."""
        deps = chart_data.get("dependencies", [])
        assert len(deps) > 0, "Chart should have dependencies defined"

        # Check for expected dependencies
        dep_names = [d["name"] for d in deps]
        expected_deps = ["postgresql", "redis", "kafka", "selenium-grid"]
        for expected in expected_deps:
            assert expected in dep_names, f"Missing dependency: {expected}"


class TestValuesYaml:
    """Tests for values.yaml content."""

    @pytest.fixture
    def values_data(self) -> dict[str, Any]:
        """Load values.yaml content."""
        with open(VALUES_FILE) as f:
            return yaml.safe_load(f)

    def test_has_image_config(self, values_data: dict[str, Any]) -> None:
        """Values must have image configuration."""
        assert "image" in values_data
        assert "repository" in values_data["image"]
        assert "tag" in values_data["image"]

    def test_has_service_config(self, values_data: dict[str, Any]) -> None:
        """Values must have service configuration."""
        assert "service" in values_data
        assert "port" in values_data["service"]
        assert values_data["service"]["port"] == 9090

    def test_has_mode_config(self, values_data: dict[str, Any]) -> None:
        """Values must have execution mode configuration."""
        assert "mode" in values_data
        assert values_data["mode"] in ["deployment", "cronjob"]

    def test_has_deployment_config(self, values_data: dict[str, Any]) -> None:
        """Values must have deployment configuration."""
        assert "deployment" in values_data
        assert "replicaCount" in values_data["deployment"]
        assert "loopInterval" in values_data["deployment"]

    def test_has_cronjob_config(self, values_data: dict[str, Any]) -> None:
        """Values must have cronjob configuration."""
        assert "cronjob" in values_data
        assert "schedule" in values_data["cronjob"]

    def test_has_autoscaling_config(self, values_data: dict[str, Any]) -> None:
        """Values must have autoscaling configuration."""
        assert "autoscaling" in values_data
        assert "enabled" in values_data["autoscaling"]
        assert "minReplicas" in values_data["autoscaling"]
        assert "maxReplicas" in values_data["autoscaling"]

    def test_has_pdb_config(self, values_data: dict[str, Any]) -> None:
        """Values must have PodDisruptionBudget configuration."""
        assert "pdb" in values_data
        assert "enabled" in values_data["pdb"]

    def test_has_ingress_config(self, values_data: dict[str, Any]) -> None:
        """Values must have ingress configuration."""
        assert "ingress" in values_data
        assert "enabled" in values_data["ingress"]
        assert "hosts" in values_data["ingress"]

    def test_has_resources_config(self, values_data: dict[str, Any]) -> None:
        """Values must have resources configuration."""
        assert "resources" in values_data

    def test_has_monitoring_config(self, values_data: dict[str, Any]) -> None:
        """Values must have monitoring configuration."""
        assert "monitoring" in values_data
        assert "serviceMonitor" in values_data["monitoring"]


class TestArgoCD:
    """Tests for ArgoCD configuration."""

    def test_application_yaml_exists(self) -> None:
        """ArgoCD application.yaml must exist."""
        app_file = ARGOCD_DIR / "application.yaml"
        assert app_file.exists(), "argocd/application.yaml is missing"

    def test_production_values_exists(self) -> None:
        """ArgoCD production values must exist."""
        prod_values = ARGOCD_DIR / "values-production.yaml"
        assert prod_values.exists(), "argocd/values-production.yaml is missing"

    @pytest.fixture
    def app_data(self) -> dict[str, Any]:
        """Load ArgoCD application.yaml."""
        with open(ARGOCD_DIR / "application.yaml") as f:
            return yaml.safe_load(f)

    @pytest.fixture
    def prod_values(self) -> dict[str, Any]:
        """Load ArgoCD production values."""
        with open(ARGOCD_DIR / "values-production.yaml") as f:
            return yaml.safe_load(f)

    def test_application_api_version(self, app_data: dict[str, Any]) -> None:
        """Application must use correct API version."""
        assert app_data.get("apiVersion") == "argoproj.io/v1alpha1"

    def test_application_kind(self, app_data: dict[str, Any]) -> None:
        """Application must have correct kind."""
        assert app_data.get("kind") == "Application"

    def test_application_has_sync_policy(self, app_data: dict[str, Any]) -> None:
        """Application must have sync policy."""
        assert "syncPolicy" in app_data["spec"]
        sync_policy = app_data["spec"]["syncPolicy"]
        assert "automated" in sync_policy
        assert sync_policy["automated"].get("prune") is True
        assert sync_policy["automated"].get("selfHeal") is True

    def test_production_has_autoscaling(self, prod_values: dict[str, Any]) -> None:
        """Production values must enable autoscaling."""
        assert "autoscaling" in prod_values
        assert prod_values["autoscaling"].get("enabled") is True

    def test_production_has_pdb(self, prod_values: dict[str, Any]) -> None:
        """Production values must enable PDB."""
        assert "pdb" in prod_values
        assert prod_values["pdb"].get("enabled") is True

    def test_production_has_resources(self, prod_values: dict[str, Any]) -> None:
        """Production values must define resources."""
        assert "resources" in prod_values
        assert "limits" in prod_values["resources"]
        assert "requests" in prod_values["resources"]


class TestTemplatesSyntax:
    """Tests for template file syntax."""

    def test_yaml_templates_valid(self) -> None:
        """All YAML templates must have valid Helm templating syntax."""
        for template_file in TEMPLATES_DIR.glob("*.yaml"):
            content = template_file.read_text()
            # Check for common template issues
            # Unbalanced braces
            open_braces = content.count("{{")
            close_braces = content.count("}}")
            assert open_braces == close_braces, (
                f"{template_file.name}: Unbalanced template braces "
                f"({{ {open_braces} vs }} {close_braces})"
            )

    def test_helpers_tpl_exists_and_has_functions(self) -> None:
        """_helpers.tpl must exist and define required functions."""
        helpers = TEMPLATES_DIR / "_helpers.tpl"
        assert helpers.exists()

        content = helpers.read_text()
        required_funcs = [
            "scrapeme.name",
            "scrapeme.fullname",
            "scrapeme.labels",
            "scrapeme.selectorLabels",
            "scrapeme.serviceAccountName",
        ]
        for func in required_funcs:
            assert func in content, f"Missing helper function: {func}"

    def test_deployment_has_required_sections(self) -> None:
        """Deployment template must have required sections."""
        deployment = TEMPLATES_DIR / "deployment.yaml"
        content = deployment.read_text()

        required_patterns = [
            r"apiVersion:\s*apps/v1",
            r"kind:\s*Deployment",
            r"livenessProbe:",
            r"readinessProbe:",
            r"resources:",
            r"volumeMounts:",
        ]
        for pattern in required_patterns:
            assert re.search(pattern, content), (
                f"Deployment template missing required section: {pattern}"
            )

    def test_hpa_has_required_sections(self) -> None:
        """HPA template must have required sections."""
        hpa = TEMPLATES_DIR / "hpa.yaml"
        content = hpa.read_text()

        required_patterns = [
            r"apiVersion:\s*autoscaling/v2",
            r"kind:\s*HorizontalPodAutoscaler",
            r"scaleTargetRef:",
            r"minReplicas:",
            r"maxReplicas:",
        ]
        for pattern in required_patterns:
            assert re.search(pattern, content), (
                f"HPA template missing required section: {pattern}"
            )

    def test_pdb_has_required_sections(self) -> None:
        """PDB template must have required sections."""
        pdb = TEMPLATES_DIR / "pdb.yaml"
        content = pdb.read_text()

        required_patterns = [
            r"apiVersion:\s*policy/v1",
            r"kind:\s*PodDisruptionBudget",
            r"selector:",
        ]
        for pattern in required_patterns:
            assert re.search(pattern, content), (
                f"PDB template missing required section: {pattern}"
            )

    def test_ingress_has_required_sections(self) -> None:
        """Ingress template must have required sections."""
        ingress = TEMPLATES_DIR / "ingress.yaml"
        content = ingress.read_text()

        required_patterns = [
            r"apiVersion:\s*networking.k8s.io/v1",
            r"kind:\s*Ingress",
            r"tls:",
            r"rules:",
        ]
        for pattern in required_patterns:
            assert re.search(pattern, content), (
                f"Ingress template missing required section: {pattern}"
            )


class TestMonitoringConfig:
    """Tests for monitoring configuration files."""

    MONITORING_DIR = Path(__file__).parent.parent.parent / "monitoring"

    def test_prometheus_config_exists(self) -> None:
        """Prometheus config must exist."""
        prometheus_file = self.MONITORING_DIR / "prometheus.yaml"
        assert prometheus_file.exists()

    def test_alerts_file_exists(self) -> None:
        """Alerts file must exist."""
        alerts_file = self.MONITORING_DIR / "alerts.yaml"
        assert alerts_file.exists()

    def test_prometheus_references_correct_alerts_file(self) -> None:
        """Prometheus config must reference the correct alerts filename."""
        prometheus_file = self.MONITORING_DIR / "prometheus.yaml"
        with open(prometheus_file) as f:
            content = f.read()

        # Should reference alerts.yaml, not alerts.yml
        assert "alerts.yaml" in content, "Prometheus should reference alerts.yaml"
        assert "alerts.yml" not in content, "Prometheus should not reference alerts.yml"

    def test_alertmanager_config_exists(self) -> None:
        """Alertmanager config must exist."""
        alertmanager_file = self.MONITORING_DIR / "alertmanager.yaml"
        assert alertmanager_file.exists()
