import pytest
import pytest_asyncio
import asyncio
from pathlib import Path
import tempfile
import os
from claude_cli_auth import ClaudeAuthManager, AuthConfig, ClaudeTimeoutError

# Skip tests if not explicitly enabled to prevent accidental costs/api calls
# Run with: pytest tests/test_e2e_live.py --run-live
# OR env var RUN_LIVE_TESTS=1
run_live = pytest.mark.skipif(
    not os.getenv("RUN_LIVE_TESTS"),
    reason="Nutné nastavit env proměnnou RUN_LIVE_TESTS=1 pro spuštění živých testů (stojí peníze/tokeny)"
)

@pytest_asyncio.fixture
async def auth_manager():
    """Fixture pro inicializaci managera s krátkým timeoutem pro testy."""
    config = AuthConfig(
        timeout_seconds=60,
        use_sdk=False, # Vynutíme CLI pro jistotu, pokud nemáme SDK nainstalované
        working_directory=Path(".")
    )
    # We catch init error here to skip gracefully if not authenticated
    try:
        manager = ClaudeAuthManager(config=config)
    except Exception as e:
        if "not authenticated" in str(e).lower() or "no interfaces available" in str(e).lower():
             pytest.skip(f"Claude Auth initialization failed (not authenticated?): {e}")
        raise e

    # Check if authenticated (redundant if init passed, but good for safety)
    if not manager.auth_manager.is_authenticated():
        pytest.skip("Claude CLI není autentizováno. Spusťte 'claude auth login'.")

    yield manager
    await manager.shutdown()

@run_live
@pytest.mark.asyncio
async def test_01_basic_connectivity(auth_manager):
    """Ověří základní spojení s Claude."""
    print("\n[TEST] Zkouším základní spojení...")
    response = await auth_manager.query("Odpověz pouze slovem 'FUNGUJU'.")

    assert response.is_successful()
    assert "FUNGUJU" in response.content
    assert response.cost >= 0
    print(f"✅ Basic connectivity OK. Cost: ${response.cost}")

@run_live
@pytest.mark.asyncio
async def test_02_session_memory(auth_manager):
    """Ověří, že si Claude pamatuje kontext v rámci session."""
    session_id = f"test_mem_{os.urandom(4).hex()}"
    secret_code = "BLUE_PINEAPPLE_99"

    # 1. Řekneme mu tajemství
    await auth_manager.query(
        f"Zapamatuj si tento kód: {secret_code}. Neodpovídej nic, jen si to ulož.",
        session_id=session_id
    )

    # 2. Zeptáme se na něj
    response = await auth_manager.query(
        "Jaký byl ten kód, který jsem ti právě řekl?",
        session_id=session_id,
        continue_session=True
    )

    assert secret_code in response.content

    # Ověříme metadata session
    session_info = auth_manager.get_session(session_id)
    assert session_info is not None
    assert session_info.total_turns >= 2
    print(f"✅ Session memory OK. Total turns: {session_info.total_turns}")

@run_live
@pytest.mark.asyncio
async def test_03_file_context_analysis(auth_manager):
    """Ověří, že Claude umí číst soubory."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp:
        tmp.write("def hello():\n    return 'Hello World'")
        tmp_path = Path(tmp.name)

    try:
        # Prompt explicitly mentions file
        prompt = f"Přečti soubor {tmp_path} a řekni mi název funkce v něm. Odpověz pouze názvem funkce."

        response = await auth_manager.query(
            prompt,
            working_directory=Path(tempfile.gettempdir()) # Working dir where file is
        )
        assert "hello" in response.content
        print("✅ File context reading OK.")
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

@run_live
@pytest.mark.asyncio
async def test_04_streaming_callback(auth_manager):
    """Ověří, že streaming vrací data po kouscích."""
    chunks = []

    async def on_stream(update):
        if update.content:
            chunks.append(update.content)

    await auth_manager.query(
        "Napiš čísla od 1 do 5 slovy (jedno na řádek).",
        stream_callback=on_stream
    )

    assert len(chunks) > 0
    full_text = "".join(chunks)
    assert "jedna" in full_text.lower() or "one" in full_text.lower()
    print(f"✅ Streaming OK. Received {len(chunks)} chunks.")

@run_live
@pytest.mark.asyncio
async def test_05_error_recovery(auth_manager):
    """Ověří chování při timeoutu."""
    # Vytvoříme novou instanci s extrémně krátkým timeoutem
    short_config = AuthConfig(timeout_seconds=0.1) # 100ms

    # Check auth before creating manager to avoid confusing errors
    if not auth_manager.auth_manager.is_authenticated():
        pytest.skip("Claude CLI not authenticated")

    manager_short = ClaudeAuthManager(config=short_config)

    try:
        with pytest.raises(ClaudeTimeoutError):
            await manager_short.query("Napiš dlouhou báseň o vesmíru.")
        print("✅ Timeout error handled correctly.")
    finally:
        await manager_short.shutdown()
