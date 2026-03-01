from unittest.mock import MagicMock, call, patch

from app.initial_data import init, main


def test_init_calls_db_and_seed_functions() -> None:
    session_mock = MagicMock()
    session_context_manager = MagicMock()
    session_context_manager.__enter__.return_value = session_mock

    with (
        patch("app.initial_data.Session", return_value=session_context_manager),
        patch("app.initial_data.init_db") as init_db_mock,
        patch("app.initial_data.seed_pacemaker_telemetry_if_empty") as seed_mock,
    ):
        init()

    init_db_mock.assert_called_once_with(session_mock)
    seed_mock.assert_called_once_with(session_mock)


def test_main_logs_and_calls_init() -> None:
    with (
        patch("app.initial_data.init") as init_mock,
        patch("app.initial_data.logger.info") as logger_info_mock,
    ):
        main()

    init_mock.assert_called_once_with()
    logger_info_mock.assert_has_calls(
        [call("Creating initial data"), call("Initial data created")]
    )
