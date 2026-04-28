import pytest
from datetime import date
from unittest.mock import AsyncMock, patch

from services.study_service import StudyService
from models import User, Plan, Task


class TestStudyService:

    @pytest.fixture
    def study_service(self):
        return StudyService()


    @pytest.mark.asyncio
    async def test_create_plan_returns_plan(self, study_service):
        with patch("services.study_service.storage") as mock_storage:
            mock_storage.create_plan = AsyncMock(
                return_value=Plan(1, 1, "Math")
            )

            result = await study_service.create_plan(1, "Math")

            assert result.subject == "Math"
            mock_storage.create_plan.assert_called_once_with(1, "Math", None)

    @pytest.mark.asyncio
    async def test_add_task_creates_task_and_updates_deadline(
        self, study_service
    ):
        with patch("services.study_service.storage") as mock_storage:
            mock_storage.create_task = AsyncMock(
                return_value=Task(1, 1, "Task 1", date(2025, 1, 1))
            )
            mock_storage.get_plan = AsyncMock(
                return_value=Plan(1, 1, "Math", date(2025, 1, 1))
            )
            mock_storage.update_plan_deadline = AsyncMock()

            result = await study_service.add_task(
                1, "Task 1", date(2025, 1, 1)
            )

            assert result.title == "Task 1"


    @pytest.mark.asyncio
    async def test_update_plan_deadline_updates_if_new_is_later(
        self, study_service
    ):
        with patch("services.study_service.storage") as mock_storage:
            mock_storage.get_plan = AsyncMock(
                return_value=Plan(1, 1, "Math", date(2025, 1, 1))
            )
            mock_storage.update_plan_deadline = AsyncMock()

            await study_service.update_plan_deadline(1, date(2025, 6, 1))

            mock_storage.update_plan_deadline.assert_called_once()


    @pytest.mark.asyncio
    async def test_update_plan_deadline_does_not_update_if_earlier(
        self, study_service
    ):

        with patch("services.study_service.storage") as mock_storage:
            mock_storage.get_plan = AsyncMock(
                return_value=Plan(1, 1, "Math", date(2025, 12, 31))
            )
            mock_storage.update_plan_deadline = AsyncMock()

            await study_service.update_plan_deadline(1, date(2025, 1, 1))

            mock_storage.update_plan_deadline.assert_not_called()


    @pytest.mark.asyncio
    async def test_update_plan_deadline_updates_if_current_is_none(
        self, study_service
    ):
        with patch("services.study_service.storage") as mock_storage:
            mock_storage.get_plan = AsyncMock(
                return_value=Plan(1, 1, "Math", None)
            )
            mock_storage.update_plan_deadline = AsyncMock()

            await study_service.update_plan_deadline(1, date(2025, 1, 1))

            mock_storage.update_plan_deadline.assert_called_once()


    @pytest.mark.asyncio
    async def test_get_plan_returns_user_plans(self, study_service):
        with patch("services.study_service.storage") as mock_storage:
            mock_storage.get_user_plans = AsyncMock(
                return_value=[Plan(1, 1, "Math")]
            )

            result = await study_service.get_plan(1)

            assert len(result) == 1


    @pytest.mark.asyncio
    async def test_get_tasks_returns_plan_tasks(self, study_service):
        with patch("services.study_service.storage") as mock_storage:
            mock_storage.get_tasks_by_plan = AsyncMock(
                return_value=[Task(1, 1, "Task 1", date(2025, 1, 1))]
            )

            result = await study_service.get_tasks(1)

            assert len(result) == 1


    @pytest.mark.asyncio
    async def test_get_plan_by_id_returns_plan(self, study_service):
        with patch("services.study_service.storage") as mock_storage:
            mock_storage.get_plan = AsyncMock(
                return_value=Plan(1, 1, "Math"))

            result = await study_service.get_plan_by_id(1)

            assert result.plan_id == 1


    def test_format_deadline_returns_nemaie_for_none(self, study_service):
        result = study_service.format_deadline(None)
        assert result == "Немає"


    def test_format_deadline_formats_date_correctly(self, study_service):
        result = study_service.format_deadline(date(2025, 12, 31))
        assert result == "31.12.2025"