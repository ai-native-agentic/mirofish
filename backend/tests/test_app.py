import importlib
import asyncio
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from flask import Blueprint


BACKEND_DIR = Path(__file__).resolve().parents[1]
SERVICES_DIR = BACKEND_DIR / "app" / "services"


def _clear_modules(prefixes):
    for name in list(sys.modules):
        if any(name == prefix or name.startswith(f"{prefix}.") for prefix in prefixes):
            sys.modules.pop(name, None)


def _stub_services_package(monkeypatch):
    services_pkg = types.ModuleType("app.services")
    services_pkg.__path__ = [str(SERVICES_DIR)]
    monkeypatch.setitem(sys.modules, "app.services", services_pkg)


def _build_fake_api_module():
    api_module = types.ModuleType("app.api")

    graph_bp = Blueprint("graph", __name__)
    simulation_bp = Blueprint("simulation", __name__)
    report_bp = Blueprint("report", __name__)

    @graph_bp.route("/ping")
    def graph_ping():
        return {"ok": True, "scope": "graph"}

    @simulation_bp.route("/ping")
    def simulation_ping():
        return {"ok": True, "scope": "simulation"}

    @report_bp.route("/ping")
    def report_ping():
        return {"ok": True, "scope": "report"}

    setattr(api_module, "graph_bp", graph_bp)
    setattr(api_module, "simulation_bp", simulation_bp)
    setattr(api_module, "report_bp", report_bp)
    return api_module


def test_create_app_factory_registers_health_and_api_routes(monkeypatch):
    _clear_modules(["app.api", "app.services"])
    _stub_services_package(monkeypatch)

    simulation_runner_module = types.ModuleType("app.services.simulation_runner")
    setattr(
        simulation_runner_module,
        "SimulationRunner",
        type("SimulationRunner", (), {"register_cleanup": staticmethod(MagicMock())}),
    )
    monkeypatch.setitem(
        sys.modules, "app.services.simulation_runner", simulation_runner_module
    )
    monkeypatch.setitem(sys.modules, "app.api", _build_fake_api_module())

    app_module = importlib.import_module("app")
    app = app_module.create_app()
    client = app.test_client()

    health = client.get("/health")
    graph_ping = client.get("/api/graph/ping")

    assert health.status_code == 200
    assert health.get_json() == {"status": "ok", "service": "MiroFish Backend"}
    assert graph_ping.status_code == 200
    assert graph_ping.get_json() == {"ok": True, "scope": "graph"}


def test_create_app_factory_loads_custom_config(monkeypatch):
    _clear_modules(["app.api", "app.services"])
    _stub_services_package(monkeypatch)

    simulation_runner_module = types.ModuleType("app.services.simulation_runner")
    setattr(
        simulation_runner_module,
        "SimulationRunner",
        type("SimulationRunner", (), {"register_cleanup": staticmethod(MagicMock())}),
    )
    monkeypatch.setitem(
        sys.modules, "app.services.simulation_runner", simulation_runner_module
    )
    monkeypatch.setitem(sys.modules, "app.api", _build_fake_api_module())

    app_module = importlib.import_module("app")

    class TestConfig:
        DEBUG = False
        SECRET_KEY = "custom-key"

    app = app_module.create_app(TestConfig)

    assert app.config["DEBUG"] is False
    assert app.config["SECRET_KEY"] == "custom-key"


def test_config_defaults_and_validate(monkeypatch):
    _clear_modules(["app.config"])
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("ZEP_API_KEY", raising=False)
    monkeypatch.setenv("FLASK_DEBUG", "False")

    config_module = importlib.import_module("app.config")
    Config = config_module.Config

    assert Config.DEBUG is False
    assert Config.JSON_AS_ASCII is False
    errors = Config.validate()
    assert "LLM_API_KEY 未配置" in errors
    assert "ZEP_API_KEY 未配置" in errors


def test_simulation_manager_initialization_creates_data_dir(monkeypatch, tmp_path):
    _clear_modules(["app.services"])
    _stub_services_package(monkeypatch)

    zep_reader_module = types.ModuleType("app.services.zep_entity_reader")
    setattr(zep_reader_module, "ZepEntityReader", object)
    setattr(zep_reader_module, "FilteredEntities", object)

    profile_module = types.ModuleType("app.services.oasis_profile_generator")
    setattr(profile_module, "OasisProfileGenerator", object)
    setattr(profile_module, "OasisAgentProfile", object)

    config_module = types.ModuleType("app.services.simulation_config_generator")
    setattr(config_module, "SimulationConfigGenerator", object)
    setattr(config_module, "SimulationParameters", object)

    monkeypatch.setitem(
        sys.modules, "app.services.zep_entity_reader", zep_reader_module
    )
    monkeypatch.setitem(
        sys.modules, "app.services.oasis_profile_generator", profile_module
    )
    monkeypatch.setitem(
        sys.modules, "app.services.simulation_config_generator", config_module
    )

    sim_manager_module = importlib.import_module("app.services.simulation_manager")
    SimulationManager = sim_manager_module.SimulationManager
    monkeypatch.setattr(
        SimulationManager, "SIMULATION_DATA_DIR", str(tmp_path), raising=False
    )

    manager = SimulationManager()

    assert Path(manager.SIMULATION_DATA_DIR).exists()


def test_retry_with_backoff_retries_until_success(monkeypatch):
    retry_module = importlib.import_module("app.utils.retry")
    attempts = {"count": 0}
    callback = MagicMock()

    monkeypatch.setattr(retry_module.time, "sleep", lambda _: None)

    @retry_module.retry_with_backoff(
        max_retries=2, initial_delay=0.01, jitter=False, on_retry=callback
    )
    def flaky_call():
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise RuntimeError("transient")
        return "ok"

    assert flaky_call() == "ok"
    assert attempts["count"] == 3
    assert callback.call_count == 2


@pytest.mark.asyncio
async def test_retry_with_backoff_async_retries_then_succeeds(monkeypatch):
    retry_module = importlib.import_module("app.utils.retry")
    attempts = {"count": 0}
    callback = MagicMock()

    async def no_sleep(_: float):
        return None

    monkeypatch.setattr(asyncio, "sleep", no_sleep)

    @retry_module.retry_with_backoff_async(
        max_retries=1,
        initial_delay=0.01,
        jitter=False,
        on_retry=callback,
    )
    async def flaky_async_call():
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise RuntimeError("transient")
        return "ok"

    assert await flaky_async_call() == "ok"
    assert attempts["count"] == 2
    callback.assert_called_once()
