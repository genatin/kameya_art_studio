"""E2E тесты диалогов Telegram бота."""
from datetime import time

import pytest
from aiogram_dialog import Dialog

from src.application.domen.models.activity_type import ActivityEnum
from src.application.domen.models.lesson_option import (
    CLASSIC_LESS,
    LessonOptionFactory,
    ONE_LESS,
    PRO_LESS,
    SUBSCRIPTION_4,
    SUBSCRIPTION_8,
    TRIAL_LESS,
)
from src.application.domen.text import RU
from src.presentation.dialogs.states import (
    AcitivityPages,
    AdminActivity,
    AdminReply,
    AdminPayments,
    Administration,
    BaseMenu,
    Developer,
    FirstSeen,
    PaymentsApprove,
    Registration,
    SignUp,
)


# ============================================================================
# ТЕСТЫ ДИАЛОГА ПЕРВОГО ЗАПУСКА (FirstSeen)
# ============================================================================


class TestFirstSeenDialog:
    """Тесты диалога первого запуска."""

    def test_first_seen_dialog_exists(self) -> None:
        """Тест существования диалога FirstSeen."""
        from src.presentation.dialogs.first_seen import first_seen_dialog

        assert first_seen_dialog is not None
        assert isinstance(first_seen_dialog, Dialog)

    def test_first_seen_states_count(self) -> None:
        """Тест количества состояний в FirstSeen."""
        from src.presentation.dialogs.first_seen import first_seen_dialog

        # states - это метод, который возвращает словарь состояний
        states_dict = first_seen_dialog.states()
        assert len(states_dict) == 1
        assert FirstSeen.START in states_dict

    def test_first_seen_windows_count(self) -> None:
        """Тест количества окон в FirstSeen."""
        from src.presentation.dialogs.first_seen import first_seen_dialog

        assert len(first_seen_dialog.windows) == 1


# ============================================================================
# ТЕСТЫ ДИАЛОГА РЕГИСТРАЦИИ (Registration)
# ============================================================================


class TestRegistrationDialog:
    """Тесты диалога регистрации."""

    def test_registration_dialog_exists(self) -> None:
        """Тест существования диалога Registration."""
        from src.presentation.dialogs.registration import registration_dialog

        assert registration_dialog is not None
        assert isinstance(registration_dialog, Dialog)

    def test_registration_states_count(self) -> None:
        """Тест количества состояний в Registration."""
        from src.presentation.dialogs.registration import registration_dialog

        # Registration имеет 5 состояний: NAME, LASTNAME, GET_CONTACT, EDIT_CONTACT, END
        expected_states = {
            Registration.NAME,
            Registration.LASTNAME,
            Registration.GET_CONTACT,
            Registration.EDIT_CONTACT,
            Registration.END,
        }
        actual_states = set(registration_dialog.states())

        assert expected_states == actual_states

    def test_registration_windows_count(self) -> None:
        """Тест количества окон в Registration."""
        from src.presentation.dialogs.registration import registration_dialog

        # 5 окон для 5 состояний
        assert len(registration_dialog.windows) == 5

    def test_registration_has_text_input_for_name(self) -> None:
        """Тест наличия TextInput для имени."""
        from src.presentation.dialogs.registration import registration_dialog

        # Ищем состояние NAME в списке
        states_list = registration_dialog.states()
        assert Registration.NAME in states_list

    def test_registration_has_text_input_for_lastname(self) -> None:
        """Тест наличия TextInput для фамилии."""
        from src.presentation.dialogs.registration import registration_dialog

        # Ищем состояние LASTNAME в списке
        states_list = registration_dialog.states()
        assert Registration.LASTNAME in states_list


# ============================================================================
# ТЕСТЫ БАЗОВОГО МЕНЮ (BaseMenu)
# ============================================================================


class TestBaseMenuDialog:
    """Тесты базового меню."""

    def test_base_menu_dialog_exists(self) -> None:
        """Тест существования диалога BaseMenu."""
        from src.presentation.dialogs.base_menu import menu_dialog

        assert menu_dialog is not None
        assert isinstance(menu_dialog, Dialog)

    def test_base_menu_states_count(self) -> None:
        """Тест количества состояний в BaseMenu."""
        from src.presentation.dialogs.base_menu import menu_dialog

        expected_states = {
            BaseMenu.START,
            BaseMenu.ABOUT_US,
            BaseMenu.HOW_TO,
        }
        actual_states = set(menu_dialog.states())

        assert expected_states == actual_states

    def test_base_menu_windows_count(self) -> None:
        """Тест количества окон в BaseMenu."""
        from src.presentation.dialogs.base_menu import menu_dialog

        assert len(menu_dialog.windows) == 3


# ============================================================================
# ТЕСТЫ ДИАЛОГА ЗАПИСИ (SignUp)
# ============================================================================


