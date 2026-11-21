"""Run with: python3 -m pytest tests/"""
import sys
import types

from ui import main_menu


def run_with_inputs(monkeypatch, capsys, inputs):
    it = iter(inputs)
    monkeypatch.setattr("builtins.input", lambda _="": next(it))
    monkeypatch.setattr("ui.terminal.clear_screen", lambda: None)
    main_menu.run_app()
    return capsys.readouterr().out


def test_exit_from_main_menu(monkeypatch, capsys):
    out = run_with_inputs(monkeypatch, capsys, ["0"])
    assert "Goodbye" in out


def test_invalid_input_does_not_crash(monkeypatch, capsys):
    out = run_with_inputs(monkeypatch, capsys, ["abc", "", "99", "0"])
    assert out.count("Invalid choice") == 3


def test_student_flow_and_return(monkeypatch, capsys):
    monkeypatch.setattr(main_menu, "login_student", lambda: 7)
    out = run_with_inputs(
        monkeypatch, capsys, ["1", "1", "", "2", "", "3", "", "0", "0"]
    )
    assert "STUDENT MENU" in out and "Goodbye" in out


def test_history_receives_user_id(monkeypatch, capsys):
    received = []
    fake = types.ModuleType("history")
    fake.show_history = lambda user_id: received.append(user_id)
    monkeypatch.setitem(sys.modules, "history", fake)
    monkeypatch.setattr(main_menu, "login_student", lambda: 7)
    run_with_inputs(monkeypatch, capsys, ["1", "3", "", "0", "0"])
    assert received == [7]


def test_teacher_flow_and_return(monkeypatch, capsys):
    out = run_with_inputs(monkeypatch, capsys, ["2", "1", "", "0", "0"])
    assert "TEACHER MENU" in out and "Goodbye" in out