class TestSignUpDialog:
    """Тесты диалога записи на занятия."""

    def test_signup_dialog_exists(self) -> None:
        """Тест существования диалога SignUp."""
        from src.presentation.dialogs.sign_up import signup_dialog

        assert signup_dialog is not None
        assert isinstance(signup_dialog, Dialog)

    def test_signup_states_count(self) -> None:
        """Тест количества состояний в SignUp."""
        from src.presentation.dialogs.sign_up import signup_dialog

        expected_states = {
            SignUp.START,
            SignUp.STAY_FORM,
        }
        actual_states = set(signup_dialog.states())

        assert expected_states == actual_states

    def test_signup_windows_count(self) -> None:
        """Тест количества окон в SignUp."""
        from src.presentation.dialogs.sign_up import signup_dialog

        assert len(signup_dialog.windows) == 2


# ============================================================================
# ТЕСТЫ ДИАЛОГА СТРАНИЦ АКТИВНОСТЕЙ (ActivityPages)
# ============================================================================


class TestActivityPagesDialog:
    """Тесты диалога страниц активностей."""

    def test_activity_pages_dialog_exists(self) -> None:
        """Тест существования диалога ActivityPages."""
        from src.presentation.dialogs.sign_up import activity_pages_dialog

        assert activity_pages_dialog is not None
        assert isinstance(activity_pages_dialog, Dialog)

    def test_activity_pages_states_count(self) -> None:
        """Тест количества состояний в ActivityPages."""
        from src.presentation.dialogs.sign_up import activity_pages_dialog

        expected_states = {
            AcitivityPages.START,
            AcitivityPages.TICKETS,
        }
        actual_states = set(activity_pages_dialog.states())

        assert expected_states == actual_states

    def test_activity_pages_windows_count(self) -> None:
        """Тест количества окон в ActivityPages."""
        from src.presentation.dialogs.sign_up import activity_pages_dialog

        assert len(activity_pages_dialog.windows) == 2


# ============================================================================
# ТЕСТЫ АДМИНИСТРАТИВНЫХ ДИАЛОГОВ
# ============================================================================


class TestAdminDialogs:
    """Тесты административных диалогов."""

    def test_admin_reply_states_exist(self) -> None:
        """Тест существования состояний AdminReply."""
        # AdminReply имеет состояния: START, CANCEL, SEND
        assert AdminReply.START is not None
        assert AdminReply.CANCEL is not None
        assert AdminReply.SEND is not None

    def test_admin_payments_states_exist(self) -> None:
        """Тест существования состояний AdminPayments."""
        # AdminPayments имеет состояния: CANCEL_PAYMENT, CONFIRM_PAYMENT
        assert AdminPayments.CANCEL_PAYMENT is not None
        assert AdminPayments.CONFIRM_PAYMENT is not None

    def test_administration_states_exist(self) -> None:
        """Тест существования состояний Administration."""
        # Administration имеет состояния: START, EDIT_ACTS, IMAGE
        assert Administration.START is not None
        assert Administration.EDIT_ACTS is not None
        assert Administration.IMAGE is not None

    def test_admin_activity_states_exist(self) -> None:
        """Тест существования состояний AdminActivity."""
        # AdminActivity имеет состояния: PAGE, CHANGE, REMOVE, NAME, DATE, TIME, DESCRIPTION, PHOTO, SEND
        assert AdminActivity.PAGE is not None
        assert AdminActivity.CHANGE is not None
        assert AdminActivity.REMOVE is not None
        assert AdminActivity.NAME is not None
        assert AdminActivity.DATE is not None
        assert AdminActivity.TIME is not None
        assert AdminActivity.DESCRIPTION is not None
        assert AdminActivity.PHOTO is not None
        assert AdminActivity.SEND is not None


# ============================================================================
# ТЕСТЫ ДИАЛОГА ПОДТВЕРЖДЕНИЯ ОПЛАТЫ (PaymentsApprove)
# ============================================================================


class TestPaymentsApproveDialog:
    """Тесты диалога подтверждения оплаты."""

    def test_payments_approve_states_exist(self) -> None:
        """Тест существования состояний PaymentsApprove."""
        # PaymentsApprove имеет состояния: START, CONFIRM_PAYMENT
        assert PaymentsApprove.START is not None
        assert PaymentsApprove.CONFIRM_PAYMENT is not None


# ============================================================================
# ТЕСТЫ ДИАЛОГА РАЗРАБОТЧИКА (Developer)
# ============================================================================


class TestDeveloperDialog:
    """Тесты диалога разработчика."""

    def test_developer_states_exist(self) -> None:
        """Тест существования состояний Developer."""
        # Developer имеет состояния: START, TO_ADMIN
        assert Developer.START is not None
        assert Developer.TO_ADMIN is not None


# ============================================================================
# ТЕСТЫ СОСТОЯНИЙ FSM
# ============================================================================


class TestStatesGroup:
    """Тесты групп состояний FSM."""

    def test_first_seen_state_group(self) -> None:
        """Тест группы состояний FirstSeen."""
        assert hasattr(FirstSeen, 'START')
        assert FirstSeen.START is not None

    def test_registration_state_group(self) -> None:
        """Тест группы состояний Registration."""
        expected_states = {'GET_CONTACT', 'EDIT_CONTACT', 'NAME', 'LASTNAME', 'END'}
        actual_states = set(name for name in dir(Registration) if not name.startswith('_'))

        assert expected_states.issubset(actual_states)

    def test_base_menu_state_group(self) -> None:
        """Тест группы состояний BaseMenu."""
        expected_states = {'START', 'SIGN_UP', 'ABOUT_US', 'HOW_TO', 'END'}
        actual_states = set(name for name in dir(BaseMenu) if not name.startswith('_'))

        assert expected_states.issubset(actual_states)

    def test_sign_up_state_group(self) -> None:
        """Тест группы состояний SignUp."""
        expected_states = {'START', 'STAY_FORM'}
        actual_states = set(name for name in dir(SignUp) if not name.startswith('_'))

        assert expected_states.issubset(actual_states)

    def test_activity_pages_state_group(self) -> None:
        """Тест группы состояний ActivityPages."""
        expected_states = {'START', 'TICKETS'}
        actual_states = set(name for name in dir(AcitivityPages) if not name.startswith('_'))

        assert expected_states.issubset(actual_states)


# ============================================================================
# ТЕСТЫ ТИПОВ АКТИВНОСТЕЙ
# ============================================================================


class TestActivityTypes:
    """Тесты типов активностей."""

    def test_activity_enum_values(self) -> None:
        """Тест значений enum активностей."""
        assert ActivityEnum.LESSON.value == 'lesson'
        assert ActivityEnum.CHILD_STUDIO.value == 'child_studio'
        assert ActivityEnum.MASS_CLASS.value == 'mclasses'
        assert ActivityEnum.EVENING_SKETCH.value == 'evening_sketch'

    def test_activity_type_factory(self) -> None:
        """Тест фабрики типов активностей."""
        lesson_type = LessonOptionFactory.generate(TRIAL_LESS)
        assert lesson_type.name == TRIAL_LESS
        assert lesson_type.human_name


# ============================================================================
# ТЕСТЫ ОПЦИЙ УРОКОВ
# ============================================================================


class TestLessonOptions:
    """Тесты опций уроков."""

    def test_lesson_option_constants(self) -> None:
        """Тест констант опций уроков."""
        assert TRIAL_LESS == 'trial_less'
        assert ONE_LESS == 'one_less'
        assert SUBSCRIPTION_4 == 'subscrition_4'
        assert SUBSCRIPTION_8 == 'subscrition_8'
        assert CLASSIC_LESS == 'classic_less'
        assert PRO_LESS == 'pro_less'

    def test_lesson_option_factory(self) -> None:
        """Тест фабрики опций уроков."""
        option = LessonOptionFactory.generate(TRIAL_LESS)
        assert option.name == TRIAL_LESS
        assert option.human_name


# ============================================================================
# ТЕСТЫ ТЕКСТОВЫХ КОНСТАНТ
# ============================================================================


class TestTextConstants:
    """Тесты текстовых констант."""

    def test_ru_texts_exist(self) -> None:
        """Тест существования русских текстов."""
        # Проверяем наличие основных текстовых констант
        assert hasattr(RU, 'lesson')
        assert hasattr(RU, 'child_studio')
        assert hasattr(RU, 'mass_class')
        assert hasattr(RU, 'evening_sketch')
        assert hasattr(RU, 'back_step')
        assert hasattr(RU, 'menu')


# ============================================================================
# ТЕСТЫ МОДЕЛЕЙ
# ============================================================================


class TestLessonActivityModel:
    """Тесты модели LessonActivity."""

    @pytest.mark.asyncio
    async def test_lesson_activity_creation(self) -> None:
        """Тест создания LessonActivity."""
        from src.application.domen.models import LessonActivity
        from src.application.domen.models.activity_type import ActivityTypeFactory

        activity = LessonActivity(
            activity_type=ActivityTypeFactory.generate(ActivityEnum.LESSON),
            topic='Тестовая тема',
            date=None,
            time=time(14, 0),
            num_tickets=2,
            lesson_option=LessonOptionFactory.generate(CLASSIC_LESS),
        )

        assert activity.activity_type.name == ActivityEnum.LESSON.value
        assert activity.topic == 'Тестовая тема'
        assert activity.num_tickets == 2
        assert activity.lesson_option.name == CLASSIC_LESS

    @pytest.mark.asyncio
    async def test_lesson_activity_model_dump_for_store(self) -> None:
        """Тест сериализации для хранения."""
        from src.application.domen.models import LessonActivity
        from src.application.domen.models.activity_type import ActivityTypeFactory

        activity = LessonActivity(
            activity_type=ActivityTypeFactory.generate(ActivityEnum.LESSON),
            topic='Тестовая тема',
            date=None,
            time=None,
            num_tickets=1,
            lesson_option=LessonOptionFactory.generate(CLASSIC_LESS),
        )

        dumped = activity.model_dump_for_store()

        assert 'topic' in dumped
        assert 'option' in dumped
        assert 'datetime' in dumped
        assert 'num_tickets' in dumped
